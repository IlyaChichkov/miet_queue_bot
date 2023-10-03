from aiogram.types import Message
from aiogram.filters import BaseFilter

from firebase import get_user_room, get_room_by_key


async def check_role(user_id, role):
    room_key = await get_user_room(user_id)
    room = await get_room_by_key(room_key)
    if role in room and user_id in room[role]:
        return True
    return False


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