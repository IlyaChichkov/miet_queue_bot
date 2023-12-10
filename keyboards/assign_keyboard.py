from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_assign_note_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#assigned_screen'
        )
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_assign_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Посмотреть очередь",
            callback_data='show#queue_list'
        ),
        types.InlineKeyboardButton(
            text="В главное меню",
            callback_data='show#room_menu'
        )
    )

    builder.row(
        types.InlineKeyboardButton(
            text="✏️ Добавить примечание",
            callback_data='action#add_note'
        )
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)