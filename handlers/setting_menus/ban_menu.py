from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from firebase_manager.firebase import leave_room_instance
from keyboards.ban_keyboard import get_ban_kb
from message_forms.ban_menu_form import get_ban_menu_form
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from routing.router import handle_message, send_message
from states.room_state import RoomVisiterState


router = Router()

@router.callback_query(F.data == 'show#ban_menu')
async def show_ban_menu(callback: types.CallbackQuery, state: FSMContext):
    form, kb = await get_ban_menu_form(callback.from_user.id)
    await handle_message(callback.from_user.id, form, reply_markup=kb)


@router.callback_query(F.data.startswith("action#initban_"))
async def ban_action_call(callback: types.CallbackQuery, state: FSMContext):
    print(callback.data)
    ban_status = callback.data.split('_')[1] == 'True'
    ban_user_id = callback.data.split('_')[2]
    init_user_id = callback.data.split('_')[3]
    ban_user: User = await get_user(ban_user_id)
    init_user: User = await get_user(init_user_id)
    room: Room = await get_room(init_user.room)
    if ban_status:
        success = await room.ban_user(init_user_id, ban_user_id)
        if success:
            user_removed = await leave_room_instance(ban_user, room)
            await send_message(callback.from_user.id, f'Вы забанили пользователя {ban_user.name}.{" Пользователь убран из комнаты" if user_removed else ""}')
            if user_removed:
                builder = InlineKeyboardBuilder()

                builder.row(
                    types.InlineKeyboardButton(
                        text="Главное меню",
                        callback_data='show#main_menu'
                    )
                )
                kb = builder.as_markup(resize_keyboard=True)
                await handle_message(ban_user_id, f'Вас {init_user.name} лишил доступа к комнате {room.name}', kb)
            else:
                await send_message(ban_user_id, f'Вас {init_user.name} лишил доступа к комнате {room.name}')

    else:
        success = await room.remove_ban(init_user_id, ban_user_id)
        if success:
            await send_message(callback.from_user.id, f'Вы убрали бан пользователю {ban_user.name}')
            await send_message(ban_user_id, f'{init_user.name} восстановил вам доступ к комнате {room.name}')

    print(room.banned)
    await show_ban_menu(callback, state)


@router.callback_query(F.data.startswith("action#ban_user#list_"))
async def action_ban_user_list_call(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_ban_kb(callback.from_user.id, True, current_page=int(callback.data.replace('action#ban_user#list_', '')))
    await handle_message(callback.from_user.id, 'Добавление в черный список:', reply_markup=kb)


@router.callback_query(F.data.startswith("action#remove_ban#list_"))
async def action_remove_ban_list_call(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_ban_kb(callback.from_user.id, False, current_page=int(callback.data.replace('action#remove_ban#list_', '')))
    await handle_message(callback.from_user.id, 'Убрать из черного списка:', reply_markup=kb)


@router.callback_query(F.data == 'action#ban_user')
async def action_ban_user_call(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_ban_kb(callback.from_user.id, True, 1)
    await handle_message(callback.from_user.id, 'Добавление в черный список:', reply_markup=kb)


@router.callback_query(F.data == 'action#remove_ban')
async def action_remove_ban_call(callback: types.CallbackQuery, state: FSMContext):
    kb = await get_ban_kb(callback.from_user.id, False, 1)
    await handle_message(callback.from_user.id, 'Убрать из черного списка:', reply_markup=kb)

