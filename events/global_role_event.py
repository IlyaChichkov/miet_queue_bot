from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from events.event import AsyncEvent
from handlers.room_welcome import welcome_room
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.special_roles import GlobalRoles
from routing.router import handle_message

update_user_global_role_event = AsyncEvent()


async def update_user(user_id, role: GlobalRoles):
    builder = InlineKeyboardBuilder()

    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    if room is not None:
        builder.row(
            types.InlineKeyboardButton(
                text="Меню комнаты",
                callback_data='show#room_menu')
        )
    else:
        builder.row(
            types.InlineKeyboardButton(
                text="Главное меню",
                callback_data='show#main_menu')
        )

    kb = builder.as_markup(resize_keyboard=True)
    await handle_message(user_id, f'Ваша глобальная роль была изменена на {role}', kb)


update_user_global_role_event.add_handler(update_user)