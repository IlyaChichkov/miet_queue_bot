from aiogram import types

from bot import bot
from events.queue_events import queue_enable_state_event, user_joined_event
from firebase import get_room_by_key

async def joined_notify(room_key, user_data, user_role):
    if user_role == 'user':
        await user_joined_notify(room_key, user_data)
    if user_role == 'moderator':
        await moderator_joined_notify(room_key, user_data)


async def user_joined_notify(room_key, user_data):
    '''
    Уведомление о новом присоединившемся пользователе
    '''
    room = await get_room_by_key(room_key)
    user_name = user_data['name']

    message_form = f'Пользователь «<b>{user_name}</b>» присоединился к комнате'

    if 'admins' in room:
        for user_num, user_in_room in enumerate(room['admins']):
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")


async def moderator_joined_notify(room_key, user_data):
    '''
    Уведомление о новом присоединившемся модераторе
    '''
    room = await get_room_by_key(room_key)
    user_name = user_data['name']

    message_form = f'Модератор «<b>{user_name}</b>» присоединился к комнате'

    if 'users' in room:
        for user_num, user_in_room in enumerate(room['users']):
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")

    if 'admins' in room:
        for user_num, user_in_room in enumerate(room['admins']):
            await bot.send_message(user_in_room, message_form, parse_mode="HTML")


user_joined_event.add_handler(joined_notify)