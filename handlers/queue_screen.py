import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot_logging import log_user_info
from events.queue_events import update_queue_event, user_assigned_event, username_changed_event
from firebase import queue_pop, get_user_role, get_room_queue_enabled_by_userid, switch_room_queue_enabled, \
    get_user_name
from handlers.room_welcome import welcome_room_state
from message_forms.assign_form import get_assigned_mesg, get_assigned_add_note
from message_forms.queue_form import get_queue_list_mesg, get_queue_main, get_noqueue_members_mesg, \
    get_queue_main_admin, get_queue_main_form
from models.note import StudyNote
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin
from states.room import RoomVisiterState
from bot import bot

router = Router()

queue_view_update = {}

async def update_queue_handler(room_id, user_id):
    await update_list_for_users()


async def update_list_for_users():
    '''
    Обновление списка с очередью для всех модераторов/админа
    '''
    logging.info(f'Update queue list for all viewing users.')
    current_dict = dict(queue_view_update)
    for user_id, mesg in current_dict.items():
        message: types.Message = mesg
        try:
            queue_message = message['queue']
            form_message, form_kb = await get_queue_list_mesg(user_id)
            await bot.edit_message_text(form_message, chat_id=queue_message.chat.id,
                                        message_id=queue_message.message_id, reply_markup=form_kb)
            #queue_message = message['queue']
            #main_form, mf_kb = await get_queue_main_form(user_id)
            #await bot.edit_message_text(main_form ,chat_id=queue_message.chat.id, message_id=queue_message.message_id, reply_markup=mf_kb)
        except Exception as e:
            logging.error(str(e))
            await delete_cache_messages(user_id)
            await queue_list_send(message['user_msg'], user_id)


username_changed_event.add_handler(update_list_for_users)
update_queue_event.add_handler(update_queue_handler)


@router.message(IsAdmin(), F.text.lower() == "⛔ выключить очередь")
async def change_queue_enabled(message: types.Message, state: FSMContext):
    await switch_room_queue_enabled(message.from_user.id)
    await message.answer("⛔ Вы выключили очередь", parse_mode="HTML")
    await queue_list_send(message)


@router.message(IsAdmin(), F.text.lower() == "✅ включить очередь")
async def change_queue_enabled(message: types.Message, state: FSMContext):
    await switch_room_queue_enabled(message.from_user.id)
    await message.answer("✅ Вы включили очередь", parse_mode="HTML")
    await queue_list_send(message)


@router.message(F.text.lower() == "назад", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def exit_queue_list_back(message: types.Message, state: FSMContext):
    await exit_queue_list(message, state)


@router.message(F.text.lower() == "принять первого", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_pop_mesg(message: types.Message, state: FSMContext):
    '''
    Callback для принятия первого человека в очереди
    '''
    await queue_pop_handler(message, state)


@router.callback_query(F.data == "queue_back", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def exit_queue_list_call(message: types.Message, state: FSMContext):
    await exit_queue_list(message, state)


@router.callback_query(F.data == "queue_pop", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_pop_call(message: types.Message, state: FSMContext):
    '''
    Callback для принятия первого человека в очереди
    '''
    await queue_pop_handler(message, state)


async def queue_pop_handler(message: types.Message, state: FSMContext):
    '''
    Обработка принятия первого человека в очереди
    '''
    user_id = message.from_user.id

    # user_name = await get_user_name(pop_user_id)
    # await bot.send_message(user_id, f'Взял пользователя: <b>{user_name}</b>',
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
    user: User = await get_user(user_id)
    user.assigned_user_id = pop_user_id
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

    main_form, mf_kb = await get_queue_main_form(user_id)
    title_message = await message.answer(main_form, reply_markup=mf_kb)
    form_message, form_kb = await get_queue_list_mesg(user_id)
    queue_message = await message.answer(form_message, reply_markup=form_kb)
    # , reply_markup=message_form['kb']

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


@router.message(F.text.lower() == "✏️ добавить примечание", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def assigned_add_note(message: types.Message, state: FSMContext):
    '''
    Начало добавления примечания
    '''
    await state.set_state(RoomVisiterState.ASSIGN_NOTE_SCREEN)
    form_message, form_kb = await get_assigned_add_note()
    await message.answer(form_message, reply_markup=form_kb, parse_mode="HTML")


@router.message(F.text.lower() == "назад", RoomVisiterState.ASSIGN_NOTE_SCREEN)
async def assigned_add_note_back(message: types.Message, state: FSMContext):
    '''
    Меню для модераторов с назначенным студентом
    '''
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    user: User = await get_user(message.from_user.id)
    await assigned_screen(message, user.assigned_user_id)


@router.message(RoomVisiterState.ASSIGN_NOTE_SCREEN)
async def assigned_note_added(message: types.Message, state: FSMContext):
    '''
    Примечание по сдаче лабораторной добавлено
    '''
    user: User = await get_user(message.from_user.id)
    room: Room = await get_room(user.room)

    teacher_name = await get_user_name(user.user_id)
    pupil_name = await get_user_name(user.assigned_user_id)
    room.study_notes.append(StudyNote(room.room_id, room.name, user.user_id, teacher_name, pupil_name, message.text))
    logging.info(f'Note was added by {user.user_id} to {user.assigned_user_id}\nNote: {message.text}')
    await message.answer(f"Заметка добавлена!", parse_mode="HTML")
    # Выход на экран очереди
    await exit_assigned_queue(message, state)


@router.message(F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def exit_assigned_queue(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.message(F.text.lower() == "в главное меню", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def exit_assigned_menu(message: types.Message, state: FSMContext):
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
    form_message, form_kb = await get_assigned_mesg(pop_user_id)

    await message.answer(form_message, reply_markup=form_kb, parse_mode="HTML")