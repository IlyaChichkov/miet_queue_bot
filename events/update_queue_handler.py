
import logging

from bot_conf.bot import bot
from events.queue_events import users_notify_queue_changed_event

async def users_notify(users, users_before_count):
    '''
    Уведомление пользователей об изменении в очереди
    '''
    for user_num, user_in_queue in enumerate(users):
        try:
            await bot.send_message(user_in_queue, f'Очередь сдвинулась, вы на <b>{user_num + users_before_count + 1}</b> месте', parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_queue} (user) about queue changed, but got error: {ex}")


users_notify_queue_changed_event.add_handler(users_notify)