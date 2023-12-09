import logging
from math import ceil

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User


def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


async def get_ban_kb(user_id, ban_toggle: bool, current_page = 1):
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    builder = InlineKeyboardBuilder()

    users_per_page = 4
    callback_type = ''
    if ban_toggle:
        callback_type = 'ban_user'
        operate_users_list = room.get_users_list()
        operate_users_list.remove(user_id)
    else:
        callback_type = 'remove_ban'
        operate_users_list = room.banned

    queue_len = len(operate_users_list)
    if queue_len > 0:
        pages_count = ceil(queue_len / users_per_page)
        current_page_users = split_list(operate_users_list, users_per_page)[current_page-1]

        for i, room_user_id in enumerate(current_page_users):
            try:
                queue_user: User = await get_user(room_user_id)
                callback_data = f"action#initban_{ban_toggle}_{room_user_id}_{user_id}"
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
            callback_data=f'action#{callback_type}#list_{current_page-1 if current_page > 1 else "none"}'
        ),
        types.InlineKeyboardButton(
            text=f"{current_page}/{pages_count}",
            callback_data='action#foo'
        ),
        types.InlineKeyboardButton(
            text="▶",
            callback_data=f'action#{callback_type}#list_{current_page+1 if current_page < pages_count else "none"}'
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#ban_menu'
        )
    )
    return builder.as_markup()


async def get_ban_menu_kb(user_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Добавить пользователя",
            callback_data='action#ban_user'),
        types.InlineKeyboardButton(
            text="Убрать пользователя",
            callback_data='action#remove_ban')
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#room_settings')
    )
    return builder.as_markup(resize_keyboard=True)