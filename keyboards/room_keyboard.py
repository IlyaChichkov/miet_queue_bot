from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from firebase import is_user_in_queue


async def get_admin_welcome_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Посмотреть очередь"),
        types.KeyboardButton(text="Принять первого в очереди")
    )

    builder.row(types.KeyboardButton(text="Настройки комнаты"))

    builder.row(
        types.KeyboardButton(
            text="Удалить комнату"
        ),
        types.KeyboardButton(
            text="Профиль"
        )
    )
    return builder.as_markup(resize_keyboard=True)

async def get_moderator_welcome_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Посмотреть очередь"),
        types.KeyboardButton(text="Принять первого в очереди")
    )

    # builder.row(types.KeyboardButton(text="Принять случайного студента"))

    builder.row(
        types.KeyboardButton(
            text="Выйти"
        ),
        types.KeyboardButton(
            text="Профиль"
        )
    )
    return builder.as_markup(resize_keyboard=True)

async def get_user_welcome_kb(user_id):
    builder = ReplyKeyboardBuilder()

    user_in_queue = await is_user_in_queue(user_id)

    if not user_in_queue:
        builder.row(types.KeyboardButton(text="Занять место"))
    else:
        builder.row(types.KeyboardButton(text="Выйти из очереди"))

    builder.row(
        types.KeyboardButton(
            text="Выйти"
        ),
        types.KeyboardButton(
            text="Профиль"
        )
    )
    return builder.as_markup(resize_keyboard=True)
