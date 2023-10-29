from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_logging import log_user_info
from firebase import change_user_name, get_user_name, db_get_user_room, get_user_role_at_room
from handlers.main_screens import start_command
from handlers.room_actions import RoomVisiterState
from handlers.room_welcome import welcome_room_state
from models.note import export_study_notes, export_study_notes_by_user
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin, IsModerator
from roles.user_roles_enum import UserRoles

router = Router()

async def get_settings_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Изменить имя")
    )

    role = await get_user_role_at_room(user_id)
    if role and role is not UserRoles.User:
        builder.row(types.KeyboardButton(text="Мои заметки"))

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    return builder.as_markup(resize_keyboard=True)


@router.message(F.text.lower() == "профиль")
async def profile_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.message(IsAdmin(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
@router.message(IsModerator(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_notes(message: types.Message, state: FSMContext):
    user: User = await get_user(message.from_user.id)
    room: Room = await get_room(user.room)

    message_data = export_study_notes_by_user(room.study_notes, user.user_id)
    await message.answer(message_data, parse_mode="HTML")
    await profile_settings_state(message, state)


@router.message(F.text.lower() == "изменить имя", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_change_name(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.CHANGE_PROFILE_NAME)
    user_name = await get_user_name(message.from_user.id)
    await message.answer(f"✏️ Текущее имя: {user_name}\nВведите новое имя (Имя Фамилия №ПК):")


@router.message(F.text.lower() == "назад", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_back(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await start_command(message, state)


@router.message(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_settings(message: types.Message):
    kb = await get_settings_kb(message.from_user.id)
    user_name = await get_user_name(message.from_user.id)
    await message.answer(f"⚙️ Настройки профиля «<b>{user_name}</b>»", parse_mode="HTML", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_PROFILE_NAME)
async def change_user_name_state(message: types.Message, state: FSMContext):
    await change_user_name(message.from_user.id, message.text)
    log_user_info(message.from_user.id, f'Changed name to: {message.text}')
    await message.answer(f"✅ Имя успешно изменено на {message.text}")
    await profile_settings_state(message, state)