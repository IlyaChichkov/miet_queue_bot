import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_conf.bot import bot
from firebase_manager.firebase import get_db_data
from routing.router import handle_message

router = Router()


@router.callback_query(F.data == "show#help_menu")
async def show_help_menu_call(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    help_message: str = await get_db_data("help_message")
    help_message = help_message.replace('\\n', '\n')
    await handle_message(callback.from_user.id, help_message, kb)