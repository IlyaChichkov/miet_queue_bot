from datetime import datetime, timedelta
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_conf.bot import bot
from firebase_manager.firebase import get_db_data
from models.server_users import get_user
from models.user import User
from routing.router import handle_message, send_message, set_user_new_message
from states.room_state import RoomVisiterState

router = Router()


@router.callback_query(F.data == "show#feedback_menu")
async def show_feedback_call(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    await state.set_state(RoomVisiterState.FEEDBACK_SEND)

    await handle_message(callback.from_user.id, 'Опишите вашу проблему или предложение в сообщении и отправьте:', kb)


@router.callback_query(F.data == "action#send_feedback", RoomVisiterState.FEEDBACK_SEND)
async def feedback_send_call(callback: types.CallbackQuery, state: FSMContext):
    user: User = await get_user(callback.from_user.id)

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    feedback_message = user.feedback_message
    if feedback_message is None or feedback_message == '':
        return

    current_time = datetime.now()
    if user.feedback_lastsend:
        delta: timedelta = current_time - user.feedback_lastsend

        if delta < timedelta(minutes=5):
            logging.warning(f'USER_{user.user_id} got feedback sending limit!')
            await handle_message(callback.from_user.id, 'Ошибка! Вы уже отправляли сообщение недавно.', kb)
            return
    user.feedback_lastsend = current_time

    feedback_listener: str = await get_db_data("feedback_listener")
    logging.info(f'USER_{user.user_id} ({user.name}) sent feedback message')
    await bot.send_message(feedback_listener, feedback_message, parse_mode="HTML")
    await handle_message(callback.from_user.id, 'Сообщение отправлено, спасибо!', kb)


@router.message(RoomVisiterState.FEEDBACK_SEND)
async def save_feedback_message(message: types.Message, state: FSMContext):
    if message.text is None or message.text == '':
        return
    feedback_message = f'({message.from_user.username}):\n{message.text}\n'
    await send_feedback(message.from_user.id, feedback_message)


async def send_feedback(user_id, feedback_message):
    current_time = datetime.now()
    user: User = await get_user(user_id)
    feedback_message = f'Сообщение от {user.name} ' + feedback_message + f'<i>{current_time.strftime("%d.%m %H:%M:%S")}</i>'
    logging.info(f'USER_{user_id} ({user.name}) saved feedback message')

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#main_menu'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    if user.feedback_lastsend:
        delta: timedelta = current_time - user.feedback_lastsend

        feedback_cooldown: int = int(await get_db_data("feedback_cooldown"))
        if delta < timedelta(minutes=feedback_cooldown):
            logging.warning(f'USER_{user.user_id} got feedback sending limit!')
            await set_user_new_message(user_id)
            await handle_message(user_id, 'Ошибка! Превышен лимит сообщений за промежуток времени.', kb)
            return
    user.feedback_lastsend = current_time

    feedback_listener: str = await get_db_data("feedback_listener")
    logging.info(f'USER_{user.user_id} ({user.name}) sent feedback message')
    await bot.send_message(feedback_listener, feedback_message, parse_mode="HTML")
    await set_user_new_message(user_id)
    await handle_message(user_id, 'Сообщение отправлено, спасибо!', kb)

