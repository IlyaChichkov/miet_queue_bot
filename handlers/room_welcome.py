import logging

from aiogram import Router, F, types

from bot import bot
from events.queue_events import queue_enable_state_event
from firebase import db_get_user_room, is_user_name_default, get_room_by_key, get_user_name
from message_forms.room_forms import get_welcome_message
from states.room import RoomVisiterState

router = Router()

# can add user join notification to moderators
# update_queue_event.add_handler(update_list_for_users)


async def welcome_room(message: types.Message, user_id = None):
    '''
    Вывод сообщения главного меню комнаты
    '''
    if not user_id:
        user_id = message.from_user.id
    room = await db_get_user_room(user_id)
    user_name = await get_user_name(user_id)

    if 'room' in room:
        if await is_user_name_default(user_id):
            await message.answer(f'ℹ️ Ваше имя соответствует стандартному: «<b>{user_name}</b>». Пожалуйста поменяйте его в настройках профиля (Имя Фамилия №ПК)', parse_mode="HTML")
        mesg = await get_welcome_message(user_id, room['room'])
        await message.answer(mesg['mesg_text'], parse_mode="HTML", reply_markup=mesg['keyboard'])
    else:
        await message.answer(f"Произошла ошибка при присоединении к комнате.\n"
                             f"{room['error']}")


@router.message(RoomVisiterState.ROOM_WELCOME_SCREEN)
async def welcome_room_state(message: types.Message):
    await welcome_room(message)