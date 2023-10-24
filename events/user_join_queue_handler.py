from aiogram import types

from bot import bot
from events.queue_events import user_joined_queue_event
from firebase import get_room_by_key
from models.server_users import get_user
from models.user import User


async def joined_notify(room, user_id):
    print('queue join notify')
    await moderator_notify(room, user_id)


async def moderator_notify(room, user_id):
    '''
    Уведомление о новом присоединившемся к очереди пользователе
    '''
    user: User = await get_user(user_id)

    message_form = f'«<b>{user.name}</b>» присоединился к очереди'

    print(user_id)
    for user_num, user_in_room in enumerate(room.moderators):
        await bot.send_message(user_in_room, message_form, parse_mode="HTML")

    for user_num, user_in_room in enumerate(room.admins):
        print(user_in_room)
        await bot.send_message(user_in_room, message_form, parse_mode="HTML")


user_joined_queue_event.add_handler(joined_notify)

