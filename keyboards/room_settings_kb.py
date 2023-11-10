from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from firebase_manager.firebase import is_autoqueue_enabled

async def get_settings_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text=f"Автоочередь ({await is_autoqueue_enabled(user_id)})"),
        types.KeyboardButton(text="Изменить название")
    )

    builder.row(
        types.KeyboardButton(text='Экспорт заметок')
    )

    builder.row(
        types.KeyboardButton(text='🗑️ Удалить комнату')
    )

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    return builder.as_markup(resize_keyboard=True)