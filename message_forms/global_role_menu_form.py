from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from firebase_manager.firebase import get_global_role_users_dict, get_user_name
from roles.special_roles import GlobalRoles


async def get_global_role_settings_form(user_id):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#admin_menu')
    )
    kb = builder.as_markup(resize_keyboard=True)

    form = 'Редактирование глобальный ролей:\n> help - список команд\n'
    l = await get_global_role_users_dict()
    for user_data in l:
        user_id = int(user_data['user_id'])
        name = await get_user_name(user_id)
        form += f"(<code>{user_id}</code>) <b>{name}</b> - {str(GlobalRoles(user_data['role'])).split('.')[1]}\n"
    return form, kb

async def get_global_role_help_form(user_id):
    form = 'Команды:\n> add (user_id) (role)\n> rm (user_id)\n'
    return form