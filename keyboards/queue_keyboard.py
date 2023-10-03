from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_queue_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(types.KeyboardButton(text="Назад"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def get_admin_queue_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Вытянуть рандомного"),
        types.KeyboardButton(text="Вытянуть первого")
    )

    builder.row(types.KeyboardButton(text="Назад"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_queue_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="Принять первого",
                                   callback_data="queue_pop")
    )

    return builder.as_markup()