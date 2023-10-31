import logging
from firebase import get_user_current_role

users_role_cache = {}


async def get_user_role(user_id):
    is_cached = False
    role = None
    if user_id in users_role_cache:
        is_cached = True
        role = users_role_cache[user_id]
    else:
        role = await get_user_current_role(user_id)
        if role != '':
            await cache_user_role(user_id, role)

    logging.info(f'Check USER_{user_id} current role: {role}. Cached: {is_cached}.')
    return role


async def cache_user_role(user_id, role):
    logging.info(f'Cache user role for: {user_id} as {role}')
    users_role_cache[user_id] = role


async def delete_user_role_cache(user_id):
    logging.info(f'Delete role cache for: {user_id}')
    if user_id in users_role_cache:
        users_role_cache.pop(user_id)
    else:
        logging.warning(f'USER_{user_id}: Tried to delete role cache, but it\'s empty')