import asyncio
import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from bot_conf.bot import bot
from events.queue_events import update_queue_event, users_notify_queue_changed_event, user_joined_queue_event, \
    users_notify_queue_skipped, favorite_toggle_event, user_leave_room_event
from firebase_manager.firebase import db_get_user_room, is_user_name_default, get_user_name
from message_forms.room_forms import get_welcome_message
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from routing.router import handle_message, send_message, answer_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState

router = Router()

main_message_cache = {}
queue_message_cache = {}


@router.callback_query(F.data == 'show#room_menu')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room(callback.from_user.id)


async def welcome_room(user_id):
    '''
    Вывод сообщения главного меню комнаты
    '''
    room = await db_get_user_room(user_id)
    user: User = await get_user(user_id)

    if 'room' in room:
        if await is_user_name_default(user_id):
            await send_message(user_id, f'ℹ️ Ваше имя соответствует стандартному: «<b>{user.name}</b>». Пожалуйста поменяйте его в настройках профиля (Имя Фамилия №ПК)')
        mesg = await get_welcome_message(user_id, room['room'])
        menu_text = mesg['mesg_text']
        if mesg['queue_list'] != '':
            menu_text = mesg['mesg_text'] + '\n' + mesg['queue_list']
        await handle_message(user_id, menu_text, reply_markup=mesg['keyboard'])
        await user.set_route(UserRoutes.RoomMenu)

    else:
        await send_message(f"Произошла ошибка при присоединении к комнате.\n"
                             f"{room['error']}")


@router.message(RoomVisiterState.ROOM_WELCOME_SCREEN)
async def welcome_room_state(message: types.Message):
    await welcome_room(message.from_user.id)


async def update_handler(room_id, user_id):
    room: Room = await get_room(room_id)
    for room_user in room.get_users_list():
        user: User = await get_user(room_user)
        if user.route is UserRoutes.RoomMenu:
            await welcome_room(room_user)


user_leave_room_event.add_handler(update_handler)
update_queue_event.add_handler(update_handler)