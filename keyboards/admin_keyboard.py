import logging

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
        types.InlineKeyboardButton(text="Журналы событий", callback_data='action#get_log_files'),
        types.InlineKeyboardButton(text="Управление ролями", callback_data='show#global_role_settings')
    )
    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )

    return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

