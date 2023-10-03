import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_logging import log_user_info
from events.queue_events import update_queue_event, user_assigned_event
from firebase import queue_pop
from handlers.room_welcome import welcome_room_state
from message_forms.assign_form import get_assigned_mesg
from message_forms.queue_form import get_queue_list_mesg, get_queue_main, get_noqueue_members_mesg
from states.room import RoomVisiterState
from bot import bot

router = Router()

queue_view_update = {}

async def update_list_for_users():
    '''
    Обновление списка с очередью для всех модераторов/админа
    '''
    logging.info(f'Update queue list for all viewing users.')
    current_dict = dict(queue_view_update)
    for key, mesg in current_dict.items():
        message: types.Message = mesg
        try:
            queue_message = message['queue']
            message_form = await get_queue_list_mesg(key)
            await bot.edit_message_text(message_form['mesg'] ,chat_id=queue_message.chat.id,
                                     message_id=queue_message.message_id, reply_markup=message_form['kb'])
        except Exception as e:
            logging.error(str(e))
            await delete_cache_messages(key)
            await queue_list_send(message['user_msg'], key)


update_queue_event.add_handler(update_list_for_users)


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def exit_queue_list_back(message: types.Message, state: FSMContext):
    await exit_queue_list(message, state)


@router.callback_query(F.data == "queue_back", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def exit_queue_list_call(message: types.Message, state: FSMContext):
    await exit_queue_list(message, state)


@router.callback_query(F.data == "queue_pop", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_pop_call(message: types.Message, state: FSMContext):
    '''
    Callback для принятия первого человека в очереди
    '''
    user_id = message.from_user.id

    # user_name = await get_user_name(pop_user_id)
    #await bot.send_message(user_id, f'Взял пользователя: <b>{user_name}</b>',
    #                       parse_mode="HTML")

    user_message = get_user_cache_message(user_id)
    if not user_message:
        user_message = message

    log_user_info(user_message.from_user.id, f'User try to queue.pop')

    current_state = await state.get_state()
    print(current_state)
    print(RoomVisiterState.ROOM_WELCOME_SCREEN)
    print(current_state is RoomVisiterState.ROOM_WELCOME_SCREEN)
    pop_user_id = await queue_pop(user_id)
    if pop_user_id is None:
        logging.info(f'Try to pop empty queue.')
        await user_message.answer(get_noqueue_members_mesg()['mesg'], parse_mode="HTML")
        return

    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    await delete_cache_messages(user_id)
    await assigned_screen(user_message, pop_user_id)
    await user_assigned_event.fire(user_id, pop_user_id)


async def exit_queue_list(message: types.Message, state: FSMContext):
    '''
    Выход из меню очереди
    '''
    log_user_info(message.from_user.id, f'User left queue list screen.')
    user_id = message.from_user.id
    user_message: types.Message = get_user_cache_message(user_id)
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(user_message)
    await delete_cache_messages(user_id)


@router.message(RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_list_state(message: types.Message):
    await queue_list_send(message)


@router.message(RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_list_send(message: types.Message, user_id = None):
    '''
    Меню с очередью, отрисовка + кеширование
    '''
    if not user_id:
        user_id = message.from_user.id

    log_user_info(user_id, f'Drawing queue list screen to user.')
    main_form = await get_queue_main()
    message_form = await get_queue_list_mesg(user_id)
    title_message = await message.answer(main_form['mesg'], reply_markup=main_form['kb'])
    queue_message = await message.answer(message_form['mesg'], reply_markup=message_form['kb'])

    if not(await update_cache_messages(user_id, 'title', title_message) and
        await update_cache_messages(user_id, 'queue', queue_message)):
        # Если нет кеша с сообщениями об очереди, то создаем
        queue_view_update[user_id] = {"user_msg": message,
                                  "title": title_message,
                                  "queue": queue_message}


def get_user_cache_message(user_id) -> types.Message:
    '''
    Получить последнее отправленное модератором/админом сообщение
    '''
    if user_id in queue_view_update:
        cache_messages = queue_view_update[user_id]
        return cache_messages['user_msg']
    return None


async def update_cache_messages(user_id, message_type, new_message):
    if user_id in queue_view_update:
        queue_view_update[user_id][message_type] = new_message
        return True
    return False


async def delete_cache_messages(user_id):
    '''
    Удаление кеша
    '''
    if user_id in queue_view_update:
        cache_messages = queue_view_update.pop(user_id, None)
        title_message: types.Message = cache_messages['title']
        await bot.delete_message(chat_id=title_message.chat.id, message_id=title_message.message_id)
        queue_message: types.Message = cache_messages['queue']
        await bot.delete_message(chat_id=queue_message.chat.id, message_id=queue_message.message_id)
        return True
    return False



@router.message(F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def exit_assigned(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.message(F.text.lower() == "в главное меню", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def exit_assigned(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_WELCOME_SCREEN)
    await welcome_room_state(message)


@router.message(RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def exit_assigned(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


async def assigned_screen(message: types.Message, pop_user_id):
    '''
    Меню для модераторов с назначенным студентом
    '''
    log_user_info(message.from_user.id, f'Drawing assigned screen to user.')
    message_form = await get_assigned_mesg(pop_user_id)

    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    builder = ReplyKeyboardBuilder()

    builder.row(
        types.KeyboardButton(text="Посмотреть очередь"),
        types.KeyboardButton(text="В главное меню"),
    )

    kb = builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    await message.answer(message_form['mesg'], reply_markup=kb, parse_mode="HTML")