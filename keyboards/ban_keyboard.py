from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

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