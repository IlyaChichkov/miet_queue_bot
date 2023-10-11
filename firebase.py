import re

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import logging

from events.queue_events import update_queue_event, queue_enable_state_event, user_joined_event, username_changed_event
from models.room import Room
from models.server_passwords import load_passwords, check_password
from models.server_rooms import get_room, create_room, get_room_where_user, get_room_by_join_code, remove_room
from models.server_users import get_user
from models.user import User
from roles.user_roles_enum import UserRoles

cred = credentials.Certificate("firebase.config.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://queue-miet-default-rtdb.europe-west1.firebasedatabase.app/"
})


async def get_room_by_key(room_key) -> Room:
    room = await get_room(room_key)
    if room:
        print('Successfully got room from server data!', room)
        return room
    else:
        print('Error getting room from server data!', room)
        return None


async def db_get_user_room(user_id):
    print('Get user\'s room')
    try:
        room = await get_room_where_user(user_id)
        if room:
            print('Successfully got room from server data!', room)
            return { 'room': room }

        user: User = await get_user(user_id)
        print(f'>>> db_get_user_room: USER: {user.to_dict()}')
        if user.room == '':
            return { 'error': 'User has no connected room' }

        room = await get_room_by_key(user.room)
        if room:
            return { 'room': room }
        else:
            return { 'error': 'No room found with such id' }

    except Exception as e:
        error_message = f"Error getting user's room. Error: {str(e)}"
        logging.error(error_message)
        return { 'error': str(e) }


async def check_room_exist(room_id):
    rooms_ref = db.reference('/rooms')
    if rooms_ref.child(room_id).get() is None:
        return False
    return True


async def db_create_room(user_id, room_name):
    print('Try create new room')
    try:
        room: Room = await create_room(user_id, room_name)

        user = await get_user(user_id)
        await user.set_room(room.room_id)
        await user.update_role('admins')

        return { 'room': room.to_dict() }
    except Exception as e:
        error_message = f"Error creating room. Arguments: {user_id}, {room_name}. Error: {str(e)}"
        logging.error(error_message)  # Log the error
        return { 'error': str(e), 'error_text': str(e) }


async def get_user_room_key(user_id):
    """
    Возвращает room_key
    """
    user: User = await get_user(user_id)
    if user.room != '':
        return user.room
    else:
        return None


async def leave_room(user_id):
    user: User = await get_user(user_id)
    room_key = user.room
    room = await get_room_by_key(room_key)
    await room.remove_user(user_id)
    return True


async def set_user_room(user_id, room_key):
    logging.info(f'Set USER_{user_id} room: {room_key}')
    user: User = await get_user(user_id)
    await user.set_room(room_key)


async def delete_room(user_id):
    user: User = await get_user(user_id)
    room_key = user.room
    await remove_room(room_key, user_id)
    return True


async def get_user_owned_rooms_list(user_id):
    user: User = await get_user(user_id)
    return user.owned_rooms


async def admin_join_room(user_id, room_code):
    # TODO: Connect to room as admin

    room = await get_room(room_code)
    await room.add_user(user_id, UserRoles.Admin)
    await set_user_room(user_id, room.room_id)
    await set_user_role(user_id, 'admins')
    await user_joined_event.fire(room, user_id, 'admin')
    result = {'room': room}
    return result


async def user_join_room(user_id, room_code, user_role):
    role_to_room_list = {
        'user': 'users',
        'moderator': 'moderators'
    }
    try:
        room_key = await get_user_room_key(user_id)
        if room_key is not None:
            if not await check_room_exist(room_key):
                await set_user_room(user_id, '')
            else:
                return {'error': "Connected to other room", 'error_text': 'Вы уже подключены к другой комнате' }

        room = await get_room_by_join_code(room_code, user_role)

        if room:
            if user_role == 'user':
                await room.add_user(user_id, UserRoles.User)
            if user_role == 'moderator':
                await room.add_user(user_id, UserRoles.Moderator)
            await set_user_room(user_id, room.room_id)

            await set_user_role(user_id, role_to_room_list[user_role])
            await user_joined_event.fire(room, user_id, user_role)
            result = { 'room': room }
            return result

        return { 'error': 'Room not found', 'error_text': 'Комната не найдена.' }
    except Exception as e:
        error_message = f"Error joining room. Arguments:\nuser_id:{user_id};\nroom_join_code:{room_code}\nError: {str(e)}"
        logging.error(error_message)
        return { 'error': str(e), 'error_text': str(e) }


