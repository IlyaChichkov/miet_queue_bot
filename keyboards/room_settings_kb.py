from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from firebase_manager.firebase import is_autoqueue_enabled

async def get_settings_kb(user_id):
    builder = InlineKeyboardBuilder()

    autoqueue = await is_autoqueue_enabled(user_id)
    msg = {
        True: 'включена',
        False: 'выключена'
    }

    builder.row(
        types.InlineKeyboardButton(
            text=f"Автоочередь {msg[autoqueue]}",
            callback_data='action#room_autoqueue_toggle'
        ),
        types.InlineKeyboardButton(
            text="Изменить название",
            callback_data='action#change_room_name')
    )

    builder.row(
        types.InlineKeyboardButton(
            text='Файл заметок',
            callback_data='action#export_notes'),
        types.InlineKeyboardButton(
            text='Черный список',
            callback_data='show#ban_menu')
    )

    builder.row(
        types.InlineKeyboardButton(
            text='🗑️ Удалить комнату',
            callback_data='action#delete_room')
    )

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#room_menu'
        )
    )
    return builder.as_markup(resize_keyboard=True)