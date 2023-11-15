
import logging

from bot_conf.bot import bot
from events.queue_events import users_notify_queue_skipped

async def skipped_user_notify(skipped_user_id, skiping_user_name, new_place):
    '''
    Уведомление пользователей об изменении в очереди
    '''
    try:
        await bot.send_message(skipped_user_id, f'Вас пропустил вперед «<b>{skiping_user_name}</b>», вы на <b>{new_place}</b> месте', parse_mode="HTML")
    except Exception as ex:
        logging.info(f"Tried to notify USER_{skipped_user_id} (user) were allowed to go ahead, but got error: {ex}")


users_notify_queue_skipped.add_handler(skipped_user_notify)