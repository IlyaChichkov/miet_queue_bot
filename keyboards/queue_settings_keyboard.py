import logging
from math import ceil

from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User

def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

async def get_remove_user_kb(user_id, current_page = 1):
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    builder = InlineKeyboardBuilder()

    users_per_page = 4
    queue_len = len(room.queue)
    if queue_len > 0:
        pages_count = ceil(queue_len / users_per_page)
        current_page_users = split_list(room.queue, users_per_page)[current_page-1]

        for i, room_user_id in enumerate(current_page_users):
            try:
                queue_user: User = await get_user(room_user_id)
                callback_data = f"queue_remove_{room_user_id}_{user_id}"
                btn = types.InlineKeyboardButton(text=f"{i+1+(users_per_page*(current_page-1))}. {queue_user.name}", callback_data=callback_data)
                if (i+1) % 2 == 0:
                    builder.add(btn)
                else:
                    builder.row(btn)
            except Exception as ex:
                logging.error(ex)
    else:
        pages_count = 1

    builder.row(
        types.InlineKeyboardButton(
            text="◀",
            callback_data=f'action#remove_from_queue#list_{current_page-1 if current_page > 1 else "none"}'
        ),
        types.InlineKeyboardButton(
            text=f"{current_page}/{pages_count}",
            callback_data='action#foo'
        ),
        types.InlineKeyboardButton(
            text="▶",
            callback_data=f'action#remove_from_queue#list_{current_page+1 if current_page < pages_count else "none"}'
        )
    )

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