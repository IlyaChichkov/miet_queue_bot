import asyncio
import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from events.queue_events import update_queue_event, user_leave_room_event, queue_enable_state_event, user_joined_event
from message_forms.room_forms import get_welcome_message
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from routing.router import handle_message, send_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState

router = Router()

main_message_cache = {}
queue_message_cache = {}
updated_rooms = set()
room_timers = {}


@router.callback_query(F.data == 'show#room_menu')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room(callback.from_user.id)


async def welcome_room(user_id):
    '''
    Вывод сообщения главного меню комнаты
    '''
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)

    if room:
        mesg = await get_welcome_message(user, room)
        menu_text = mesg['mesg_text']
        if mesg['queue_list'] != '':
            menu_text = mesg['mesg_text'] + '\n' + mesg['queue_list']
        await handle_message(user_id, menu_text, reply_markup=mesg['keyboard'])
        await user.set_route(UserRoutes.RoomMenu)
    else:
        await send_message(f"Произошла ошибка при присоединении к комнате.\n")


@router.message(RoomVisiterState.ROOM_WELCOME_SCREEN)
async def welcome_room_state(message: types.Message):
    await welcome_room(message.from_user.id)


async def debounce_update_handler(room_id):
    global updated_rooms

    if room_id not in updated_rooms:
        updated_rooms.add(room_id)

        async def wait_and_call_update(room_id):
            from firebase_manager.firebase import get_db_data
            delay: float = float(await get_db_data("update_debounce_delay"))
            await asyncio.sleep(delay)
            await update_handler(room_id)
            updated_rooms.discard(room_id)

        room_timers[room_id] = asyncio.create_task(wait_and_call_update(room_id))


async def update_handler(room_id):
    logging.info('-- UPDATE OTHER USERS MENU --')
    room: Room = await get_room(room_id)
    for room_user in room.get_users_list():
        user: User = await get_user(room_user)
        logging.info(f'-- UPDATE USER_{room_user} by ROUTE {user.route} --')
        if user.route is UserRoutes.RoomMenu:
            await welcome_room(room_user)


async def queue_enable_state_event_handler(room_id, user_id):
    logging.info('-- queue_enable_state_event --')
    await asyncio.create_task(debounce_update_handler(room_id))


async def user_leave_room_event_handler(room_id, user_id):
    logging.info('-- user_leave_room_event_handler --')
    await asyncio.create_task(debounce_update_handler(room_id))


async def user_joined_event_handler(room_id, user_id):
    logging.info('-- user_joined_event_handler --')
    await asyncio.create_task(debounce_update_handler(room_id))


async def update_queue_event_handler(room_id, user_id):
    logging.info('-- update_queue_event --')
    await asyncio.create_task(debounce_update_handler(room_id))


queue_enable_state_event.add_handler(queue_enable_state_event_handler)
user_leave_room_event.add_handler(user_leave_room_event_handler)
user_joined_event.add_handler(user_joined_event_handler)
update_queue_event.add_handler(update_queue_event_handler)