async def get_room_queue(room_key):
    room = await get_room_by_key(room_key)
    return room.queue


async def get_queue_users(room_key):
    queue_users = await get_room_queue(room_key)
    users_names = []
    for user_id in queue_users:
        user: User = await get_user(user_id)
        users_names.append(user.name)

    return users_names


async def exit_queue(user_id):
    if not await is_user_in_queue(user_id):
        return False

    user: User = await get_user(user_id)
    room_key = user.room
    room = await get_room_by_key(room_key)
    await room.queue_remove(user_id)
    await update_queue_event.fire()
    return True


async def enter_queue(user_id):
    if await is_user_in_queue(user_id):
        return -1

    user: User = await get_user(user_id)
    room_key = user.room

    room = await get_room_by_key(room_key)
    place = len(room.queue) + 1
    await room.queue_add(user_id)
    await update_queue_event.fire()
    return place


async def is_autoqueue_enabled(user_id):
    room = await get_room_by_key(await get_user_room_key(user_id))
    return room.is_queue_on_join


async def is_user_in_queue(user_id):
    room = await get_room_by_key(await get_user_room_key(user_id))
    if room and user_id in room.queue:
        return True
    return False


async def get_room_queue_enabled_by_userid(user_id) -> bool:
    room_key = await get_user_room_key(user_id)
    return await get_room_queue_enabled(room_key)


async def get_room_queue_enabled(room_key) -> bool:
    room = await get_room_by_key(room_key)
    if room:
        return room.is_queue_enabled
    return None


async def get_user_role(user_id):
    room_key = await get_user_room_key(user_id)
    room = await get_room_by_key(room_key)
    user_role = room.get_user_group(user_id)
    logging.info(f'USER_{user_id}: Get user role: {user_role}')
    return user_role


async def switch_room_queue_enabled(user_id):
    room_key = await get_user_room_key(user_id)
    room = await get_room_by_key(room_key)
    await room.switch_queue_enabled()
    new_val: bool = room.is_queue_enabled
    queue_state = {
        True: "enabled",
        False: "disabled"
    }
    logging.info(f'Queue in room {room_key} is {queue_state[new_val]}')
    await queue_enable_state_event.fire(room_key, new_val)


async def change_room_auto_queue(room_key):
    room = await get_room_by_key(room_key)
    await room.switch_autoqueue_enabled()
    logging.info(f'Auto queue join in room {room_key} set to {room.is_queue_on_join}')


async def change_room_name(user_id, new_name):
    user: User = await get_user(user_id)
    room_key = user.room

    room = await get_room_by_key(room_key)
    await room.update_name(new_name)
    return True


async def change_user_name(user_id, new_name):
    try:
        user: User = await get_user(user_id)
        await user.update_name(new_name)
        await username_changed_event.fire()
        return True
    except Exception as e:
        logging.error(f'Update user name error: {str(e)}')
        return False


def default_name_regular(input_text):
    pattern = re.compile(r"User_[0-9]+", re.IGNORECASE)
    return pattern.match(input_text)


async def is_user_name_default(user_id):
    user: User = await get_user(user_id)
    return default_name_regular(user.name)


async def get_user_name(user_id):
    user: User = await get_user(user_id)
    return user.name


async def get_user_role_at_room(user_id) -> UserRoles:
    user: User = await get_user(user_id)
    room = await get_room_by_key(user.room)
    return room.get_user_role(user_id)


async def set_user_role(user_id, role):
    try:
        user: User = await get_user(user_id)
        await user.update_role(role)
        return True
    except Exception as e:
        logging.error(f'Update user role error: {str(e)}')
        return False


async def get_user_current_role(user_id):
    user: User = await get_user(user_id)
    return user.current_role


async def queue_pop(user_id):
    user: User = await get_user(user_id)
    room = await get_room_by_key(user.room)
    user_pop_id = await room.queue_pop(user_id)
    return user_pop_id