import json
import logging
from typing import List

from firebase_admin import db

from events.queue_events import update_room_event, delete_room_event
from models.room import Room
from models.server_users import get_user
from models.user import User

server_rooms: List[Room] = []

async def get_room_where_user(user_id) -> Room:
    print(f'>>> get room where user_{user_id}: \n')
    for sr in server_rooms:
        print(sr.room_id)
    room = [room for room in server_rooms if user_id in room.users or user_id in room.moderators or user_id in room.admins]
    if room and len(room) > 0:
        return room[0]
    return None


async def get_room(room_id) -> Room:
    if room_id == '':
        return None
    print(f'> get room {room_id}: \n', server_rooms)
    room = [room for room in server_rooms if room.room_id == room_id]
    if len(room) > 0:
        print(f'> find in cache')
        return room[0]
    else:
        print(f'> find in db')
        room = await try_get_room_from_db(room_id)
        if room:
            await add_room(room)
        return room


async def try_get_room_from_db(room_id) -> Room:
    rooms_ref = db.reference(f'/rooms/{room_id}')
    return load_room_from_json(room_id, rooms_ref.get())


def load_room_from_json(room_id, db_room) -> Room:
    if db_room is None:
        return None
    print(f">>> Load From Database <<<")
    print(f"db room: ", db_room)
    print(f"ID: ", room_id)
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
    print(f"Loaded room from db: ", room)
    return room


async def create_room(user_id, room_name) -> Room:
    logging.info(f'Creating new room by USER_{user_id}. Room name: {room_name}')

    user: User = await get_user(user_id)
    room = Room(room_name, user_id)

    rooms_ref = db.reference('/rooms')
    room_ref = rooms_ref.push(room.to_dict())
    room.set_room_id(room_ref.key)

    logging.info(f'Created: {room.to_dict()}')
    await user.add_owned_room(room_ref.key)
    await add_room(room)
    return room


async def add_room(room: Room):
    logging.info(f'Caching new room: {room.room_id}')
    server_rooms.append(room)


async def remove_room(room_id, user_id):
    logging.info(f'Removing room cache: {room_id}')
    rooms_to_remove = [room for room in server_rooms if room.room_id == room_id]
    room_to_remove = rooms_to_remove[0]

    is_admin = await room_to_remove.is_user_admin(user_id)
    if is_admin:
        user: User = await get_user(user_id)
        await user.remove_owned_room(room_id)
        await delete_room_event.fire(room_to_remove.get_users_list())
        await room_to_remove.delete()
        server_rooms.remove(room_to_remove)


async def get_room_by_join_code(join_code, user_role):
    logging.info(f'Get room by join code\nCode:{join_code}')
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
        print(f'> find in cache')
        return room[0]
    else:
        print(f'> find in db')
        rooms_ref = db.reference('/rooms')
        db_room_data = rooms_ref.order_by_child(role_to_room_code[user_role]).equal_to(join_code).get()
        print(db_room_data.items())
        room_key, room_data = list(db_room_data.items())[0]
        print(room_key, room_data)
        room = load_room_from_json(room_key, room_data)
        print(room)
        if room:
            await add_room(room)
        return room


async def update_database_room_handler(room: Room):
    if room.room_id == '':
        logging.error('Room in cache has empty ID!')
        return

    logging.info('>>> async UPDATE DATABASE (Room) <<<')
    save_data = room.to_dict()
    logging.info(save_data)
    rooms_ref = db.reference('/rooms')
    rooms_ref.child(room.room_id).set(save_data)

update_room_event.add_handler(update_database_room_handler)