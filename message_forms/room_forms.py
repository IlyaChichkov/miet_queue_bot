import logging

from firebase_manager.firebase import try_enter_queue, get_queue_users
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

    return result


def format_user_count(count):
    if count % 10 == 1 and count % 100 != 11:
        word_form = 'пользователь'
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        word_form = 'пользователя'
    else:
        word_form = 'пользователей'
    return word_form


async def get_welcome_queue_message(room: Room):
    queue_list = '<b>Очередь:</b>\n'
    overflow = False
    max_display_count = 5

    users_names = []
    for queue_user_id in room.queue:
        user: User = await get_user(queue_user_id)
        users_names.append(user.name)

    disp_count = len(users_names) - max_display_count
    if disp_count > 0:
        users_names = users_names[:max_display_count]
        overflow = True

    if len(users_names) < 1:
        queue_list = ''
    for i, user_name in enumerate(users_names):
        queue_list += f'{i + 1}. {user_name}\n'

    if overflow:
        queue_list += f"Еще {disp_count} {format_user_count(disp_count)}"

    return queue_list


async def get_welcome_message(user: User, room: Room):
    user_id = user.user_id
    role = room.get_user_role(user_id)
    keyboard_func = role_to_welcome_kb.get(role, get_user_welcome_kb)
    is_room_favorite = room.room_id in user.favorites
    kb = await keyboard_func(user, is_room_favorite)

    room_name = room.name
    moderator_code = room.moderators_join_code
    join_code = room.users_join_code

    room_users_count = len(room.get_users_list())
    room_users_mesg = f'Сейчас в комнате {room_users_count} ' + format_user_count(room_users_count)

    place_message = ''
    if user_id in room.queue:
        place_message = f'Вы в очереди на {room.queue.index(user_id) + 1} месте.'

    queue_status = room.is_queue_enabled
    if not queue_status:
        place_message = ''
    queue_status_form = {
        True: "✅",
        False: "⛔"
    }
    queue_status_msg = f"Очередь: {queue_status_form[queue_status]}"
    role_to_welcome_text = {
        UserRoles.Admin:  f"🎄 Комната «<b>{room_name}</b>»\n{queue_status_msg}\n{room_users_mesg}\n"
                          f"<b>Код для присоединения:</b>\nМодераторов: <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                          f"Студентов: <code>{join_code}</code>",
        UserRoles.Moderator:  f"🎄 Комната «<b>{room_name}</b>»\n{queue_status_msg}\n{room_users_mesg}\n"
                              f"<b>Код для присоединения:</b>\nМодераторов: <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                              f"Студентов: <code>{join_code}</code>",
        UserRoles.User:  f'🎄 Комната «<b>{room_name}</b>»\n{queue_status_msg}\n{room_users_mesg}\n{place_message}'
    }
    mesg_text = role_to_welcome_text.get(role, 'None')
    queue_list = ''
    #if role == UserRoles.User:
    queue_list = await get_welcome_queue_message(room)
    return { 'mesg_text': mesg_text, 'keyboard': kb, 'queue_list': queue_list }


async def get_username(user_id):
    user: User = await get_user(user_id)
    if user:
        return user.name
    return ''


async def get_users_list_form(user_id):
    form_message = 'Список пуст'
    form_kb = get_users_list_kb()

    user = await get_user(user_id)
    room = await get_room(user.room)
    if room:
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
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#room_menu'
        )
    )
    form_kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    form_message = 'Введите текст общего уведомления:'
    return form_message, form_kb
