from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from firebase import get_queue_users, get_user_room_key, get_room_queue_enabled_by_userid
from keyboards.queue_keyboard import get_main_queue_kb, get_queue_kb
from roles.role_cache import get_user_role


def get_noqueue_members_mesg():
    return {"mesg": f"В очереди никого нет 👻",
            "kb": None}



async def get_queue_main_admin():
    return {"mesg": f"✏️Очередь для сдачи:"}


async def get_queue_main():
    return {"mesg": f"✏️Очередь для сдачи:",
            "kb": get_main_queue_kb()}


async def get_queue_update_form(user_id):
    main_form, mf_kb = await get_queue_main_form(user_id)
    main_form = await get_queue_list_mesg(user_id)
    return main_form, mf_kb

async def get_queue_main_form(user_id):
    user_role = await get_user_role(user_id)
    main_form = f"✏️Очередь для сдачи:"
    builder = ReplyKeyboardBuilder()

    if user_role == 'admins':
        queue_state = await get_room_queue_enabled_by_userid(user_id)
        queue_state_to_msg = {
            None: "✅ Включить",
            True: "⛔ Выключить",
            False: "✅ Включить"
        }

        builder.row(types.KeyboardButton(text=f"{queue_state_to_msg[queue_state]} очередь"),
        types.KeyboardButton(text=f"Принять первого"))
        builder.row(types.KeyboardButton(text="Настройки очереди"))
        builder.row(types.KeyboardButton(text="Назад"))

        mf_kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        return main_form, mf_kb
    else:
        builder.row(types.KeyboardButton(text="Настройки очереди"),
                    types.KeyboardButton(text=f"Принять первого"))
        builder.row(types.KeyboardButton(text="Назад"))

        mf_kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
        return main_form, mf_kb



async def get_queue_list_mesg(user_id):
    room_queue = await get_queue_users(await get_user_room_key(user_id))
    message = f"Сейчас в очереди никого 👻"
    kb = get_queue_kb(False)
    if room_queue:
        queue_list = ''
        for i, user in enumerate(room_queue):
            queue_list += f'{i + 1}. {user}\n'
        message = f"{queue_list}"
        return message, kb
    else:
        kb = get_queue_kb(True)
        return message, kb