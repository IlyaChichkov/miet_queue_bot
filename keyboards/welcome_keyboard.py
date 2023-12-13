import logging

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

    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'show#main_menu'
        )
    )

    return builder.as_markup()


async def get_welcome_kb(user_id):
    global_role: GlobalRoles = await get_access_level(user_id)
    builder = InlineKeyboardBuilder()

    if global_role is None or global_role is GlobalRoles.Empty:
        builder.row(
            types.InlineKeyboardButton(
                text="Избранное",
                callback_data='show#favorite'
            ),
            types.InlineKeyboardButton(
                text="Присоединиться к комнате",
                callback_data='action#join_room'
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text="Профиль",
                callback_data='show#profile'
            )
        )
        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

    if global_role is GlobalRoles.Developer:
        builder.row(
            types.InlineKeyboardButton(
                text="Избранное",
                callback_data='show#favorite'
            ),
            types.InlineKeyboardButton(
                text="Мои комнаты",
                callback_data='show#my_rooms'
            )
        )

        builder.row(
            types.InlineKeyboardButton(
                text="Создать комнату",
                callback_data='action#create_room'
            ),
            types.InlineKeyboardButton(
                text="Присоединиться к комнате",
                callback_data='action#join_room'
            )
        )

        builder.row(
            types.InlineKeyboardButton(
                text="Профиль",
                callback_data='show#profile'
            )
        )
        builder.row(
            types.InlineKeyboardButton(
                text="Управление",
                callback_data='show#admin_menu'
            )
        )

        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")

    if global_role is GlobalRoles.Teacher:
        builder.row(
            types.InlineKeyboardButton(
                text="Избранное",
                callback_data='show#favorite'
            ),
            types.InlineKeyboardButton(
                text="Мои комнаты",
                callback_data='show#my_rooms'
            )
        )

        builder.row(
            types.InlineKeyboardButton(
                text="Создать комнату",
                callback_data='action#create_room'
            ),
            types.InlineKeyboardButton(
                text="Присоединиться к комнате",
                callback_data='action#join_room'
            )
        )

        builder.row(
            types.InlineKeyboardButton(
                text="Помощь",
                callback_data='show#help_menu'
            ),
            types.InlineKeyboardButton(
                text="Профиль",
                callback_data='show#profile'
            )
        )
        return builder.as_markup(resize_keyboard=True, input_field_placeholder="")


async def get_favorite_rooms_kb(user_id):
    builder = InlineKeyboardBuilder()
    favorites = await get_favorite_rooms_dict(user_id)
    logging.info(favorites)
    for room_id, data in favorites.items():
        try:
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
        except Exception as ex:
            logging.error(ex)

    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'show#main_menu'
        )
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="")

