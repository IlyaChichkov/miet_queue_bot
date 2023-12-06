import logging

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
        try:
            queue_user: User = await get_user(room_user_id)
            builder.row(
                types.InlineKeyboardButton(text=f"{i}. {queue_user.name}", callback_data=f"queue_remove_{room_user_id}_{user_id}")
            )
        except Exception as ex:
            logging.error(ex)

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#queue_settings'
        )
    )
    return builder.as_markup()

async def get_queue_settings_kb():
    builder = InlineKeyboardBuilder()

    builder.row(types.InlineKeyboardButton(
        text="Сгенерировать случайную очередь",
        callback_data='action#random_queue'
    ))
    builder.row(types.InlineKeyboardButton(
        text="Удалить из очереди",
        callback_data='action#remove_from_queue'
    ))
    builder.row(types.InlineKeyboardButton(
        text="Назад",
        callback_data='show#queue_list'
    ))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)