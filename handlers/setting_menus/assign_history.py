from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.room_event import RoomEventType
from models.room_journal import RoomJournal
from models.server_jornals import get_room_journal
from models.server_users import get_user
from models.user import User
from routing.router import handle_message

from firebase_manager.firebase import get_user_name

router = Router()

@router.callback_query(F.data == 'show#assign_history')
async def show_assign_history(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#profile')
    )
    kb = builder.as_markup(resize_keyboard=True)
    form = await get_history(user_id)
    await handle_message(user_id, form, reply_markup=kb)

async def get_history(user_id):
    user: User = await get_user(user_id)
    journal: RoomJournal = await get_room_journal(user.room)
    events = journal.get_events_by_type(RoomEventType.USER_ASSIGNED)
    history_msg = 'История:\n'
    for ev in events:
        user_name = await get_user_name(int(ev.event_data['user_id']))
        history_msg += f"[{ev.datetime.split(' ')[1]}] Принял пользователя <b>{user_name}</b>\n"
    return history_msg