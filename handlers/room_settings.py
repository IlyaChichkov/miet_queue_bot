from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from firebase import change_room_auto_queue, get_user_room, get_room_option, change_room_name
from handlers.room_actions import RoomVisiterState
from handlers.room_welcome import welcome_room_state

router = Router()

async def get_settings_kb(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text=f"Автоочередь ({await get_room_option(user_id, 'queue_on_join')})"),
        types.KeyboardButton(text="Изменить название")
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
    await change_room_auto_queue(await get_user_room(message.from_user.id))
    kb = await get_settings_kb(message.from_user.id)
    await message.answer("Автоочередь - вкл/выкл", reply_markup=kb)


@router.message(F.text.lower() == "изменить название", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.CHANGE_ROOM_NAME)
    await message.answer("Введите новое название комнаты")


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.message(RoomVisiterState.ROOM_SETTINGS_SCREEN)
async def room_settings(message: types.Message):
    kb = await get_settings_kb(message.from_user.id)
    await message.answer("Настройка комнаты:", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_ROOM_NAME)
async def change_room_name_state(message: types.Message, state: FSMContext):
    await change_room_name(message.from_user.id, message.text)
    await message.answer(f"Название комнаты успешно изменено на {message.text}")
    await state.set_state(RoomVisiterState.ROOM_SETTINGS_SCREEN)