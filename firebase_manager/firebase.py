import asyncio

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import logging

from models.room_event import RoomEvent
from models.room_journal import RoomJournal
from events.queue_events import queue_enable_state_event, user_joined_event, username_changed_event, update_queue_event
from models.room import Room
from models.server_jornals import get_room_journal
from models.server_rooms import get_room, create_room, get_room_by_join_code, remove_room
from models.server_users import get_user
from models.user import User
from roles.user_roles_enum import UserRoles

cred = credentials.Certificate("firebase.config.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://queue-miet-default-rtdb.europe-west1.firebasedatabase.app/"
})


async def toggle_favorite_room(user_id):
    user: User = await get_user(user_id)
    return await user.toggle_favorite_room(user.room)


async def get_favorite_rooms_dict(user_id):
    favorites = {}
    user: User = await get_user(user_id)

    unknown_rooms = []
    for favorite_room, role in user.favorites.items():
        room: Room = await get_room(favorite_room)
        if room is None:
            unknown_rooms.append(favorite_room)
            continue
        favorites[favorite_room] = {'room': room, 'role': role}

    for unknown_room in unknown_rooms:
        await user.remove_favorite_room(unknown_room)

    return favorites


async def check_room_exist(room_id):
    rooms_ref = db.reference('/rooms')
    if rooms_ref.child(room_id).get() is None:
        return False
    return True


async def db_create_room(user_id, room_name):
    try:
        room: Room = await create_room(user_id, room_name)

        user = await get_user(user_id)
        await user.set_room(room.room_id)
        await user.update_role('admins')
        journal: RoomJournal = await get_room_journal(room.room_id)
        await journal.add_event(RoomEvent.CreateRoom(user_id))
        return room, None
    except Exception as e:
        error_message = f"Error creating room. Arguments: {user_id}, {room_name}. Error: {str(e)}"
        logging.error(error_message)  # Log the error
        return None, str(e)


async def get_user_room_key(user_id):
    """
    Возвращает room_key
    """
    user: User = await get_user(user_id)
    if user.room != '':
        return user.room
    else:
        return None


async def get_global_role_users_dict():
    global_roles_ref = db.reference('/special_roles')
    global_roles = global_roles_ref.get()
    result = []
    for key, item in global_roles.items():
        result.append({
            'user_id': key,
            'role': item
        })
    return result


async def leave_room(user_id):
    user: User = await get_user(user_id)
    room = await get_room(user.room)
    if room is not None:
        logging.info(f'USER_{user_id} leave ROOM_{user.room} ({room.name})')
        await room.remove_user(user_id)

        journal: RoomJournal = await get_room_journal(room.room_id)
        await journal.add_event(RoomEvent.UserLeft(user_id))
        return True
    else:
        return False


async def leave_room_instance(user, room):
    if int(user.user_id) in room.get_users_list():
        logging.info(f'USER_{user.user_id} leave ROOM_{room.room_id} ({room.name})')
        await room.remove_user(user.user_id)
        return True
    return False


async def set_user_room(user_id, room_key):
    logging.info(f'Set USER_{user_id} room: {room_key}')
    user: User = await get_user(user_id)
    await user.set_room(room_key)


async def delete_room(user_id):
    user: User = await get_user(user_id)
    room_id = user.room
    result = await remove_room(room_id, user_id)
    if result:
        journal: RoomJournal = await get_room_journal(room_id)
        await journal.add_event(RoomEvent.DeleteRoom(user_id))
    return result


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
            room_exits = await check_room_exist(room_key)
            if not room_exits:
                logging.warning(f"USER_{user_id} was connected to not existing room with id={room_key}!")
                await set_user_room(user_id, '')
            else:
                return {'error': "Connected to other room", 'error_text': 'Вы уже подключены к другой комнате' }

        room = await get_room_by_join_code(room_code, user_role)

        if room:
            if await room.check_banned(user_id):
                return { 'error': 'Banned', 'error_text': 'Вы были добавлены в черный список комнаты.' }

            if user_role == 'user':
                await room.add_user(user_id, UserRoles.User)
            if user_role == 'moderator':
                await room.add_user(user_id, UserRoles.Moderator)

            room_key = room.room_id
            user: User = await get_user(user_id)
            await user.set_room(room_key)
            await user.update_role(role_to_room_list[user_role])
            await user_joined_event.fire(room, user_id, user_role)

            journal: RoomJournal = await get_room_journal(room.room_id)
            await journal.add_event(RoomEvent.UserJoin(user_id))
            logging.info(f'USER_{user_id} join ROOM_{room_key} ({room.name})')
            return { 'room': room }

        return { 'error': 'Room not found', 'error_text': 'Комната не найдена.' }
    except Exception as e:
        error_message = f"Error joining room. Arguments:\nuser_id:{user_id};\nroom_join_code:{room_code}\nError: {str(e)}"
        logging.error(error_message)
        return { 'error': str(e), 'error_text': str(e) }


