from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_logging import log_user_info
from firebase import change_room_auto_queue, get_user_room_key, change_room_name, is_autoqueue_enabled, delete_room
from handlers.main_screens import start_command
from handlers.room_actions import RoomVisiterState
from handlers.room_welcome import welcome_room_state
from roles.check_user_role import IsAdmin

router = Router()


async def get_settings_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text=f"Автоочередь ({await is_autoqueue_enabled(user_id)})"),
        types.KeyboardButton(text="Изменить название")
    )

    builder.row(
        types.KeyboardButton(text='🗑️ Удалить комнату')
    )

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    return builder.as_markup(resize_keyboard=True)

@router.message(F.text.lower() == "настройки комнаты", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)
    await room_settings(message)


@router.message(F.text.startswith("Автоочередь"), RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await change_room_auto_queue(await get_user_room_key(message.from_user.id))
    kb = await get_settings_kb(message.from_user.id)
    await message.answer("Автоочередь - вкл/выкл", reply_markup=kb)


@router.message(IsAdmin(), F.text.lower() == "🗑️ удалить комнату", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_delete_state(message: types.Message, state: FSMContext):
    log_user_info(message.from_user.id, f'Deleted room.')
    if await delete_room(message.from_user.id):
        await start_command(message, state)


@router.message(F.text.lower() == "изменить название", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.CHANGE_ROOM_NAME)
    await message.answer("✏️ Введите новое название комнаты")


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.message(RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings(message: types.Message):
    user_id = message.from_user.id
    log_user_info(user_id, f'Entered room settings screen')
    kb = await get_settings_kb(user_id)
    await message.answer("⚙️ Настройка комнаты:", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_ROOM_NAME)
async def change_room_name_state(message: types.Message, state: FSMContext):
    await change_room_name(message.from_user.id, message.text)
    await message.answer(f"✅ Название комнаты успешно изменено на {message.text}")
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)