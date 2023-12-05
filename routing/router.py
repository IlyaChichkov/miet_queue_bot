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

    if last_message:
        successfully_updated = False
        # Пробуем обновить старое сообщение
        try:
            print(f"Edit try")
            await bot.edit_message_text(chat_id=user_id, message_id=last_message.message_id, text=message_text, reply_markup=kb)
        except Exception as ex:
            print(ex)
        finally:
            successfully_updated = True

        if not successfully_updated:
            # Не получилось обновить - создаем новое сообщение
            try:
                created_message = await bot.send_message(user_id, message_text, reply_markup=kb)
            except Exception as ex:
                print(ex)
            finally:
                await user.set_last_message(created_message)

    else:
        # Создаем новое сообщение
        try:
            created_message = await bot.send_message(user_id, message_text, reply_markup=kb)
        except Exception as ex:
            print(ex)
        finally:
            await user.set_last_message(created_message)

