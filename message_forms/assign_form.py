from firebase import get_user_name


async def get_assigned_mesg(pop_user_id):
    user_name = await get_user_name(pop_user_id)
    return {"mesg": f'Взял пользователя: <b>{user_name}</b>'}
