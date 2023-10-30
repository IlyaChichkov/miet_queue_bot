from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_assign_note_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Назад"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_assign_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Посмотреть очередь"),
        types.KeyboardButton(text="В главное меню")
    )

    builder.row(
        types.KeyboardButton(text="✏️ Добавить примечание"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)