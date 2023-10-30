import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.queue_screen import queue_list_state, delete_cache_messages
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin, IsModerator
from keyboards.queue_settings_keyboard import get_queue_settings_kb, get_remove_user_kb
from states.room import RoomVisiterState
from bot import bot

router = Router()

@router.message(IsAdmin(), F.text.lower() == "настройки очереди")
@router.message(IsModerator(), F.text.lower() == "настройки очереди")
async def queue_settings(message: types.Message, state: FSMContext):
    await delete_cache_messages(message.from_user.id)
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
    kb = await get_queue_settings_kb()
    await message.answer("Выберите действие:", reply_markup=kb, parse_mode="HTML")


@router.message(F.text.lower() == "удалить из очереди", RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
async def queue_remove_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.QUEUE_SETTINGS_REMOVE)
    await queue_remove(message, state)


@router.callback_query(F.data.startswith("queue_remove_"), RoomVisiterState.QUEUE_SETTINGS_REMOVE)
async def queue_remove_user(callback: CallbackQuery, state: FSMContext):
    queue_remove_user_id = callback.data.split('_')[2]
    init_user_id = callback.data.split('_')[3]
    init_user: User = await get_user(str(init_user_id))
    room: Room = await get_room(init_user.room)
    await room.queue_remove(queue_remove_user_id)

    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Вернуться в меню"),
    )
    kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    await bot.send_message(queue_remove_user_id, f'{init_user.name} убрал вас из очереди.',  reply_markup=kb, parse_mode="HTML")


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_QUEUE_SETTINGS_SCREEN)
@router.message(F.text.lower() == "назад", RoomVisiterState.QUEUE_SETTINGS_REMOVE)
async def exit_queue_settings(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.message(RoomVisiterState.QUEUE_SETTINGS_REMOVE)
async def queue_remove(message: types.Message, state: FSMContext):
    kb = await get_remove_user_kb(message.from_user.id)
    await message.answer("Выберите пользователя:", reply_markup=kb)