import logging
from aiogram import Router, types
from bot_conf.bot import bot
from events.queue_events import user_assigned_event
from firebase_manager.firebase import get_user_name, get_user_room_key, get_room_by_key

router = Router()


async def assign_user(moderator_id, user_id):
    '''
    Отправка сообщения пользователю о том, что его готовы принять.
    Остальным пользователя о том, какое теперь место в очереди они занимают
    '''
    try:

        from aiogram.utils.keyboard import ReplyKeyboardBuilder
        builder = ReplyKeyboardBuilder()

        builder.row(
            types.KeyboardButton(text="Вернуться в меню"),
        )
        kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

        user_name = await get_user_name(moderator_id)
        await bot.send_message(user_id, f'Вас принял для сдачи: <b>{user_name}</b>', reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logging.error(str(e))

    #room_key = await get_user_room_key(moderator_id)
    #room = await get_room_by_key(room_key)

    #for user_num, user_in_queue in enumerate(room.queue):
    #    print(f'Send message about {user_num} to {user_in_queue}')
    #    await bot.send_message(user_in_queue, f'Очередь сдвинулась, вы на <b>{user_num + 1}</b> месте', parse_mode="HTML")
    #await welcome_room(message)
    #state = dp.current_state(chat=message.chat.id, user=user_id)
    #await state.set_state(User.accepted)


user_assigned_event.add_handler(assign_user)