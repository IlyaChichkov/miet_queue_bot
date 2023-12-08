from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from message_forms.ban_menu_form import get_ban_menu_form
from routing.router import handle_message
from states.room_state import RoomVisiterState


router = Router()

@router.callback_query(F.data == 'show#ban_menu')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    form, kb = await get_ban_menu_form(callback.from_user.id)
    await handle_message(callback.from_user.id, form, reply_markup=kb)


@router.callback_query(F.data == 'action#ban_user')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    form, kb = await get_ban_menu_form(callback.from_user.id)
    await handle_message(callback.from_user.id, form, reply_markup=kb)


@router.callback_query(F.data == 'action#remove_ban')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    form, kb = await get_ban_menu_form(callback.from_user.id)
    await handle_message(callback.from_user.id, form, reply_markup=kb)

