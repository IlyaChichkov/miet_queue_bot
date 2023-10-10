import json
import logging
from typing import List
from firebase_admin import db

from models.server_passwords import server_passwords
from models.server_rooms import server_rooms, load_room_from_json, add_room
from models.server_users import server_users, load_user_from_json, add_user


async def check_admin(user_id):
    admin_ids_ref = db.reference(f'/bot_admins')
    admin_ids: List[str] = admin_ids_ref.get()
    if str(user_id) in admin_ids:
        return True
    return False


async def show_cache():
    message = 'Rooms:\n'
    for num, room in enumerate(server_rooms):
        r = json.dumps(room.to_dict())
        loaded_r = json.loads(r)
        message += f' {num+1}) {json.dumps(loaded_r, indent=2)}\n'

    message += 'Users:\n'
    for num, user in enumerate(server_users):
        r = json.dumps(user.to_dict())
        loaded_r = json.loads(r)
        message += f' {num+1}) {json.dumps(loaded_r, indent=2)}\n'

    return message


async def __load_rooms():
    rooms_ref = db.reference(f'/rooms').get()
    rooms_list = list(rooms_ref.items())
    for room in rooms_list:
        room_key, room_data = room
        loaded_room = load_room_from_json(room_key, room_data)
        await add_room(loaded_room)

    users_ref = db.reference(f'/users').get()
    users_list = list(users_ref.items())
    for user in users_list:
        user_key, user_data = user
        loaded_user = load_user_from_json(user_key, user_data)
        await add_user(loaded_user)


async def update_cache():
    await delete_cache()
    await __load_rooms()


async def delete_cache():
    server_rooms.clear()
    server_users.clear()
    server_passwords.clear()