async def get_room_queue(room_key):
    room = await get_room(room_key)
    return room.queue


async def get_queue_users(room_key):
    queue_users = await get_room_queue(room_key)
    users_names = []
    for user_id in queue_users:
        # TODO: Часто необходимо узнать имя пользователя из очереди, следует изменить список на словарь [user_id: user_name]
        user: User = await get_user(user_id)
        users_names.append(user.name)

    return users_names


async def skip_queue_place(user_id):
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    skip_user_id = await room.skip_queue_place(user)
    if skip_user_id:
        skip_user: User = await get_user(skip_user_id)
        return skip_user.name
    return None


async def exit_queue(user_id):
    user: User = await get_user(user_id)
    logging.info(f'USER_{user_id} left queue')
    return await user.exit_queue()


async def try_enter_queue(user_id):
    user: User = await get_user(user_id)
    if user.check_has_default_name():
        return {'error': 'User has default name!', 'error_text': f'Нельзя присоединиться к очереди со стандартным именем - <b>{user.name}</b>!'}

    logging.info(f'USER_{user_id} entered queue')
    place = await user.enter_queue()
    return { 'place': place }


async def enter_queue(user_id):
    user: User = await get_user(user_id)
    logging.info(f'USER_{user_id} entered queue')
    return await user.enter_queue()


async def is_autoqueue_enabled(user_id):
    room = await get_room(await get_user_room_key(user_id))
    return room.is_queue_on_join


async def is_user_in_queue(user_id):
    room = await get_room(await get_user_room_key(user_id))
    if room and user_id in room.queue:
        return {'result': True, 'place': room.queue.index(user_id), 'len': len(room.queue)}
    return {'result': False, 'place': None, 'len': None}


async def is_room_favorite(user_id):
    user: User = await get_user(user_id)
    return await user.is_favorite_room(user.room)


async def get_room_queue_enabled_by_userid(user_id) -> bool:
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    if room:
        return room.is_queue_enabled
    return None


async def get_room_queue_enabled(room_key) -> bool:
    room = await get_room(room_key)
    if room:
        return room.is_queue_enabled
    return None


async def get_user_role(user_id):
    room_key = await get_user_room_key(user_id)
    room = await get_room(room_key)
    user_role = room.get_user_group(user_id)
    logging.info(f'USER_{user_id}: Get user role: {user_role}')
    return user_role


async def generate_random_queue(room, queue_list):
    await room.queue_clear()
    await room.set_queue(queue_list)

    message_text = ''
    if len(queue_list) < 1:
        return f"<b>В комнате нет пользователей!</b>"

    for i, add_user in enumerate(queue_list):
        user: User = await get_user(add_user)
        message_text += f'{i + 1}. {user.name}\n'
        await user.set_queue_enter(room, i)

    asyncio.create_task(update_queue_event.fire(room.room_id, None))
    return f"<b>Случайный список:</b>\n{message_text}"


async def switch_room_queue_enabled(user_id):
    room_key = await get_user_room_key(user_id)
    room = await get_room(room_key)
    await room.switch_queue_enabled()
    new_val: bool = room.is_queue_enabled
    queue_state = {
        True: "enabled",
        False: "disabled"
    }
    logging.info(f'Queue in room {room_key} is {queue_state[new_val]}')
    await queue_enable_state_event.fire(room_key, new_val)
    return new_val


async def change_room_auto_queue(room_key):
    room = await get_room(room_key)
    await room.switch_autoqueue_enabled()
    logging.info(f'Auto queue join in room {room_key} set to {room.is_queue_on_join}')
    return room.is_queue_on_join


async def change_room_name(user_id, new_name):
    user: User = await get_user(user_id)
    room_key = user.room

    room = await get_room(room_key)
    await room.update_name(new_name)
    return True


async def change_user_name(user_id, new_name):
    try:
        user: User = await get_user(user_id)
        await user.update_name(new_name)
        await username_changed_event.fire()
    except Exception as e:
        logging.error(f'Update user name error: {str(e)}')
        return False
    finally:
        return True


async def is_user_name_default(user_id):
    user: User = await get_user(user_id)
    return user.has_default_name


async def get_user_name(user_id):
    user: User = await get_user(user_id)
    return user.name


async def get_user_role_at_room(user_id) -> UserRoles:
    user: User = await get_user(user_id)
    room = await get_room(user.room)
    if room:
        return room.get_user_role(user_id)
    return None


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
    room = await get_room(user.room)
    user_pop_id = await room.queue_pop(user_id)
    return user_pop_id

async def get_db_data(key):
    data_ref = db.reference('/data').child(key)
    data = data_ref.get()
    return data