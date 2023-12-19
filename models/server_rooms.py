import asyncio
import logging

from firebase_admin import db

from events.queue_events import update_room_event, delete_room_event
from models.room import Room
from models.server_users import get_user
from models.user import User
from utils import generate_code

server_rooms_dict: dict[int, Room] = {}

async def get_room_where_user(user_id) -> Room:
    logging.info(f'Get room containing USER_{user_id}')
    for r in server_rooms_dict.values():
        if user_id in r.users or user_id in r.moderators or user_id in r.admins:
            return r
    return None


async def get_room(room_id) -> Room:
    room_id = str(room_id)
    if room_id == '':
        return None
    logging.info(f'Get room ROOM_{room_id}')
    if room_id in server_rooms_dict:
        return server_rooms_dict[room_id]
    else:
        logging.info(f'Try pooling from database')
        room = await try_get_room_from_db(room_id)
        if room:
            logging.info(f'Room found - {room.name}')
            await add_room(room_id, room)
            return room
        else:
            logging.warning(f'Room was not found in database!')
            return None


async def try_get_room_from_db(room_id) -> Room:
    rooms_ref = db.reference(f'/rooms/{room_id}')
    return load_room_from_json(room_id, rooms_ref.get())


def load_room_from_json(room_id, db_room) -> Room:
    if db_room is None:
        return None
    if 'admins' in db_room:
        room = Room(db_room['name'], db_room['admins'][0])
    else:
        room = Room(db_room['name'])
    room.set_room_id(room_id)
    room.is_queue_enabled = db_room['queue_enabled']
    room.is_queue_on_join = db_room['queue_on_join']
    room.users_join_code = db_room['join_code']
    room.moderators_join_code = db_room['mod_password']
    if 'users' in db_room:
        room.users = db_room['users']
    if 'moderators' in db_room:
        room.moderators = db_room['moderators']
    if 'admins' in db_room:
        room.admins = db_room['admins']
    if 'queue' in db_room:
        room.queue = db_room['queue']
    if 'banned' in db_room:
        room.banned = db_room['banned']
    if 'notes' in db_room:
        room.study_notes = room.decompress_notes(db_room['notes'])
    logging.info(f'Loaded room from database')
    return room


def check_room_join_code(room_join_code):
    for r in server_rooms_dict.values():
        if r.users_join_code == room_join_code:
            return True
    return False


async def create_room(user_id, room_name) -> Room:
    logging.info(f'Creating new room by USER_{user_id}. Room name: {room_name}')

    user: User = await get_user(user_id)
    room = Room(room_name, user_id)

    while check_room_join_code(room.users_join_code):
        logging.warning(f'ROOM_{room.room_id} has duplicated user join code ({room.users_join_code}) with other room!')
        room.users_join_code = generate_code(4)

    rooms_ref = db.reference('/rooms')
    room_ref = rooms_ref.push(room.to_dict())
    room_id = room_ref.key
    room.set_room_id(room_id)

    logging.info(f'Created: {room.to_dict()}')
    await user.add_owned_room(room_id)
    await add_room(room_id, room)
    return room


async def add_room(room_id, room: Room):
    logging.info(f'Caching ROOM_{room.room_id}')
    server_rooms_dict[room_id] = room


async def remove_room(room_id, user_id):
    logging.info(f'Removing ROOM_{room_id} by USER_{user_id}')
    room_to_remove = await get_room(room_id)
    if room_to_remove is None:
        return
    is_admin = await room_to_remove.is_user_admin(user_id)
    if is_admin:
        user: User = await get_user(user_id)
        await delete_room_event.fire(room_to_remove.get_users_list())
        await user.remove_owned_room(room_id)
        await room_to_remove.delete()
        del server_rooms_dict[room_id]
        return True
    return False


async def get_room_by_join_code(join_code, user_role):
    logging.info(f'Get room by join code | Code:{join_code} | Role: {user_role}')
    role_to_room_code = {
        'user': 'join_code',
        'moderator': 'mod_password'
    }

    if user_role == 'user':
        for r in server_rooms_dict.values():
            if r.users_join_code == join_code:
                return r
    if user_role == 'moderator':
        for r in server_rooms_dict.values():
            if r.moderators_join_code == join_code:
                return r

    logging.info(f'Try pooling from database')
    rooms_ref = db.reference('/rooms')
    db_room_data = rooms_ref.order_by_child(role_to_room_code[user_role]).equal_to(join_code).get()
    rooms_list = list(db_room_data.items())
    if len(rooms_list) < 1:
        return None
    room_key, room_data = rooms_list[0]
    room = load_room_from_json(room_key, room_data)
    if room:
        await add_room(room_key, room)
    return room


async def update_database_room_handler(room: Room):
    logging.info(f'Update room in database | ROOM_{room.room_id}')
    if room.room_id == '':
        logging.error('Room in cache has empty ID!')
        return

    try:
        save_data = room.to_dict()
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(room.room_id).set(save_data)
    except ConnectionError as cer:
        logging.error(f"Got room update connection error! {cer}")
        await asyncio.sleep(3)
        save_data = room.to_dict()
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(room.room_id).set(save_data)
    except Exception as ex:
        logging.error(f"Got room update error! {ex}")

update_room_event.add_handler(update_database_room_handler)