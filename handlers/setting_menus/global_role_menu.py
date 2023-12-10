from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from events.global_role_event import update_user_global_role_event
from message_forms.global_role_menu_form import get_global_role_settings_form, get_global_role_help_form
from models.server_admin import set_global_role, delete_global_role
from roles.special_roles import check_access_level, GlobalRoles
from routing.router import handle_message, send_message
from states.room_state import RoomVisiterState

router = Router()

@router.callback_query(F.data == 'show#global_role_settings')
async def show_global_role_settings_call(callback: types.CallbackQuery, state: FSMContext):
    await show_global_role_settings(callback.from_user.id, state)


async def show_global_role_settings(user_id, state: FSMContext):
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if not has_access:
        return
    await state.set_state(RoomVisiterState.ADMIN_ROLES_SCREEN)
    form, kb = await get_global_role_settings_form(user_id)
    await handle_message(user_id, form, reply_markup=kb)


@router.message(RoomVisiterState.ADMIN_ROLES_SCREEN)
async def show_global_role_edit(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if not has_access:
        return

    if message.text.startswith('add'):
        add_user_id = message.text.split(' ')[1]
        role = int(message.text.split(' ')[2])
        await set_global_role(add_user_id, role)
        await send_message(user_id, f'Добавил пользователю {add_user_id} роль {GlobalRoles(role)}')
        await update_user_global_role_event.fire(add_user_id, GlobalRoles(role))

    if message.text.startswith('rm'):
        rm_user_id = message.text.split(' ')[1]
        await delete_global_role(rm_user_id)
        await send_message(user_id, f'Убрал пользователю {rm_user_id} роль')
        await update_user_global_role_event.fire(rm_user_id, None)

    if message.text.startswith('help'):
        msg = await get_global_role_help_form(user_id)
        await send_message(user_id, msg)

    await show_global_role_settings(user_id, state)