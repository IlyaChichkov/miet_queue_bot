
import logging

from bot_conf.bot import bot
from events.queue_events import update_queue_event
from models.room import Room
from models.server_rooms import get_room

async def user_notify(room_id, user_id):
    '''
    Уведомление пользователей об изменении в очереди
    '''
    room: Room = await get_room(room_id)
    for user_num, user_in_queue in enumerate(room.queue):
        if user_in_queue == user_id:
            continue
        try:
            await bot.send_message(user_in_queue, f'Очередь сдвинулась, вы на <b>{user_num + 1}</b> месте', parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_queue} (user) about queue changed, but got error: {ex}")


update_queue_event.add_handler(user_notify)