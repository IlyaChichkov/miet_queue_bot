from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from firebase import get_user_owned_rooms_list
from models.server_rooms import get_room
from roles.special_roles import GlobalRoles, get_access_level


async def get_owner_rooms_kb(user_id):
    builder = InlineKeyboardBuilder()
    rooms_list = await get_user_owned_rooms_list(user_id)

    for room_item in rooms_list:
        room = await get_room(room_item)
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
