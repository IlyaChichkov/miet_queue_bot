import logging

from aiogram import Router, types

from bot_conf.bot import bot
from events.queue_events import update_queue_event, users_notify_queue_changed_event, user_joined_queue_event, \
    users_notify_queue_skipped
from firebase_manager.firebase import db_get_user_room, is_user_name_default, get_user_name
from message_forms.room_forms import get_welcome_message
from models.room import Room
from models.server_rooms import get_room
from states.room_state import RoomVisiterState

router = Router()


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


async def update_welcome_room(room_id):
    return
    # TODO: Update main room's message
    room: Room = await get_room(room_id)
    for room_user in room.users:
        try:
            user_name = await get_user_name(room_user)
            if await is_user_name_default(room_user):
                pass
                #await bot.send_message(room_user, f'ℹ️ Ваше имя соответствует стандартному: «<b>{user_name}</b>». Пожалуйста поменяйте его в настройках профиля (Имя Фамилия №ПК)', parse_mode="HTML")
            mesg = await get_welcome_message(room_user, room)
            await bot.send_message(room_user, mesg['mesg_text'], parse_mode="HTML", reply_markup=mesg['keyboard'])
        except Exception as ex:
            logging.info(f"Tried to update main room screen USER_{room_user} (user) because queue changed, but got error: {ex}")


async def users_notify_handler(users):
    if len(users) > 0:
        from models.server_users import get_user
        user = await get_user(users[0])
        await update_welcome_room(user.room)


users_notify_queue_changed_event.add_handler(users_notify_handler)


async def user_joined_handler(room, user_id, place, notify_mod):
    await update_welcome_room(room.room_id)


user_joined_queue_event.add_handler(user_joined_handler)


async def users_notify_queue_skipped_handler(pass_user_id, user_name, user_index):
    from models.server_users import get_user
    user = await get_user(pass_user_id)
    await update_welcome_room(user.room)


users_notify_queue_skipped.add_handler(users_notify_queue_skipped_handler)


@router.message(RoomVisiterState.ROOM_WELCOME_SCREEN)
async def welcome_room_state(message: types.Message):
    await welcome_room(message)