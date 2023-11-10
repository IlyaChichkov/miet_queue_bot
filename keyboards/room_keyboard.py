from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from firebase_manager.firebase import is_user_in_queue, get_room_queue_enabled_by_userid


async def get_admin_welcome_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Посмотреть очередь"),
        types.KeyboardButton(text="Принять первого в очереди")
    )

    builder.row(types.KeyboardButton(text="Настройки комнаты"))
    builder.row(
        types.KeyboardButton(text="Сделать уведомление"),
        types.KeyboardButton(text="Список пользователей")
    )

    builder.row(
        types.KeyboardButton(
            text="Выйти"
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

    builder.row(types.KeyboardButton(text="Список пользователей"))

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

    queue_enabled = await get_room_queue_enabled_by_userid(user_id)
    if queue_enabled:
        if not user_in_queue:
            builder.row(types.KeyboardButton(text="Занять место"))
        else:
            builder.row(types.KeyboardButton(text="Выйти из очереди"))
    else:
        builder.row(types.KeyboardButton(text="Очередь заблокирована"))

    builder.row(
        types.KeyboardButton(
            text="Выйти"
        ),
        types.KeyboardButton(
            text="Профиль"
        )
    )
    return builder.as_markup(resize_keyboard=True)


def get_users_list_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    return builder.as_markup(resize_keyboard=True)
