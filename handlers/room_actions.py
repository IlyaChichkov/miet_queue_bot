from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from events.room_announcement_handler import send_public_announcement
from firebase_manager.firebase import leave_room, exit_queue, skip_queue_place, toggle_favorite_room
from handlers.main_screens import start_command
from handlers.queue_screen import queue_list_state, queue_pop_handler
from handlers.room_welcome import welcome_room_state
from message_forms.room_forms import get_users_list_form, get_join_queue_form, get_announcement_form
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsModerator, IsAdmin, IsUser
from routing.router import handle_message, send_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState

router = Router()


@router.message(F.text.lower() == "назад", RoomVisiterState.MAKE_ANNOUNCEMENT_SCREEN)
async def exit_announcement(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.callback_query(F.data == "action#favorite", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def switch_favorite_state_call(callback: types.CallbackQuery, state: FSMContext):
    added_to_favorites = await toggle_favorite_room(callback.from_user.id)
    if added_to_favorites:
        await callback.answer(f"Комната добавлена в избранное")
    else:
        await callback.answer(f"Комната убрана из избранного")

    await welcome_room_state(callback)


@router.callback_query(F.data == "action#make_announcement", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def make_announcement(callback: types.CallbackQuery, state: FSMContext):
    '''
    Создание уведомления для всех участников комнаты
    '''
    await state.set_state(RoomVisiterState.MAKE_ANNOUNCEMENT_SCREEN)
    form_message, form_kb = await get_announcement_form(callback.from_user.id)
    user: User = await get_user(callback.from_user.id)
    await user.set_route(UserRoutes.MakeAnnouncement)
    await handle_message(callback.from_user.id, form_message, reply_markup=form_kb)


@router.message(RoomVisiterState.MAKE_ANNOUNCEMENT_SCREEN)
async def send_announcement(message: types.Message, state: FSMContext):
    '''
    Отправка уведомления
    '''
    await send_public_announcement(message.from_user.id, message.text)
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.callback_query(F.data == "show#users_list", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_users_list_call(callback: types.CallbackQuery, state: FSMContext):
    form_message, form_kb = await get_users_list_form(callback.from_user.id)
    user: User = await get_user(callback.from_user.id)
    await user.set_route(UserRoutes.RoomUsersList)
    await handle_message(callback.from_user.id, form_message, form_kb)


@router.callback_query(F.data == "action#queue_pop")
async def room_get_queue_pop(callback: types.CallbackQuery, state: FSMContext):
    await queue_pop_handler(callback, state)


@router.message(IsAdmin(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_queue_show(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.callback_query(F.data == "show#queue_list")
async def room_queue_show(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(callback)


@router.message(F.text.lower() == "выйти", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_exit_state(message: types.Message, state: FSMContext):
    await leave_room(message.from_user.id)
    await state.set_state(None)
    await start_command(message, state)


@router.callback_query(F.data == "action#exit_room", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_exit_state_call(callback: types.CallbackQuery, state: FSMContext):
    await leave_room(callback.from_user.id)
    await state.set_state(None)
    await start_command(callback, state)


@router.callback_query(F.data == "action#enter_queue")
async def room_queue_push(callback: types.CallbackQuery, state: FSMContext):
    message_text = await get_join_queue_form(callback.from_user.id)
    print(message_text)
    # TODO: Got error here
    # aiogram.exceptions.TelegramBadRequest: Telegram server says - Bad Request: query is too old and response timeout expired or query ID is invalid
    if 'place' in message_text:
        await callback.answer(f"Вы на {message_text['place']} месте в очереди")
    await welcome_room_state(callback)


@router.callback_query(F.data == "action#exit_queue")
async def room_queue_push(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if await exit_queue(user_id):
        await callback.answer(f"Вы покинули очередь")
        await welcome_room_state(callback)
    else:
        await callback.answer(f"Вы уже не состоите в очереди")  # TODO: Add error text
        await welcome_room_state(callback)


@router.callback_query(F.data == "action#skip_turn")
async def room_queue_push(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    skiped_user_name = await skip_queue_place(user_id)
    if skiped_user_name:
        await send_message(user_id, f"Вы пропустили вперед «<b>{skiped_user_name}</b>»")
