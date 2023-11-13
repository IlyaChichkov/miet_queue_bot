from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from firebase_manager.firebase import get_user_owned_rooms_list, get_favorite_rooms_dict
from models.server_rooms import get_room
from roles.special_roles import GlobalRoles, get_access_level


async def get_owner_rooms_kb(user_id):
    builder = InlineKeyboardBuilder()
    rooms_list = await get_user_owned_rooms_list(user_id)

    for room_item in rooms_list:
        room = await get_room(room_item)
        if room:
            builder.row(
                types.InlineKeyboardButton(text=room.name,
                                           callback_data=f"connect_room#{room_item}")
            )

    return builder.as_markup()


async def get_welcome_kb(user_id):
    global_role: GlobalRoles = await get_access_level(user_id)

    if global_role is None:
        builder = ReplyKeyboardBuilder()

        builder.row(
            types.KeyboardButton(
                text="Избранное"
            ),
            types.KeyboardButton(
                text="Присоединиться к комнате"
            )
        )

        builder.row(
            types.KeyboardButton(
                text="Профиль"
            )
        )
        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

    if global_role is GlobalRoles.Developer:
        builder = ReplyKeyboardBuilder()

        builder.row(
            types.KeyboardButton(
                text="Избранное"
            ),
            types.KeyboardButton(
                text="Мои комнаты"
            )
        )

        builder.row(
            types.KeyboardButton(
                text="Создать комнату"
            ),
            types.KeyboardButton(
                text="Присоединиться к комнате"
            )
        )

        builder.row(
            types.KeyboardButton(
                text="Профиль"
            )
        )
        builder.row(
            types.KeyboardButton(
                text="Посмотреть кэш"
            ),
            types.KeyboardButton(
                text="Обновить кэш"
            )
        )
        builder.row(
            types.KeyboardButton(
                text="Удалить кэш"
            ),
            types.KeyboardButton(
                text="Добавить преподавателя"
            )
        )
        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

    if global_role is GlobalRoles.Teacher:
        builder = ReplyKeyboardBuilder()

        builder.row(
            types.KeyboardButton(
                text="Избранное"
            ),
            types.KeyboardButton(
                text="Мои комнаты"
            )
        )

        builder.row(
            types.KeyboardButton(
                text="Создать комнату"
            ),
            types.KeyboardButton(
                text="Присоединиться к комнате"
            )
        )

        builder.row(
            types.KeyboardButton(
                text="Профиль"
            )
        )
        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")


async def get_favorite_rooms_kb(user_id):
    builder = InlineKeyboardBuilder()
    favorites = await get_favorite_rooms_dict(user_id)
    for room_id, data in favorites.items():
        room = data['room']
        role = data['role']
        room_list_to_role = {
            'users': 'Пользователь',
            'moderators': 'Модератор',
            'admins': 'Админ'
        }
        builder.row(
            types.InlineKeyboardButton(
                text=f'{room.name} ({room_list_to_role[role]})',
                callback_data=f'join_fav_room#{room.room_id}#{role}'
            )
        )

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="")

