import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from firebase_manager.firebase import generate_random_queue
from handlers.queue_screen import queue_list_state, delete_cache_messages
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin, IsModerator
from keyboards.queue_settings_keyboard import get_queue_settings_kb, get_remove_user_kb
from routing.router import handle_message, send_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState
from bot_conf.bot import bot

router = Router()


@router.callback_query(F.data== "action#random_queue")
async def queue_generate_random(callback: types.CallbackQuery, state: FSMContext):
    '''
    Генерация случайной очереди из пользователей
    '''
    import random
    user: User = await get_user(callback.from_user.id)
    room: Room = await get_room(user.room)
    users_list = room.users[:]
    random.shuffle(users_list)
    message_text = await generate_random_queue(room, users_list)

    builder = InlineKeyboardBuilder()

    builder.row(types.InlineKeyboardButton(
        text="Назад",
        callback_data='show#queue_settings'
    ))

    kb =  builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    logging.info(f'Random queue was generated by USER_{user.user_id}\nQueue List:\n{message_text}')
    await handle_message(callback.from_user.id, message_text, reply_markup=kb)


@router.callback_query(F.data == "show#queue_settings")
async def queue_settings(callback: types.CallbackQuery, state: FSMContext):
    await delete_cache_messages(callback.from_user.id)
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
    kb = await get_queue_settings_kb()
    await handle_message(callback.from_user.id, "Настройки очереди:", reply_markup=kb)

    user: User = await get_user(callback.from_user.id)
    await user.set_route(UserRoutes.QueueSettings)


@router.callback_query(F.data == "action#remove_from_queue", RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
async def queue_remove_state(callback: types.CallbackQuery, state: FSMContext):
    '''
    Подготовка к вводу ID пользователя для удаления из очереди
    '''
    kb = await get_remove_user_kb(callback.from_user.id, current_page=1)
    await handle_message(callback.from_user.id, "Удаление из очереди\nВыберите пользователя:", reply_markup=kb)


@router.callback_query(F.data.startswith("action#remove_from_queue#list_"), RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
async def queue_remove_state(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_remove_user_kb(callback.from_user.id, current_page=int(callback.data.replace('action#remove_from_queue#list_', '')))
    await handle_message(callback.from_user.id, "Удаление из очереди\nВыберите пользователя:", reply_markup=kb)


@router.callback_query(F.data.startswith("queue_remove"))
async def queue_remove_user(callback: CallbackQuery, state: FSMContext):
    '''
    Удаления пользователя из очереди
    '''
    queue_remove_user_id = callback.data.split('_')[2]
    init_user_id = callback.data.split('_')[3]
    init_user: User = await get_user(str(init_user_id))
    removed_user: User = await get_user(str(queue_remove_user_id))
    room: Room = await get_room(init_user.room)
    await room.queue_remove(queue_remove_user_id)

    logging.info(f'USER_{removed_user.user_id} was removed from queue by USER_{init_user.user_id}')
    try:
        await send_message(queue_remove_user_id, f'<b>{init_user.name}</b> убрал вас из очереди.')
    except Exception as ex:
        logging.info(f"Tried to notify USER_{queue_remove_user_id} (user) about being removed from queue, but got error: {ex}")

    try:
        await send_message(init_user_id, f'Вы убрали пользователя <b>{removed_user.name}</b> из очереди.')
    except Exception as ex:
        logging.info(f"Tried to notify USER_{init_user_id} about successful user remove from queue, but got error: {ex}")
    await queue_settings(callback, state)


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
@router.message(F.text.lower() == "назад", RoomVisiterState.QUEUE_SETTINGS_REMOVE)
async def exit_queue_settings(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)
