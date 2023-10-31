import logging

from aiogram import types

from bot import bot
from events.queue_events import queue_enable_state_event
from firebase import get_room_by_key
from models.room import Room


async def notify_user_queue_switch(room_key, new_val):
    '''
    Отправка сообщения пользователю о том, очередь включили/выключили
    '''
    room: Room = await get_room_by_key(room_key)
    queue_state_to_msg = {
        None: "[no_state]",
        True: "✅ Очередь включили",
        False: "⛔ Очередь выключили"
    }

    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    if new_val:
        builder.row(
            types.KeyboardButton(text="Занять место"),
        )
    else:
        builder.row(
            types.KeyboardButton(text="Вернуться в меню"),
        )

    kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

    for user_num, user_in_queue in enumerate(room.users):
        print(f'Send message about {user_num} to {user_in_queue}')
        try:
            await bot.send_message(user_in_queue, f'{queue_state_to_msg[new_val]}!',  reply_markup=kb, parse_mode="HTML")
        except Exception as ex:
            logging.info(f"Tried to notify USER_{user_in_queue} about room queue state was switched to {new_val}, but got error: {ex}")


queue_enable_state_event.add_handler(notify_user_queue_switch)