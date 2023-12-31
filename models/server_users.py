import logging
from typing import List

from firebase_admin import db
from firebase_admin.exceptions import FirebaseError

from models.user import User
from utils import generate_code

server_users_dict: dict[int, User] = {}


async def get_user(user_id, create_new = False) -> User:
    user_id = int(user_id)
    logging.info(f'Get USER_{user_id}')

    if user_id in server_users_dict:
        return server_users_dict[user_id]
    else:
        logging.info(f'Try pooling user from database USER_{user_id}')
        user = await try_get_user_from_db(user_id)
        if user:
            await add_user(user_id, user)
        else:
            if create_new:
                user = await create_user(user_id)

        return user


async def try_get_user_from_db(user_id) -> User:
    try:
        user_id = int(user_id)
        users_ref = db.reference(f'/users/')
        user_db = users_ref.order_by_child('tg_id').equal_to(user_id).get()
        user_key, user_data = list(user_db.items())[0]
        return await load_user_from_json(user_key, user_data)
    except Exception as e:
        logging.warning(f'Load user from database failed. Exception: {str(e)}')
        return None


async def load_user_from_json(user_key, user_data) -> User:
    if user_data is None:
        return None

    user = User(user_data['name'])
    user.db_key = user_key
    user.set_user_id(user_data['tg_id'])

    if 'own_rooms' in user_data:
        user.owned_rooms = user_data['own_rooms']

    if 'room' in user_data:
        user.room = user_data['room']

    if 'favorites' in user_data:
        user.favorites = user_data['favorites']

    if 'current_role' in user_data:
        user.current_role = user_data['current_role']

    if 'has_verified_name' in user_data:
        user.has_verified_name = user_data['has_verified_name']

    if 'route' in user_data:
        from routing.user_routes import UserRoutes
        await user.set_route(UserRoutes(int(user_data['route'])))
    return user


async def create_user(user_id) -> User:
    user = User(f'User_{generate_code(5)}')
    user.set_user_id(user_id)
    logging.info(f'Add new user | USER_{user_id}')

    users_ref = db.reference('/users')
    user_ref = users_ref.push(user.to_dict())

    user.db_key = user_ref.key
    await add_user(user_id, user)
    return user


async def add_user(user_id, user: User):
    logging.info(f'Caching USER_{user.user_id}')
    user.check_has_default_name()
    server_users_dict[int(user_id)] = user


async def get_total_users_count():
    return len(server_users_dict)


async def remove_user_from_db(user_id):
    try:
        user = await get_user(user_id)

        from firebase_manager.firebase import leave_room
        await leave_room(user_id)
        users_ref = db.reference('/users')
        users_ref.child(user.db_key).delete()

        logging.info(f'USER_{user_id} was deleted from database')
        if user in server_users_dict:
            del server_users_dict[user_id]
        return True
    except Exception as ex:
        logging.error(f'Failed to delete USER_{user_id} from database. Error: {ex}')
        return False