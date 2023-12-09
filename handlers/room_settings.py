from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from pathlib import Path

from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_conf.bot_logging import log_user_info
from firebase_manager.firebase import change_room_auto_queue, get_user_room_key, change_room_name, delete_room
from handlers.main_screens import start_command
from handlers.room_actions import RoomVisiterState
from handlers.room_welcome import welcome_room_state
from keyboards.room_settings_kb import get_settings_kb
from models.note import export_study_notes
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from datetime import date

from routing.router import handle_message
from routing.user_routes import UserRoutes

router = Router()


@router.callback_query(F.data == "show#room_settings")
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)
    user: User = await get_user(callback.from_user.id)
    await user.set_route(UserRoutes.RoomSettings)
    await room_settings(callback)


@router.message(F.text.startswith("Автоочередь"), RoomVisiterState.ROOM_SETTINGS_SCREEN)
@router.callback_query(F.data == "action#room_autoqueue_toggle", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_toggle_autoqueue(message: types.Message, state: FSMContext):
    autoqueue = await change_room_auto_queue(await get_user_room_key(message.from_user.id))
    kb = await get_settings_kb(message.from_user.id)
    msg = {
        True: 'включена',
        False: 'выключена'
    }
    await message.answer(f"Автоочередь {msg[autoqueue]}", reply_markup=kb)
    await room_settings(message)


@router.message(F.text.lower() == "🗑️ удалить комнату", RoomVisiterState.ROOM_SETTINGS_SCREEN)
@router.callback_query(F.data == "action#delete_room", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_delete_state(message: types.Message, state: FSMContext):
    log_user_info(message.from_user.id, f'Deleted room.')
    if await delete_room(message.from_user.id):
        await start_command(message, state)


@router.message(F.text.lower() == "экспорт заметок", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    user: User = await get_user(message.from_user.id)
    room: Room = await get_room(user.room)
    today = date.today()
    csv_data = export_study_notes(room.study_notes, 'json')

    Path("./temp_files").mkdir(parents=True, exist_ok=True)
    file_path = './temp_files/study_note_' + str(message.message_id) + '.json'
    with open(file_path, 'w+', encoding="utf-8") as file:
        file.write(csv_data)

    send_file = FSInputFile(file_path, f'Заметки. Комната {room.name} {today}.json')
    await message.answer_document(send_file)

    Path(file_path).unlink()
    await room_settings(message)

@router.callback_query(F.data == "action#export_notes", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(callback: types.CallbackQuery, state: FSMContext):
    user: User = await get_user(callback.from_user.id)
    room: Room = await get_room(user.room)
    today = date.today()
    csv_data = export_study_notes(room.study_notes, 'json')

    Path("./temp_files").mkdir(parents=True, exist_ok=True)
    file_path = './temp_files/study_note_' + str(callback.id) + '.json'
    with open(file_path, 'w+', encoding="utf-8") as file:
        file.write(csv_data)

    send_file = FSInputFile(file_path, f'Заметки. Комната {room.name} {today}.json')
    await callback.message.answer_document(send_file)

    Path(file_path).unlink()
    await room_settings(callback)


@router.message(F.text.lower() == "изменить название", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.CHANGE_ROOM_NAME)
    await message.answer("✏️ Введите новое название комнаты")


@router.callback_query(F.data == "action#change_room_name", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.CHANGE_ROOM_NAME)

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'action#cancel_room_change_name'
        )
    )

    kb = builder.as_markup(resize_keyboard=True)

    await handle_message(callback.from_user.id, "✏️ Введите новое название комнаты", kb)


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_SETTINGS_SCREEN)
@router.callback_query(F.data == "show#room_menu", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.message(RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings(message: types.Message):
    user_id = message.from_user.id
    log_user_info(user_id, f'Entered room settings screen')
    kb = await get_settings_kb(user_id)
    await handle_message(user_id, "⚙️ Настройка комнаты:", reply_markup=kb)


@router.callback_query(F.data == 'action#cancel_room_change_name', RoomVisiterState.CHANGE_ROOM_NAME)
async def cancel_room_change_name(message: types.Message, state: FSMContext):
    print('cancel change')
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)
    await room_settings(message)


@router.message(RoomVisiterState.CHANGE_ROOM_NAME)
async def change_room_name_state(message: types.Message, state: FSMContext):
    await change_room_name(message.from_user.id, message.text)
    await message.answer(f"✅ Название комнаты успешно изменено на {message.text}")
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)
    await room_settings(message)