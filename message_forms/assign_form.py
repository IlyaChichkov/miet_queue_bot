from firebase import get_user_name
from keyboards.assign_keyboard import get_assign_kb


async def get_assigned_mesg(pop_user_id):
    user_name = await get_user_name(pop_user_id)
    kb = get_assign_kb()
    return f'Взял пользователя: <b>{user_name}</b>', kb
