import logging

from models.server_users import get_user
import enum


class GlobalRoles(enum.Enum):
    Empty = 0
    Developer = 1
    Teacher = 2


async def check_access_level(user_id, access_level: GlobalRoles):
    logging.info(f'Check if USER_{user_id} has {access_level} access level')
    global_role = await get_access_level(user_id)
    if global_role is None:
        return False
    if access_level.value >= GlobalRoles(global_role).value:
        return True
    return False


async def get_access_level(user_id):
    user = await get_user(user_id)
    global_role = await user.get_global_role()
    if global_role is None:
        return None
    return GlobalRoles(global_role)