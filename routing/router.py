import logging

from aiogram import types

from bot_conf.bot import bot
from models.server_users import get_user
from models.user import User


async def handle_message(user_id, message_text, reply_markup=None):
    user_id = str(user_id)
    user: User = await get_user(user_id)
    last_message = user.last_message
    print(f"USER has last message: {last_message is not None}")
    created_message = None
    kb = reply_markup

    if kb and kb is types.KeyboardButton:
        print("[WARNING!] Default Keyboard passed to router!")

    if last_message and not user.create_new_message:
        successfully_updated = False
        # Пробуем обновить старое сообщение
        try:
            successfully_updated = True
            await bot.edit_message_text(chat_id=user_id, message_id=last_message.message_id, text=message_text, reply_markup=kb, parse_mode="HTML")
        except Exception as ex:
            if "message is not modified" in str(ex):
                logging.warning(ex)
            else:
                logging.error(ex)
                successfully_updated = False

        if not successfully_updated:
            # Не получилось обновить - создаем новое сообщение
            try:
                created_message = await bot.send_message(user_id, message_text, reply_markup=kb, parse_mode="HTML")
            except Exception as ex:
                logging.error(ex)
            finally:
                await user.set_last_message(created_message)

    else:
        if last_message and user.create_new_message:
            # Удаляем старое
            try:
                await bot.delete_message(user_id, last_message.message_id)
            except Exception as ex:
                logging.error(ex)
        # Создаем новое сообщение
        try:
            created_message = await bot.send_message(user_id, message_text, reply_markup=kb, parse_mode="HTML")
        except Exception as ex:
            logging.error(ex)
        finally:
            await user.set_last_message(created_message)


async def send_document(user_id, document, message_text):
    user: User = await get_user(user_id)
    user.create_new_message = True
    try:
        await bot.send_document(user_id, document=document, caption=message_text, parse_mode="HTML")
    except Exception as ex:
        logging.error(ex)


async def send_message(user_id, message_text):
    user: User = await get_user(user_id)
    user.create_new_message = True
    try:
        await bot.send_message(user_id, message_text, parse_mode="HTML")
    except Exception as ex:
        logging.error(ex)


async def answer_message(message: types.Message, message_text):
    user: User = await get_user(message.from_user.id)
    user.last_message = None
    await message.answer(message_text, parse_mode="HTML")
