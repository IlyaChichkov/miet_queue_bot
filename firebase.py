import re
from collections import OrderedDict

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import logging

from events.queue_events import update_queue_event
from utils import generate_password, generate_code

cred = credentials.Certificate("firebase.config.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://queue-miet-default-rtdb.europe-west1.firebasedatabase.app/"
})

def get_new_room(user_id, room_name):
    return {
        'name': room_name,
        'mod_password': generate_password(7),
        'join_code': generate_code(4),
        'queue_on_join': True,
        'admins': [ user_id ],
        'moderators': None,
        'users': None,
        'banned': None
    }


async def get_room_by_key(room_key):
    rooms_ref = db.reference(f'/rooms/{room_key}')
    return rooms_ref.get()


async def db_get_user_room(user_id):
    try:
        user = await get_user(user_id)
        user_key, user_data = list(user.items())[0]

        if 'room' not in user_data:
            return { 'error': 'User has no connected room' }

        room_key = user_data['room']

        if room_key == "":
            return { 'error': 'User has no connected room' }

        room = await get_room_by_key(room_key)
        if room:
            return { 'room': room }
        else:
            return { 'error': 'No room found with such id' }

    except Exception as e:
        error_message = f"Error getting user's room. Error: {str(e)}"
        logging.error(error_message)
        return { 'error': str(e) }


async def db_create_room(user_id, password, room_name):
    try:
        # TODO: check user is in other room already

        # Check admin password to create room
        pass_ref = db.reference('/root_passwords')
        passwords = pass_ref.get()
        correct = False

        for root_password in passwords:
            if root_password == password:
                correct = True

        if not correct:
            return { 'error': 'Wrong password', 'error_text': 'У вас нет прав доступа к этому действию.' }

        # Check if room with the same name is already exist
        rooms_ref = db.reference('/rooms')
        room = rooms_ref.order_by_child('name').equal_to(room_name).get()
        if room:
            # user_key, user_data = list(room.items())[0]
            return {'error': 'Room name duplicate', 'error_text': 'Такая комната уже есть.'}

        room = get_new_room(user_id, room_name)
        room_ref = rooms_ref.push(room)

        users_ref = db.reference('/users')
        user = await get_user(user_id)
        if user:
            user_key, user_data = list(user.items())[0]

            user_data['room'] = room_ref.key

            users_ref.child(user_key).set(user_data)

        return { 'room': room }
    except Exception as e:
        error_message = f"Error creating room. Arguments: {user_id}, {password}, {room_name}. Error: {str(e)}"
        logging.error(error_message)  # Log the error
        return { 'error': str(e), 'error_text': str(e) }


async def get_user(user_id):
    users_ref = db.reference('/users')
    user = users_ref.order_by_child('tg_id').equal_to(user_id).get()

    if user:
        # Return existing user
        return user
    else:
        # Create user
        new_user_dict = {
            'tg_id': user_id,
            'name': f'User_{generate_code(5)}',
            'room': "",
            'data': {}
        }
        logging.info(f'New user was created: {new_user_dict}')
        new_user_ref = users_ref.push(new_user_dict)
        result = OrderedDict()
        result[new_user_ref.key] = db.reference(f'/users/{new_user_ref.key}').get()
        return result


async def get_user_data(user_id):
    user = await get_user(user_id)
    return list(user.items())[0]


async def get_user_room(user_id):
    """
    Возвращает room_key
    """
    user_key, user_data = await get_user_data(user_id)
    if 'room' in user_data:
        room_key = user_data['room']
        if room_key == "":
            return None
        else:
            return user_data['room']
    else:
        return None


async def leave_room(user_id):
    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']
    room = await get_room_by_key(room_key)

    if 'users' in room and user_id in room['users']:
        room['users'].remove(user_id)
        if 'queue' in room and user_id in room['queue']:
            room['queue'].remove(user_id)
    elif 'moderators' in room and user_id in room['moderators']:
        room['moderators'].remove(user_id)
    else:
        return False

    await set_user_room(user_id, None)

    rooms_ref = db.reference('/rooms')
    rooms_ref.child(room_key).set(room)
    return True


async def set_user_room(user_id, room_key):
    users_ref = db.reference('/users')
    user_key, user_data = await get_user_data(user_id)
    user_data['room'] = room_key
    users_ref.child(user_key).set(user_data)


async def delete_room(user_id):
    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']
    room = await get_room_by_key(room_key)

    if 'admins' in room:
        if user_id not in room['admins']:
            return False

    if 'users' in room:
        for user in room['users']:
            await set_user_room(user, None)

    if 'moderators' in room:
        for user in room['moderators']:
            await set_user_room(user, None)

    if 'admins' in room:
        for user in room['admins']:
            await set_user_room(user, None)

    logging.info(f'Deleting room, id: {room_key}, name: {room["name"]}')
    room_ref = db.reference(f'/rooms/{room_key}')
    room_ref.delete()
    return True


