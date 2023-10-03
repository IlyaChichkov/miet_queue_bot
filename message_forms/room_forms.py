from keyboards.room_keyboard import *
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

async def get_welcome_message(user_id, room):
    role = get_user_role_in_room(user_id, room['room'])
    keyboard_func = role_to_welcome_kb.get(role, get_user_welcome_kb)
    kb = await keyboard_func(user_id)

    room_name = room['room']['name']
    moderator_code = room['room']['mod_password']
    join_code = room['room']['join_code']
    role_to_welcome_text = {
        UserRoles.Admin:  f"Вы находитесь в меню комнаты «<b>{room_name}</b>»\n"
                          f"Код для присоединения модераторов:  <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                          f"Код для присоединения студентов: <code>{join_code}</code>",
        UserRoles.Moderator:  f"Вы находитесь в меню комнаты «<b>{room_name}</b>»\n"
                              f"Код для присоединения модераторов:  <tg-spoiler><code>{moderator_code}</code></tg-spoiler>\n"
                              f"Код для присоединения студентов: <code>{join_code}</code>",
        UserRoles.User:  f'Вы находитесь в меню комнаты «<b>{room_name}</b>»\n'
    }
    mesg_text = role_to_welcome_text.get(role, 'None')
    return { 'mesg_text': mesg_text, 'keyboard': kb }