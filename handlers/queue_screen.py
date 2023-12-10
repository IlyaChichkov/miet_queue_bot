import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_conf.bot_logging import log_user_info
from events.queue_events import update_queue_event, user_assigned_event, username_changed_event
from firebase_manager.firebase import queue_pop, switch_room_queue_enabled, get_user_name
from handlers.room_welcome import welcome_room_state
from message_forms.assign_form import get_assigned_mesg, get_assigned_add_note
from message_forms.queue_form import get_queue_list_mesg, get_noqueue_members_mesg, get_queue_main_form
from models.note import StudyNote
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user
from models.user import User
from roles.check_user_role import IsAdmin
from routing.router import handle_message, send_message
from routing.user_routes import UserRoutes
from states.room_state import RoomVisiterState
from bot_conf.bot import bot

router = Router()

queue_viewers = []
queue_view_update = {}

async def update_queue_handler(room_id, user_id):
    await update_queue_list()


async def update_queue_list():
    for viewer in queue_viewers:
        user: User = await get_user(viewer)
        if user.route == UserRoutes.QueueView:
            await queue_list_send(viewer)
        else:
            queue_viewers.remove(viewer)


username_changed_event.add_handler(update_queue_list)
update_queue_event.add_handler(update_queue_handler)


@router.callback_query(F.data == "action#toggle_queue")
async def change_queue_enabled(callback: types.CallbackQuery, state: FSMContext):
    queue_state = await switch_room_queue_enabled(callback.from_user.id)
    result_msg = {
        True: "✅ Вы включили очередь",
        False: "⛔ Вы выключили очередь"
    }
    await callback.answer(result_msg[queue_state], parse_mode="HTML")
    await queue_list_send(callback.from_user.id)


@router.callback_query(F.data == "queue_back", RoomVisiterState.ROOM_QUEUE_SCREEN)
async def exit_queue_list_call(message: types.Message, state: FSMContext):
    await exit_queue_list(message, state)


async def queue_pop_handler(callback: types.CallbackQuery, state: FSMContext):
    '''
    Обработка принятия первого человека в очереди
    '''
    user_id = callback.from_user.id

    # user_name = await get_user_name(pop_user_id)
    # await bot.send_message(user_id, f'Взял пользователя: <b>{user_name}</b>',
    #                       parse_mode="HTML")

    pop_user_id = await queue_pop(user_id)
    if pop_user_id is None:
        logging.info(f'Try to pop empty queue.')
        await callback.answer('В очереди никого нет')
        return

    logging.info(f'USER_{user_id} taking first user from queue.')
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    await delete_cache_messages(user_id)
    user: User = await get_user(user_id)
    user.assigned_user_id = pop_user_id

    await assigned_screen(callback, pop_user_id)
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
    await queue_list_send(message.from_user.id)


@router.message(RoomVisiterState.ROOM_QUEUE_SCREEN)
async def queue_list_send(user_id):
    '''
    Меню с очередью, отрисовка + кеширование
    '''
    log_user_info(user_id, f'Drawing queue list screen to user.')

    main_form, mf_kb = await get_queue_main_form(user_id)
    await handle_message(user_id, main_form, reply_markup=mf_kb)

    user: User = await get_user(user_id)
    await user.set_route(UserRoutes.QueueView)

    if user_id not in queue_viewers:
        queue_viewers.append(user_id)


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
    if user_id in queue_viewers:
        queue_viewers.remove(user_id)
        return True

    if user_id in queue_view_update:
        cache_messages = queue_view_update.pop(user_id, None)
        title_message: types.Message = cache_messages['title']
        await bot.delete_message(chat_id=title_message.chat.id, message_id=title_message.message_id)
        queue_message: types.Message = cache_messages['queue']
        await bot.delete_message(chat_id=queue_message.chat.id, message_id=queue_message.message_id)
        return True
    return False


@router.callback_query(F.data == "action#add_note", RoomVisiterState.ROOM_ASSIGN_SCREEN)
async def assigned_add_note(callback: types.CallbackQuery, state: FSMContext):
    '''
    Начало добавления примечания
    '''
    await state.set_state(RoomVisiterState.ASSIGN_NOTE_SCREEN)
    form_message, form_kb = await get_assigned_add_note()
    await handle_message(callback.from_user.id, form_message, reply_markup=form_kb)


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
    await send_message(message.from_user.id, f"Заметка добавлена!")
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


@router.callback_query(F.data == "show#assigned_screen")
async def assigned_screen_call(callback: types.callback_query, state: FSMContext):
    user = await get_user(callback.from_user.id)
    await state.set_state(RoomVisiterState.ROOM_ASSIGN_SCREEN)
    await assigned_screen(callback, user.assigned_user_id)


async def assigned_screen(message: types.Message, pop_user_id):
    '''
    Меню для модераторов с назначенным студентом
    '''
    log_user_info(message.from_user.id, f'Drawing assigned screen to user.')
    form_message, form_kb = await get_assigned_mesg(pop_user_id)

    await handle_message(message.from_user.id, form_message, reply_markup=form_kb)