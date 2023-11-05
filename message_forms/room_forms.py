import logging

from firebase import db_get_user_room, try_enter_queue
from keyboards.room_keyboard import *
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.user_roles_enum import UserRoles

role_to_welcome_kb = {
    UserRoles.Admin: get_admin_welcome_kb,
    UserRoles.Moderator: get_moderator_welcome_kb,
    UserRoles.User: get_user_welcome_kb
}

def get_user_role_in_room(user_id, room):
    if 'users' in room and user_id in room['users']:
        return UserRoles.User
    if 'moderators' in room and user_id in room['moderators']:
        return UserRoles.Moderator
    if 'admins' in room and user_id in room['admins']:
        return UserRoles.Admin


async def get_join_queue_form(user_id):
    result = await try_enter_queue(user_id)

    if 'error' in result:
        return f"{result['error_text']}"

    return f""


async def get_welcome_message(user_id, room: Room):
    role = room.get_user_role(user_id)
    keyboard_func = role_to_welcome_kb.get(role, get_user_welcome_kb)
    kb = await keyboard_func(user_id)

    room_name = room.name
    moderator_code = room.moderators_join_code
    join_code = room.users_join_code
    place_message = 'Вас нет в очереди.'
    if user_id in room.queue:
        place_message = f'Вы в очереди на {room.queue.index(user_id) + 1} месте.'

    role_to_welcome_text = {
        UserRoles.Admin:  f"📖 Вы находитесь в меню комнаты «<b>{room_name}</b>»\n"
                          f"Код для присоединения:\nМодераторов: <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                          f"Студентов: <code>{join_code}</code>",
        UserRoles.Moderator:  f"📖 Вы находитесь в меню комнаты «<b>{room_name}</b>»\n"
                              f"Код для присоединения:\nМодераторов: <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                              f"Студентов: <code>{join_code}</code>",
        UserRoles.User:  f'📖 Вы находитесь в меню комнаты «<b>{room_name}</b>»\n{place_message}'
    }
    mesg_text = role_to_welcome_text.get(role, 'None')
    return { 'mesg_text': mesg_text, 'keyboard': kb }


async def get_username(user_id):
    user: User = await get_user(user_id)
    if user:
        return user.name
    return ''


async def get_users_list_form(user_id):
    form_message = 'Список пуст'
    form_kb = get_users_list_kb()

    room_dict = await db_get_user_room(user_id)
    if 'room' in room_dict:
        room: Room = room_dict['room']
        form_message = '🔸 Админы:\n'

        for num, admin in enumerate(room.admins):
            form_message += f'    <b>{await get_username(admin)}</b>\n'

        form_message += '\n🔸 Модераторы:\n'
        for num, moderator in enumerate(room.moderators):
            form_message += f'{num + 1}.  <b>{await get_username(moderator)}</b>\n'

        form_message += '\n🔹 Пользователи:\n'
        for num, ruser in enumerate(room.users):
            form_message += f'{num + 1}. <b>{await get_username(ruser)}</b>\n'

    logging.info(f'USER_{user_id} requested users list')
    return form_message, form_kb


async def get_announcement_form(user_id):
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(
            text="Назад"
        )
    )
    form_kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    form_message = 'Введите текст общего уведомления:'
    return form_message, form_kb
