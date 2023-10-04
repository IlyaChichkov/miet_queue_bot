from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_logging import log_user_info
from firebase import db_get_user_room, delete_room, leave_room, enter_queue, exit_queue
from handlers.main_screens import start_command
from handlers.queue_screen import queue_list_state, queue_pop_call
from handlers.room_welcome import welcome_room_state
from message_forms.room_forms import get_welcome_message
from roles.check_user_role import IsModerator, IsAdmin, IsUser
from states.room import RoomVisiterState

router = Router()


@router.message(IsAdmin(), F.text.lower() == "принять первого в очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "принять первого в очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await queue_pop_call(message, state)


@router.message(IsAdmin(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.message(IsAdmin(), F.text.lower() == "удалить комнату", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    log_user_info(message.from_user.id, f'Deleted room.')
    if await delete_room(message.from_user.id):
        await start_command(message, state)


@router.message(F.text.lower() == "выйти", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    if await leave_room(message.from_user.id):
        await start_command(message, state)


@router.message(IsUser(), F.text.lower() == "занять место", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    place = await enter_queue(message.from_user.id)
    await message.answer(f"Вы заняли место в очереди: #️⃣{place}")
    await welcome_room_state(message)


@router.message(IsUser(), F.text.lower() == "выйти из очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    if await exit_queue(message.from_user.id):
        await message.answer(f"Вы покинули очередь")
        await welcome_room_state(message)
    else:
        await message.answer(f"Вы уже не состоите в очереди") # TODO: Add error text
        await welcome_room_state(message)