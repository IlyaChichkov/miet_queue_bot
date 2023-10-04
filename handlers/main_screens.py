from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove, URLInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from firebase import db_get_user_room
from handlers.room_welcome import welcome_room
from roles.check_user_role import IsAdmin
from roles.role_cache import users_role_cache
from states.room import RoomVisiterState
from states.welcome import WelcomeState

router = Router()


@router.message(StateFilter(None))
async def any_text(message: Message, state: FSMContext):
    await start_command(message, state)


@router.message(Command("state"))
async def state_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await message.answer(f"State: {current_state}")


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == "отмена")
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    '''
    Создание пользователя,
    Подключение к комнате, если пользователь находится в ней,
    Отображение меню
    '''
    room = await db_get_user_room(message.from_user.id)
    print(room)
    if 'room' in room:
        await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
        await welcome_room(message)
        return

    kb = [
        [
            types.KeyboardButton(text="Создать комнату"),
            types.KeyboardButton(text="Присоединиться к комнате")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder=""
    )
    start_image = URLInputFile(
        "https://i.postimg.cc/MpCGsd4H/1.png"
    )
    await message.answer_photo(start_image, "Добро пожаловать в QueueBot! Пожалуйста выберите действие:", reply_markup=keyboard)
    await state.set_state(WelcomeState.WELCOME_SCREEN)
