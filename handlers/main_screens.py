import logging

from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, InputMediaPhoto, InputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from handlers.room_welcome import welcome_room
from message_forms.welcome_form import get_welcome_form
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.role_cache import users_role_cache
from routing.router import handle_message, handle_message_image, set_user_new_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState
from states.welcome_state import WelcomeState

router = Router()


@router.message(StateFilter(None))
async def any_text(message: Message, state: FSMContext):
    await message.answer(f"Возобновление сессии...")
    await start_command(message, state)


@router.callback_query(F.data == 'show#main_menu')
async def show_main_menu(message: Message, state: FSMContext):
    await start_command(message, state)


@router.message(Command("role"))
async def state_command(message: Message, state: FSMContext):
    await message.answer(f"Role cache: {users_role_cache}")


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
async def start_command_handler(message: types.Message, state: FSMContext):
    await set_user_new_message(message.from_user.id)
    await start_command(message, state)


async def start_command(message: types.Message, state: FSMContext):
    '''
    Создание пользователя,
    Подключение к комнате, если пользователь находится в ней,
    Отображение меню
    '''

    username = message.from_user.username
    if username is None or username == '':
        return
    user: User = await get_user(message.from_user.id, True)
    room: Room = await get_room(user.room)
    if room:
        await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
        await welcome_room(message.from_user.id)
        return

    await state.set_state(WelcomeState.WELCOME_SCREEN)

    await user.set_route(UserRoutes.MainMenu)

    logging.info(f'MAIN SCREEN | USER_{user.user_id} | {message.from_user.username}')
    form_message, form_kb = await get_welcome_form(message.from_user.first_name, message.from_user.id)
    await handle_message(user.user_id, form_message, reply_markup=form_kb)
