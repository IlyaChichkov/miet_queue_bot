from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_conf.bot_logging import log_user_info
from firebase_manager.firebase import change_user_name, get_user_name
from handlers.main_screens import start_command
from handlers.room_actions import RoomVisiterState
from keyboards.profile_settings_kb import get_settings_kb
from models.note import export_study_notes_by_user
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin, IsModerator

router = Router()


@router.message(F.text.lower() == "профиль")
async def profile_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.message(IsAdmin(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
@router.message(IsModerator(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_notes(message: types.Message, state: FSMContext):
    '''
    Отображение заметок преподавателя
    '''
    user: User = await get_user(message.from_user.id)
    room: Room = await get_room(user.room)

    message_data = export_study_notes_by_user(room.study_notes, user.user_id)
    await message.answer(message_data, parse_mode="HTML")
    await profile_settings_state(message, state)


@router.message(F.text.lower() == "изменить имя", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_change_name(message: types.Message, state: FSMContext):
    '''
    Переход в состояние изменения пользовательского имени
    '''
    await state.set_state(RoomVisiterState.CHANGE_PROFILE_NAME)
    await message.answer(f"✏️ Введите новое имя (Имя Фамилия №ПК):", reply_markup=types.ReplyKeyboardRemove())


@router.message(F.text.lower() == "назад", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_back(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await start_command(message, state)


@router.message(F.text.lower() == "назад", RoomVisiterState.CHANGE_PROFILE_NAME)
async def profile_back(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.message(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_settings(message: types.Message):
    kb = await get_settings_kb(message.from_user.id)
    user_name = await get_user_name(message.from_user.id)
    await message.answer(f"⚙️ Настройки профиля «<b>{user_name}</b>»", parse_mode="HTML", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_PROFILE_NAME)
async def change_user_name_state(message: types.Message, state: FSMContext):
    '''
    Подтверждение изменения имени
    '''
    await change_user_name(message.from_user.id, message.text)
    log_user_info(message.from_user.id, f'Changed name to: {message.text}')
    await message.answer(f"✅ Имя успешно изменено на {message.text}")
    await profile_settings_state(message, state)