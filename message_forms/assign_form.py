from firebase_manager.firebase import get_user_name
from keyboards.assign_keyboard import get_assign_kb, get_assign_note_kb


async def get_assigned_mesg(pop_user_id):
    user_name = await get_user_name(pop_user_id)
    kb = get_assign_kb()
    return f'Меню работы со студентом <b>{user_name}</b>', kb


async def get_assigned_add_note():
    kb = get_assign_note_kb()
    return f'Введите примечание:', kb


async def get_assigned_note_added():
    kb = get_assign_note_kb()
    return f'Примечание добавлено!', kb