import logging

from bot_conf.bot import bot
from events.queue_events import user_joined_queue_event
from models.server_users import get_user
from models.user import User


async def joined_notify(room, user_id, place, notify_mod):
    if notify_mod:
        await moderator_notify(room, user_id)
    await user_notify(room, user_id, place)


async def user_notify(room, user_id, place):
    try:
        message = f"Вы присоединились к очереди!\n#️⃣ Ваше место в очереди: <b>{place}</b>"
        await bot.send_message(user_id, message, parse_mode="HTML")
    except Exception as ex:
        logging.info(f"Tried to notify USER_{user_id} (user) about queue join, but got error: {ex}")


async def moderator_notify(room, user_id):
    '''
    Уведомление о новом присоединившемся к очереди пользователе
    '''
    user: User = await get_user(user_id)

    message_form = f'«<b>{user.name}</b>» присоединился к очереди'

    for user_num, user_in_room in enumerate(room.moderators):
        try:
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_id} (moderator) about queue join, but got error: {ex}")

    for user_num, user_in_room in enumerate(room.admins):
        try:
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_id} (admin) about queue join, but got error: {ex}")


user_joined_queue_event.add_handler(joined_notify)