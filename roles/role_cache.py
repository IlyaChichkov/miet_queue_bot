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
        await cache_user_role(user_id, role)

    logging.info(f'Check USER_{user_id} current role: {role}. Cached: {is_cached}.')
    return role


async def cache_user_role(user_id, role):
    users_role_cache[user_id] = role


async def delete_user_role_cache(user_id):
    users_role_cache.pop(user_id)