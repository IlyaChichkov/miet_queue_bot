from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User


async def get_remove_user_kb(user_id):
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    builder = InlineKeyboardBuilder()

    for i, room_user_id in enumerate(room.queue):
        queue_user: User = await get_user(room_user_id)
        builder.row(
            types.InlineKeyboardButton(text=f"{i}. {queue_user.name}", callback_data=f"queue_remove_{room_user_id}_{user_id}")
        )
        print(f'Remove user btn:')
        print(f"queue_remove_{room_user_id}_{user_id}")

    return builder.as_markup()

async def get_queue_settings_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(types.KeyboardButton(text="Удалить из очереди"))
    builder.row(types.KeyboardButton(text="Назад"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)