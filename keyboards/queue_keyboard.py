from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_queue_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(types.KeyboardButton(text="Назад"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


async def get_admin_queue_kb():
    builder = ReplyKeyboardBuilder()

    builder.row(types.KeyboardButton(text="Включить очередь"))
    builder.row(types.KeyboardButton(text="Назад"))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_queue_kb(is_queue_empty):
    builder = InlineKeyboardBuilder()

    if not is_queue_empty:
        builder.row(
            types.InlineKeyboardButton(text="Принять первого",
                                       callback_data="action#queue_pop")
        )


    return builder.as_markup()