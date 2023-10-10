from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_logging import log_user_info
from firebase import user_join_room, admin_join_room
from handlers.room_welcome import welcome_room_state, welcome_room
from message_forms.welcome_form import get_owner_rooms_form
from models.room import Room
from models.server_users import get_user
from models.user import User
from roles.special_roles import check_access_level, GlobalRoles
from states.room import RoomVisiterState
from states.welcome import WelcomeState

router = Router()


@router.message(F.text.lower() == "мои комнаты", WelcomeState.WELCOME_SCREEN)
async def show_rooms_list(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Teacher)
    if not has_access:
        return

    form_message, form_kb = await get_owner_rooms_form(message.from_user.id)
    await message.answer(form_message, reply_markup=form_kb)


@router.callback_query(F.data.startswith("connect_room"), WelcomeState.WELCOME_SCREEN)
async def show_rooms_list(callback: types.CallbackQuery, state: FSMContext):
    room_id = callback.data.split('#')[1]
    user_id = callback.from_user.id
    user: User = await get_user(user_id)
    if user.is_owner_of_room(room_id):
        joined_room = await admin_join_room(user.user_id, room_id)

        if 'room' in joined_room:
            room: Room = joined_room['room']
            room_name = room.name

            log_user_info(user.user_id, f'Joined room, name: {room_name} as admin')
            await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
            await welcome_room(callback.message, user_id)