async def user_join_room(user_id, room_code, user_role):
    role_to_room_list = {
        'user': 'users',
        'moderator': 'moderators'
    }
    role_to_room_code = {
        'user': 'join_code',
        'moderator': 'mod_password'
    }
    try:
        users_ref = db.reference('/users')
        user = await get_user(user_id)

        room_key = await get_user_room(user_id)
        if room_key is not None:
            return { 'error': "Connected to other room" }

        rooms_ref = db.reference('/rooms')
        room = rooms_ref.order_by_child(role_to_room_code[user_role]).equal_to(room_code).get()
        if room:
            room_key, room_data = list(room.items())[0]
            user_key, user_data = list(user.items())[0]
            user_data['room'] = room_key
            users_ref.child(user_key).set(user_data)

            try:
                room_data[role_to_room_list[user_role]].append(user_id)
            except KeyError:
                room_data[role_to_room_list[user_role]] = [ user_id ]

            rooms_ref.child(room_key).set(room_data)

            return { 'room': room_data }

        return { 'error': 'Room not found' }
    except Exception as e:
        error_message = f"Error joining room. Arguments: {user_id}, {room_code}. Error: {str(e)}"
        logging.error(error_message)
        return { 'error': str(e) }


async def get_room_queue(room_key):
    room = await get_room_by_key(room_key)
    if 'queue' in room:
        return room['queue']
    else:
        return None


async def get_queue_users(room_key):
    queue_users = await get_room_queue(room_key)
    users_names = []
    if queue_users:
        for user_id in queue_users:
            user_key, user_data = await get_user_data(user_id)
            users_names.append(user_data['name'])

        return users_names
    return None


async def exit_queue(user_id):
    if not await is_user_in_queue(user_id):
        return False

    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']
    room = await get_room_by_key(room_key)

    try:
        room['queue'].remove(user_id)
    except Exception as e:
        logging.error(str(e))

    rooms_ref = db.reference('/rooms')
    rooms_ref.child(room_key).set(room)
    await update_queue_event.fire()
    return True


async def enter_queue(user_id):
    if await is_user_in_queue(user_id):
        return -1

    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']

    room = await get_room_by_key(room_key)
    place = -1

    try:
        place = len(room['queue']) + 1
        room['queue'].append(user_id)
    except KeyError:
        place = 1
        room['queue'] = [user_id]

    rooms_ref = db.reference('/rooms')
    rooms_ref.child(room_key).set(room)
    await update_queue_event.fire()
    return place


async def get_room_option(user_id, option_name):
    room = await get_room_by_key(await get_user_room(user_id))
    if option_name in room:
        return room[option_name]


async def is_user_in_queue(user_id):
    room = await get_room_by_key(await get_user_room(user_id))
    if 'queue' in room and user_id in room['queue']:
        return True
    return False


async def change_room_auto_queue(room_key):
    room = await get_room_by_key(room_key)

    if 'queue_on_join' in room:
        new_val = not room['queue_on_join']
        room['queue_on_join'] = new_val
        logging.info(f'Auto queue join in room {room_key} set to {new_val}')

        rooms_ref = db.reference('/rooms')
        rooms_ref.child(room_key).set(room)


async def change_room_name(user_id, new_name):
    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']

    room = await get_room_by_key(room_key)
    room['name'] = new_name

    rooms_ref = db.reference('/rooms')
    rooms_ref.child(room_key).set(room)
    return True


async def change_user_name(user_id, new_name):
    user_key, user_data = await get_user_data(user_id)
    user_data['name'] = new_name

    user_ref = db.reference('/users')
    user_ref.child(user_key).set(user_data)
    return True


def default_name_regular(input_text):
    pattern = re.compile(r"User_[0-9]+", re.IGNORECASE)
    return pattern.match(input_text)


async def is_user_name_default(user_id):
    user_key, user_data = await get_user_data(user_id)
    return default_name_regular(user_data['name'])


async def get_user_name(user_id):
    user_key, user_data = await get_user_data(user_id)
    return user_data['name']


async def queue_pop(user_id):
    if await is_user_in_queue(user_id):
        return -1

    user_key, user_data = await get_user_data(user_id)
    room_key = user_data['room']

    room = await get_room_by_key(room_key)
    first_in_queue = None
    if 'queue' in room:
        first_in_queue = room['queue'].pop(0)
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(room_key).set(room)

    return first_in_queue