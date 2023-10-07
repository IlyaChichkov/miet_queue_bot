import json
import logging
from typing import List

from firebase_admin import db

from models.user import User
from utils import generate_code

server_users: List[User] = []


async def get_user(user_id) -> User:
    user = [user for user in server_users if user.user_id == user_id]
    if len(user) > 0:
        print(f'> find user in cache')
        return user[0]
    else:
        print(f'> find user in db')
        user = await try_get_user_from_db(user_id)
        if user:
            await add_user(user)
        else:
            user = await create_user(user_id)

        return user


async def try_get_user_from_db(user_id) -> User:
    try:
        users_ref = db.reference(f'/users/')
        user_db = users_ref.order_by_child('tg_id').equal_to(user_id).get()
        return load_room_from_json(user_db)
    except Exception as e:
        logging.warning(f'Load user from database failed. Exception: {str(e)}')
        return None


def load_room_from_json(db_user) -> User:
    user_key, user_data = list(db_user.items())[0]
    if db_user is None:
        return None

    user = User(user_data['name'])
    user.db_key = user_key
    user.set_user_id(user_data['tg_id'])
    if 'room' in user_data:
        user.room = user_data['room']

    if 'current_role' in user_data:
        user.current_role = user_data['current_role']
    return user


async def create_user(user_id) -> User:
    logging.info(f'Creating new user')
    user = User(f'User_{generate_code(5)}')
    user.set_user_id(user_id)

    users_ref = db.reference('/users')
    user_ref = users_ref.push(user.to_dict())

    user.db_key = user_ref.key
    await add_user(user)
    return user


async def add_user(user: User):
    logging.info(f'Caching new user: {user.user_id}')
    server_users.append(user)