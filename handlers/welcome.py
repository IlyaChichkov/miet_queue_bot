from aiogram import Router, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
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
        print(result)
        if 'room' in result:
            await message.answer(f"Вы создали комнату {args[1]}.")
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            await message.answer(f"Не получилось создать комнату. {result['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    else:
        print('Wrong create room pattern')
        await message.answer("Введите для создания комнаты (пароль#имя_комнаты):")


@router.message(F.text, WelcomeState.JOIN_ROOM_SCREEN)
async def join_room(message: types.Message, state: FSMContext):
    filter_join_code = re.findall(r"^[0-9]+$", message.text)

    print('2)', message.text)
    print('1)', len(filter_join_code) > 0 and len(filter_join_code[0]) == 4)
    print('2)', len(message.text) == 7)

    if len(filter_join_code) > 0 and len(filter_join_code[0]) == 4:
        joined_room = await user_join_room(message.from_user.id, message.text, 'user')
        print(joined_room)
        if 'room' in joined_room:
            print('joined_room', joined_room)
            print('room', joined_room['room'])
            if 'queue_on_join' in joined_room['room'] and joined_room['room']['queue_on_join'] == True:
                await enter_queue(message.from_user.id)

            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
            # await message.answer(f"Студент {message.from_user.username}\nДобро пожаловать в комнату {joined_room['room']['name']}")
        else:
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    elif len(message.text) == 7:
        joined_room = await user_join_room(message.from_user.id, message.text, 'moderator')
        print(joined_room)
        if 'room' in joined_room:
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
            # await message.answer(f"Модератор {message.from_user.username}\nДобро пожаловать в комнату {joined_room['room']['name']}")
        else:
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    else:
        await message.answer("Неверный код подключения")
        await state.set_state(WelcomeState.WELCOME_SCREEN)