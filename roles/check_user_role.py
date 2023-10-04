from aiogram.types import Message
from aiogram.filters import BaseFilter
from roles.role_cache import get_user_role


async def check_role(user_id, role):
    return role == await get_user_role(user_id)


class IsModerator(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        return await check_role(message.from_user.id, 'moderators')


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        return await check_role(message.from_user.id, 'admins')


class IsUser(BaseFilter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message) -> bool:
        return await check_role(message.from_user.id, 'users')