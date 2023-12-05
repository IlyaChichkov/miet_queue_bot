from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_conf.bot_logging import log_user_info
from firebase_manager.firebase import db_create_room, user_join_room, enter_queue, admin_join_room, try_enter_queue
import re

from handlers.main_screens import start_command
from handlers.room_welcome import welcome_room_state, welcome_room
from keyboards.welcome_keyboard import get_welcome_kb
from message_forms.welcome_form import get_favorites_form
from models.room import Room
from roles.special_roles import check_access_level, GlobalRoles
from routing.router import handle_message
from states.room_state import RoomVisiterState
from states.welcome_state import WelcomeState

router = Router()


@router.message(F.text.lower() == "избранное", WelcomeState.WELCOME_SCREEN)
async def show_favorites_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    message_form, kb = await get_favorites_form(user_id)
    await message.answer(message_form, reply_markup=kb)


@router.callback_query(F.data == "show#favorite", WelcomeState.WELCOME_SCREEN)
async def show_favorites_list(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    message_form, kb = await get_favorites_form(user_id)
    await handle_message(user_id, message_form, reply_markup=kb)


@router.callback_query(F.data.startswith("join_fav_room"), WelcomeState.WELCOME_SCREEN)
async def show_rooms_list(callback: types.CallbackQuery, state: FSMContext):
    room_id = callback.data.split('#')[1]
    room_list_to_role = {
        'users': 'user',
        'moderators': 'moderator',
        'admins': 'admin'
    }
    role = room_list_to_role[callback.data.split('#')[2]]
    user_id = callback.from_user.id

    from models.server_rooms import get_room
    room = await get_room(room_id)

    if role == 'user':
        joined_room = await user_join_room(user_id, room.users_join_code, 'user')

        if 'room' in joined_room:
            room: Room = joined_room['room']
            room_name = room.name
            if room.is_queue_on_join and room.is_queue_enabled:
                await try_enter_queue(user_id)

            log_user_info(user_id, f'Joined room, name: {room_name} as user')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room(callback.message, user_id)
        else:
            # If already connected to the room: move to room lobby
            if joined_room['error'] == 'Connected to other room':
                await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
                await welcome_room(callback.message, user_id)
            await callback.answer(f"Ошибка подключения к комнате. {joined_room['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
        return

    if role == 'moderator':
        joined_room = await user_join_room(user_id, room.moderators_join_code, 'moderator')

        if 'room' in joined_room:
            room: Room = joined_room['room']
            room_name = room.name

            log_user_info(user_id, f'Joined room, name: {room_name} as moderator')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room(callback.message, user_id)
        else:
            # If already connected to the room: move to room lobby
            if joined_room['error'] == 'Connected to other room':
                await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
                await welcome_room(callback.message, user_id)
            await callback.answer(f"Ошибка подключения к комнате. {joined_room['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
        return

    if role == 'admin':
        from models.server_users import get_user
        from models.user import User
        user: User = await get_user(user_id)
        if user.is_owner_of_room(room_id):
            joined_room = await admin_join_room(user.user_id, room_id)

            if 'room' in joined_room:
                room: Room = joined_room['room']
                room_name = room.name

                log_user_info(user.user_id, f'Joined room, name: {room_name} as admin')
                await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
                await welcome_room(callback.message, user_id)
        return


@router.message(F.text.lower() == "вернуться в главное меню")
async def create_room_state(message: types.Message, state: FSMContext):
    await start_command(message, state)


@router.message(F.text.lower() == "создать комнату", WelcomeState.WELCOME_SCREEN)
async def create_room_state(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Teacher)
    if not has_access:
        return
    await message.answer("Введите название комнаты:")
    await state.set_state(WelcomeState.CREATE_ROOM_SCREEN)


@router.message(F.text.lower() == "присоединиться к комнате", WelcomeState.WELCOME_SCREEN)
async def join_room_state(message: types.Message, state: FSMContext):
    await message.answer("Введите код присоединения к комнате:")
    await state.set_state(WelcomeState.JOIN_ROOM_SCREEN)


@router.message(F.text.lower() == "назад", WelcomeState.CREATE_ROOM_SCREEN)
async def create_room_cancel(message: types.Message, state: FSMContext):
    await state.set_state(WelcomeState.WELCOME_SCREEN)
    await start_command(message, state)


@router.message(F.text, WelcomeState.CREATE_ROOM_SCREEN)
async def create_room(message: types.Message, state: FSMContext):
    '''
    Создание комнаты
    '''
    result = await db_create_room(message.from_user.id, message.text)
    is_room_created = 'room' in result
    if is_room_created:
        log_user_info(message.from_user.id, f'Try create room, name: {message.text}')
        await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
        await welcome_room(message)
    else:
        await message.answer(f"Не получилось создать комнату. Ошибка: {result['error_text']}")
        await state.set_state(WelcomeState.WELCOME_SCREEN)
        await start_command(message, state)


@router.message(F.text, WelcomeState.JOIN_ROOM_SCREEN)
async def join_room(message: types.Message, state: FSMContext):
    '''
    Присоединение к комнате
    '''

    filter_join_code = re.findall(r"^[0-9]+$", message.text)

    check_user_code = len(filter_join_code) > 0 and len(filter_join_code[0]) == 4
    check_mod_code = len(message.text) == 7

    if check_user_code:
        joined_room = await user_join_room(message.from_user.id, message.text, 'user')

        if 'room' in joined_room:
            room: Room = joined_room['room']
            room_name = room.name
            if room.is_queue_on_join and room.is_queue_enabled:
                await try_enter_queue(message.from_user.id)

            log_user_info(message.from_user.id, f'Joined room, name: {room_name} as user')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            # If already connected to the room: move to room lobby
            if joined_room['error'] == 'Connected to other room':
                await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
                await welcome_room_state(message)
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    elif check_mod_code:
        joined_room = await user_join_room(message.from_user.id, message.text, 'moderator')

        if 'room' in joined_room:
            room: Room = joined_room['room']
            room_name = room.name

            log_user_info(message.from_user.id, f'Joined room, name: {room_name} as moderator')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room_state(message)
        else:
            # If already connected to the room: move to room lobby
            if joined_room['error'] == 'Connected to other room':
                await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
                await welcome_room_state(message)
            await message.answer(f"Ошибка подключения к комнате. {joined_room['error_text']}")
            await state.set_state(WelcomeState.WELCOME_SCREEN)
    else:
        keyboard = await get_welcome_kb(message.from_user.id)
        await message.answer("Неверный код подключения.", reply_markup=keyboard)
        await state.set_state(WelcomeState.WELCOME_SCREEN)