from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from firebase_manager.firebase import get_user_role_at_room
from roles.user_roles_enum import UserRoles


async def get_settings_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Удалить профиль"),
        types.KeyboardButton(text="Изменить имя")
    )

    role = await get_user_role_at_room(user_id)
    if role and role is not UserRoles.User:
        builder.row(types.KeyboardButton(text="Мои заметки"))

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    return builder.as_markup(resize_keyboard=True)


async def get_delete_profile_kb(user_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text='Удалить профиль 🗑️',
            callback_data=f'delete_profile#{user_id}'
        )
    )

    return builder.as_markup(resize_keyboard=True)