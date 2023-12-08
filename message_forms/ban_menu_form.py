from keyboards.ban_keyboard import get_ban_menu_kb


async def get_ban_menu_form(user_id):
    kb = await get_ban_menu_kb(user_id)
    form = 'Редактирование черного списка:'
    return form, kb