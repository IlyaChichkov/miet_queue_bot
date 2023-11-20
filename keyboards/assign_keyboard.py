from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_add_score_kb(tutor_id, assigned_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="10", callback_data=f"addscore#{tutor_id}_{assigned_id}_10"),
        types.InlineKeyboardButton(text="5", callback_data=f"addscore#{tutor_id}_{assigned_id}_5"),
        types.InlineKeyboardButton(text="Назад", callback_data=f"addscore#back"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


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
        types.KeyboardButton(text="💯 Поставить баллы"),
        types.KeyboardButton(text="✏️ Добавить примечание"),
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)