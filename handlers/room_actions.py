from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot_logging import log_user_info
from firebase import delete_room, leave_room, enter_queue, exit_queue
from handlers.main_screens import start_command
from handlers.queue_screen import queue_list_state, queue_pop_call
from handlers.room_welcome import welcome_room_state
from message_forms.room_forms import get_users_list_form
from roles.check_user_role import IsModerator, IsAdmin, IsUser
from states.room import RoomVisiterState

router = Router()

@router.message(IsAdmin(), F.text.lower() == "список пользователей", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "список пользователей", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_users_list(message: types.Message, state: FSMContext):
    form_message, form_kb = await get_users_list_form(message.from_user.id)
    await message.answer(form_message, parse_mode="HTML", reply_markup=form_kb)


@router.message(IsAdmin(), F.text.lower() == "принять первого в очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "принять первого в очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_get_queue_pop(message: types.Message, state: FSMContext):
    await queue_pop_call(message, state)


@router.message(IsAdmin(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
@router.message(IsModerator(), F.text.lower() == "посмотреть очередь", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_queue_show(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.ROOM_QUEUE_SCREEN)
    await queue_list_state(message)


@router.message(IsAdmin(), F.text.lower() == "удалить комнату", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_delete_state(message: types.Message, state: FSMContext):
    log_user_info(message.from_user.id, f'Deleted room.')
    if await delete_room(message.from_user.id):
        await start_command(message, state)


@router.message(F.text.lower() == "выйти", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_exit_state(message: types.Message, state: FSMContext):
    await leave_room(message.from_user.id)
    await state.set_state(None)
    await start_command(message, state)


@router.message(IsUser(), F.text.lower() == "занять место", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_queue_push(message: types.Message, state: FSMContext):
    place = await enter_queue(message.from_user.id)
    await message.answer(f"#️⃣ Ваше место в очереди: <b>№{place}</b>", parse_mode="HTML")
    await welcome_room_state(message)


@router.message(IsUser(), F.text.lower() == "выйти из очереди", RoomVisiterState.ROOM_WELCOME_SCREEN)
async def room_queue_remove(message: types.Message, state: FSMContext):
    if await exit_queue(message.from_user.id):
        await message.answer(f"Вы покинули очередь")
        await welcome_room_state(message)
    else:
        await message.answer(f"Вы уже не состоите в очереди") # TODO: Add error text
        await welcome_room_state(message)