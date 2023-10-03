from aiogram import Router, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot_logging import log_user_info
from firebase import db_create_room, user_join_room, enter_queue
import re

from handlers.room_welcome import welcome_room_state
from states.room import RoomVisiterState

router = Router()

class WelcomeState(StatesGroup):
    WELCOME_SCREEN = State()
    CREATE_ROOM_SCREEN = State()
    JOIN_ROOM_SCREEN = State()

def create_room_input_reg(input_text):
    pattern = re.compile(r"[A-Za-z0-9]+#+", re.IGNORECASE)
    return pattern.match(input_text)


@router.message(F.text.lower() == "создать комнату" or Command("create"), WelcomeState.WELCOME_SCREEN)
async def create_room_state(message: types.Message, state: FSMContext):
    await message.answer("Введите для создания комнаты (пароль#имя_комнаты):")
    await state.set_state(WelcomeState.CREATE_ROOM_SCREEN)


@router.message(F.text.lower() == "присоединиться к комнате", WelcomeState.WELCOME_SCREEN)
async def join_room_state(message: types.Message, state: FSMContext):
    await message.answer("Введите для присоединения к комнате:")
    await state.set_state(WelcomeState.JOIN_ROOM_SCREEN)


@router.message(F.text, WelcomeState.CREATE_ROOM_SCREEN)
async def create_room(message: types.Message, state: FSMContext):
    if create_room_input_reg(message.text):
        args = message.text.split('#')
        result = await db_create_room(message.from_user.id, args[0], args[1])
        is_room_created = 'room' in result
        log_user_info(message.from_user.id, f'Try create room, name: {args[1]}, password: {args[0]}, result: {is_room_created}')
        if is_room_created:
            await message.answer(f"Вы создали комнату {args[1]}.")
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            await message.answer(f"Не получилось создать комнату. Ошибка: {result['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    else:
        await message.answer("Не получилось создать комнату.")
        await state.set_state(WelcomeState.WELCOME_SCREEN)


@router.message(F.text, WelcomeState.JOIN_ROOM_SCREEN)
async def join_room(message: types.Message, state: FSMContext):
    filter_join_code = re.findall(r"^[0-9]+$", message.text)

    check_user_code = len(filter_join_code) > 0 and len(filter_join_code[0]) == 4
    check_mod_code = len(message.text) == 7

    if check_user_code:
        joined_room = await user_join_room(message.from_user.id, message.text, 'user')
        room_name = joined_room['room']['name']
        if 'room' in joined_room:
            if 'queue_on_join' in joined_room['room'] and joined_room['room']['queue_on_join'] == True:
                await enter_queue(message.from_user.id)

            log_user_info(message.from_user.id, f'Joined room, name: {room_name} as user')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    elif check_mod_code:
        joined_room = await user_join_room(message.from_user.id, message.text, 'moderator')
        room_name = joined_room['room']['name']
        if 'room' in joined_room:
            log_user_info(message.from_user.id, f'Joined room, name: {room_name} as moderator')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    else:
        await message.answer("Неверный код подключения")
        await state.set_state(WelcomeState.WELCOME_SCREEN)