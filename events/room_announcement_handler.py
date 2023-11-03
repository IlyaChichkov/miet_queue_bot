import logging

from bot import bot
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from models.room import Room

async def send_public_announcement(user_id, message_text):
    user: User = await get_user(user_id)
    room: Room = await get_room(user.room)
    room_users_list = room.get_users_list()
    users_count = len(room_users_list)
    logging.info(f'Making public announcement in ROOM_{user.room}\nAnnouncement message: «{message_text}»')
    for room_user in room_users_list:
        if str(room_user) == str(user_id):
            try:
                await bot.send_message(room_user, f'<i>Ваше уведомление выглядит так:</i>\n'
                                                  f'<b>📌 Уведомление от {user.name}:</b>\n{message_text}\n'
                                                  f'<i>Кол-во получивших пользователей: {users_count - 1}</i>', parse_mode="HTML")
            except Exception as ex:
                logging.error(f"Tried to make public announcement for USER_{room_user} (creator), but got error: {ex}")
        else:
            try:
                await bot.send_message(room_user, f'<b>📌 Уведомление от {user.name}:</b>\n{message_text}', parse_mode="HTML")
            except Exception as ex:
                logging.error(f"Tried to make public announcement for USER_{room_user}, but got error: {ex}")
