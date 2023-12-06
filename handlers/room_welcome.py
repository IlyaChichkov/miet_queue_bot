import asyncio
import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from bot_conf.bot import bot
from events.queue_events import update_queue_event, users_notify_queue_changed_event, user_joined_queue_event, \
    users_notify_queue_skipped, favorite_toggle_event
from firebase_manager.firebase import db_get_user_room, is_user_name_default, get_user_name
from message_forms.room_forms import get_welcome_message
from models.room import Room
from models.server_rooms import get_room
from routing.router import handle_message, send_message, answer_message
from states.room_state import RoomVisiterState

router = Router()

main_message_cache = {}
queue_message_cache = {}


@router.callback_query(F.data == 'show#room_menu')
async def show_room_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room(callback, callback.from_user.id)


async def welcome_room(message: types.Message, user_id = None):
    '''
    Вывод сообщения главного меню комнаты
    '''
    if not user_id:
        user_id = message.from_user.id
    room = await db_get_user_room(user_id)
    user_name = await get_user_name(user_id)

    if 'room' in room:
        if await is_user_name_default(user_id):
            await send_message(user_id, f'ℹ️ Ваше имя соответствует стандартному: «<b>{user_name}</b>». Пожалуйста поменяйте его в настройках профиля (Имя Фамилия №ПК)')
        mesg = await get_welcome_message(user_id, room['room'])

        asyncio.create_task(delete_main_message_cache(user_id))
        main_cache_msg = await handle_message(user_id, mesg['mesg_text'], reply_markup=mesg['keyboard'])
        main_message_cache[user_id] = main_cache_msg

        if 'queue_list' in mesg and mesg['queue_list']:
            asyncio.create_task(delete_queue_message_cache(user_id))
            cache_msg = await message.answer(mesg['queue_list'], parse_mode="HTML")
            queue_message_cache[user_id] = cache_msg

    else:
        await message.answer(f"Произошла ошибка при присоединении к комнате.\n"
                             f"{room['error']}")


async def delete_main_message_cache(user_id):
    if user_id in main_message_cache:
        try:
            cache_msg = main_message_cache[user_id]
            await bot.delete_message(chat_id=cache_msg.chat.id, message_id=cache_msg.message_id)
        except Exception as ex:
            logging.error(ex)


async def delete_queue_message_cache(user_id):
    if user_id in queue_message_cache:
        try:
            cache_msg = queue_message_cache[user_id]
            await bot.delete_message(chat_id=cache_msg.chat.id, message_id=cache_msg.message_id)
        except Exception as ex:
            logging.error(ex)


async def update_welcome_room(room_id):
    room: Room = await get_room(room_id)
    for room_user in room.users:
        mesg = await get_welcome_message(room_user, room)
        if room_user in queue_message_cache:
            cache_msg = queue_message_cache[room_user]
            if cache_msg and cache_msg.text != mesg['queue_list']:
                try:
                    if 'queue_list' in mesg and mesg['queue_list']:
                        await bot.edit_message_text(mesg['queue_list'], chat_id=cache_msg.chat.id,
                                                message_id=cache_msg.message_id)
                except Exception as ex:
                    logging.error(ex)
        else:
            try:
                cache_msg = await bot.send_message(room_user, mesg['queue_list'], parse_mode="HTML")
                queue_message_cache[room_user] = cache_msg
            except Exception as ex:
                logging.error(ex)


@router.message(RoomVisiterState.ROOM_WELCOME_SCREEN)
async def welcome_room_state(message: types.Message):
    await welcome_room(message)