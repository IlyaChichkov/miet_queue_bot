import logging
from aiogram import Router
from events.queue_events import user_assigned_event
from firebase_manager.firebase import get_user_name
from routing.router import send_message

router = Router()


async def assign_user(moderator_id, user_id):
    '''
    Отправка сообщения пользователю о том, что его готовы принять.
    Остальным пользователя о том, какое теперь место в очереди они занимают
    '''
    try:
        user_name = await get_user_name(moderator_id)
        await send_message(user_id, f'Вас принял для сдачи: <b>{user_name}</b>')
    except Exception as e:
        logging.error(str(e))


user_assigned_event.add_handler(assign_user)