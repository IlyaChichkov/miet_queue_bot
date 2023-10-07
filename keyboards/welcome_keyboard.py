from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_welcome_kb():
    builder = ReplyKeyboardBuilder()

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