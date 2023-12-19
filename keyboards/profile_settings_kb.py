from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from firebase_manager.firebase import get_user_role_at_room
from roles.user_roles_enum import UserRoles


async def get_settings_kb(user_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Удалить профиль",
            callback_data=f'action#delete_profile'
        ),
        types.InlineKeyboardButton(
            text="Изменить имя",
            callback_data=f'action#change_name'
        )
    )

    role = await get_user_role_at_room(user_id)
    if role and role is not UserRoles.User:
        builder.row(
            types.InlineKeyboardButton(
                text="Мои заметки",
                callback_data=f'show#my_notes'
            ),
            types.InlineKeyboardButton(
                text="История",
                callback_data=f'show#assign_history'
            )
        )

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data=f'show#main_menu'
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
    builder.row(
        types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'show#profile'
        )
    )

    return builder.as_markup(resize_keyboard=True)