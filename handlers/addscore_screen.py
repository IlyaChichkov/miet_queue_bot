import datetime

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext

from firebase_manager.firebase import get_user_name
from handlers.queue_screen import assigned_screen
from keyboards.assign_keyboard import get_add_score_kb
from models.room import Room
from models.server_rooms import get_room
from models.server_score import usersScore
from models.server_users import get_user
from models.user import User
from states.room_state import RoomVisiterState

router = Router()


@router.message(F.text.lower() == "💯 поставить баллы", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def assigned_add_score(message: types.Message, state: FSMContext):
    '''
    Начало выставления баллов
    '''
    user: User = await get_user(message.from_user.id)
    pupil_name = await get_user_name(user.assigned_user_id)
    await state.set_state(RoomVisiterState.ROOM_SCORE_SCREEN)
    form_message = f'Выставить баллы «<b>{pupil_name}</b>»'
    form_kb = get_add_score_kb(user.user_id, user.assigned_user_id)
    await message.answer(form_message, reply_markup=form_kb, parse_mode="HTML")


@router.callback_query(F.data == "addscore#back", RoomVisiterState.ROOM_SCORE_SCREEN)
async def exit_add_score(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    user: User = await get_user(callback.from_user.id)
    await assigned_screen(callback.message, user.assigned_user_id)


@router.callback_query(F.data.startswith("addscore"), RoomVisiterState.ROOM_SCORE_SCREEN)
async def add_score(callback: types.CallbackQuery, state: FSMContext):
    '''
    Выставления баллов
    '''
    callback_data = callback.data.split('#')[1].split('_')
    print(callback_data)
    tutor_id = int(callback_data[0])
    pupil_id = int(callback_data[1])
    score = int(callback_data[2])
    user: User = await get_user(tutor_id)
    room: Room = await get_room(user.room)

    await usersScore.add_score(pupil_id, tutor_id, score, room.name,
                               datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    await callback.message.answer(f"Добавил баллы ({score}) пользователю")
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    await assigned_screen(callback.message, pupil_id)


@router.message(F.text.lower() == 'назад', RoomVisiterState.ROOM_SCORE_SCREEN)
async def add_score(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    user: User = await get_user(message.from_user.id)
    await assigned_screen(message, user.assigned_user_id)


@router.message(RoomVisiterState.ROOM_SCORE_SCREEN)
async def add_score(message: types.Message, state: FSMContext):
    print(message.text)
    if message.text.isdigit():
        print('it is')
