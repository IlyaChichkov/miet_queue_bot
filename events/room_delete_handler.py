import logging

from events.queue_events import delete_room_event
from aiogram import types

from bot_conf.bot import bot


async def room_deleted_notify(users_id_list):
    '''
    Уведомление об удалении комнаты
    '''

    for user_num, user_in_queue in enumerate(users_id_list):
        try:
            await bot.send_message(user_in_queue, f'Комната в который вы находились была удалена.', parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_queue} about room had been deleted, but got error: {ex}")


delete_room_event.add_handler(room_deleted_notify)