import logging

from aiogram import types

from bot import bot
from events.queue_events import queue_enable_state_event, user_joined_event
from firebase import get_room_by_key
from models.server_users import get_user
from models.user import User


async def joined_notify(room, user_id, user_role):
    if user_role == 'user':
        await user_joined_notify(room, user_id)
    if user_role == 'moderator':
        await moderator_joined_notify(room, user_id)


async def user_joined_notify(room, user_id):
    '''
    Уведомление о новом присоединившемся пользователе
    '''
    user: User = await get_user(user_id)

    message_form = f'Пользователь «<b>{user.name}</b>» присоединился к комнате'

    for user_num, user_in_room in enumerate(room.admins):
        try:
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_room} (admin) about user joined room, but got error: {ex}")


async def moderator_joined_notify(room, user_id):
    '''
    Уведомление о новом присоединившемся модераторе
    '''
    user: User = await get_user(user_id)

    message_form = f'Модератор «<b>{user.name}</b>» присоединился к комнате'

    for user_num, user_in_room in enumerate(room.users):
        try:
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_room} (user) about moderator joined room, but got error: {ex}")

    for user_num, user_in_room in enumerate(room.admins):
        try:
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_room} (admin) about moderator joined room, but got error: {ex}")


# user_joined_event.add_handler(joined_notify)