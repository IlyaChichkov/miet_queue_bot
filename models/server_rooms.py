import asyncio
import logging
from typing import List

from firebase_admin import db

from events.queue_events import update_room_event, delete_room_event
from models.room import Room
from models.server_users import get_user
from models.user import User
from utils import generate_code

server_rooms: List[Room] = []

async def get_room_where_user(user_id) -> Room:
    logging.info(f'Get room containing USER_{user_id}')
    room = [room for room in server_rooms if user_id in room.users or user_id in room.moderators or user_id in room.admins]
    if room and len(room) > 0:
        return room[0]
    return None


async def get_room(room_id) -> Room:
    logging.info(f'Get room ROOM_{room_id}')
    if room_id == '':
        return None
    room = [room for room in server_rooms if room.room_id == room_id]
    if len(room) > 0:
        return room[0]
    else:
        logging.info(f'Try pooling from database')
        room = await try_get_room_from_db(room_id)
        if room:
            logging.info(f'Room found - {room.name}')
            await add_room(room)
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
    logging.info(f'Loaded room from database')
    return room


def check_room_join_code(room_join_code):
    for r in server_rooms:
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
    room.set_room_id(room_ref.key)

    logging.info(f'Created: {room.to_dict()}')
    await user.add_owned_room(room_ref.key)
    await add_room(room)
    return room


async def add_room(room: Room):
    logging.info(f'Add new room to cache | ROOM_{room.room_id}')
    server_rooms.append(room)


async def remove_room(room_id, user_id):
    logging.info(f'Removing ROOM_{room_id} by USER_{user_id}')
    rooms_to_remove = [room for room in server_rooms if room.room_id == room_id]
    room_to_remove = rooms_to_remove[0]

    is_admin = await room_to_remove.is_user_admin(user_id)
    if is_admin:
        user: User = await get_user(user_id)
        await delete_room_event.fire(room_to_remove.get_users_list())
        await user.remove_owned_room(room_id)
        await room_to_remove.delete()
        server_rooms.remove(room_to_remove)


async def get_room_by_join_code(join_code, user_role):
    logging.info(f'Get room by join code | Code:{join_code} | Role: {user_role}')
    role_to_room_code = {
        'user': 'join_code',
        'moderator': 'mod_password'
    }

    room = None
    if user_role == 'user':
        room = [room for room in server_rooms if room.users_join_code == join_code]
    if user_role == 'moderator':
        room = [room for room in server_rooms if room.moderators_join_code == join_code]

    if room and len(room) > 0:
        return room[0]
    else:
        logging.info(f'Try pooling from database')
        rooms_ref = db.reference('/rooms')
        db_room_data = rooms_ref.order_by_child(role_to_room_code[user_role]).equal_to(join_code).get()
        rooms_list = list(db_room_data.items())
        if len(rooms_list) < 1:
            return None
        room_key, room_data = rooms_list[0]
        room = load_room_from_json(room_key, room_data)
        if room:
            await add_room(room)
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