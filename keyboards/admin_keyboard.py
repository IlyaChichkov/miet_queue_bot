import logging

from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from firebase_manager.firebase import get_user_owned_rooms_list, get_favorite_rooms_dict
from models.server_rooms import get_room
from roles.special_roles import GlobalRoles, get_access_level


async def get_admin_kb(user_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Удалить кэш",
            callback_data='action#delete_server_cache'
        ),
        types.InlineKeyboardButton(

            text="Посмотреть кэш",
            callback_data='show#server_cache'
        ),
        types.InlineKeyboardButton(
            text="Обновить кэш",
            callback_data='action#update_server_cache'
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )

    return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

