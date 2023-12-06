from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_conf.bot_logging import log_user_info
from firebase_manager.firebase import change_user_name, get_user_name
from handlers.main_screens import start_command
from handlers.room_actions import RoomVisiterState
from keyboards.profile_settings_kb import get_settings_kb, get_delete_profile_kb
from models.note import export_study_notes_by_user
from models.room import Room
from models.server_rooms import get_room
from models.server_users import get_user, remove_user_from_db
from models.user import User
from roles.check_user_role import IsAdmin, IsModerator
from routing.router import handle_message, send_message
from routing.user_routes import UserRoutes

router = Router()


@router.callback_query(F.data == "show#profile")
async def profile_settings_state(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.callback_query(F.data == "show#my_notes", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_notes_call(callback: types.CallbackQuery, state: FSMContext):
    '''
    Отображение заметок преподавателя
    '''
    user: User = await get_user(callback.from_user.id)
    room: Room = await get_room(user.room)

    message_data = export_study_notes_by_user(room.study_notes, user.user_id)

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'show#profile'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    await handle_message(callback.from_user.id, message_data, kb)


@router.message(IsAdmin(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
@router.message(IsModerator(), F.text.lower() == "мои заметки", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_notes(message: types.Message, state: FSMContext):
    '''
    Отображение заметок преподавателя
    '''
    user: User = await get_user(message.from_user.id)
    room: Room = await get_room(user.room)

    message_data = export_study_notes_by_user(room.study_notes, user.user_id)
    await handle_message(message.from_user.id, message_data)
    await profile_settings_state(message, state)


@router.callback_query(F.data == "action#delete_profile", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
@router.message(F.text.lower() == "удалить профиль", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_delete(message: types.Message, state: FSMContext):
    kb = await get_delete_profile_kb(message.from_user.id)
    await handle_message(message.from_user.id, f"Вы уверены что хотите удалить профиль?", reply_markup=kb)


@router.callback_query(F.data.startswith("delete_profile"), RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_delete(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split('#')[1]
    if await remove_user_from_db(user_id):
        await callback.message.answer(f"Профиль успешно удален!")
    else:
        await callback.message.answer(f"Возникла ошибка при удалении профиля.")


@router.message(F.text.lower() == "изменить имя", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
@router.callback_query(F.data == "action#change_name", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_change_name(message: types.Message, state: FSMContext):
    '''
    Переход в состояние изменения пользовательского имени
    '''

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'action#cancel_change_name'
        )
    )

    kb = builder.as_markup(resize_keyboard=True)

    await state.set_state(RoomVisiterState.CHANGE_PROFILE_NAME)
    await handle_message(message.from_user.id,f"✏️ 1. Введите новое имя (Имя Фамилия):", reply_markup=kb)


@router.callback_query(F.data == "action#cancel_change_name", RoomVisiterState.CHANGE_PROFILE_NAME)
async def cancel_change_name(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.message(F.text.lower() == "назад", RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_back(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await start_command(message, state)


@router.message(F.text.lower() == "назад", RoomVisiterState.CHANGE_PROFILE_NAME)
async def profile_back(message: types.Message, state: FSMContext):
    await state.set_state(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
    await profile_settings(message)


@router.message(RoomVisiterState.PROFILE_SETTINGS_SCREEN)
async def profile_settings(message: types.Message):
    kb = await get_settings_kb(message.from_user.id)
    user: User = await get_user(message.from_user.id)
    await user.set_route(UserRoutes.Profile)
    user_name = await get_user_name(message.from_user.id)
    await handle_message(message.from_user.id, f"⚙️ Настройки профиля «<b>{user_name}</b>»", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_PROFILE_NAME)
async def change_user_name_state(message: types.Message, state: FSMContext):
    '''
    Подтверждение изменения имени
    '''

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'show#profile'
        )
    )
    kb = builder.as_markup(resize_keyboard=True)

    input_name = message.text
    if not input_name.replace(' ', '').isalpha():
        await handle_message(message.from_user.id,f"Неверный формат имени\n✏️ 1. Введите новое имя (Имя Фамилия):", reply_markup=kb)
        return

    if 'Мод' in input_name or 'мод' in input_name:
        import re
        replace_regex = re.compile(re.escape('мод'), re.IGNORECASE)
        user_name = replace_regex.sub('', input_name)
        user_name = '⭐ ' + user_name
        await change_user_name(message.from_user.id, user_name)
        log_user_info(message.from_user.id, f'Changed name to: {message.text}')
        await send_message(message.from_user.id,f"✅ Имя успешно изменено на {input_name}")
        await profile_settings_state(message, state)
        return

    if 'Адм' in input_name or 'адм' in input_name:
        import re
        replace_regex = re.compile(re.escape('адм'), re.IGNORECASE)
        user_name = replace_regex.sub('', input_name)
        user_name = '👑 ' + user_name
        await change_user_name(message.from_user.id, user_name)
        log_user_info(message.from_user.id, f'Changed name to: {message.text}')
        await send_message(message.from_user.id,f"✅ Имя успешно изменено на {input_name}")
        await profile_settings_state(message, state)
        return

    if 1 < len(input_name.split(' ')) < 3:
        user: User = await get_user(message.from_user.id)
        user.nickname = message.text
        await handle_message(message.from_user.id,f"✏️ 2. Введите номер компьютера, за которым вы сидите:", reply_markup=kb)
        await state.set_state(RoomVisiterState.CHANGE_PROFILE_NAME_PC)
    else:
        await handle_message(message.from_user.id, f"Неверный формат имени\n✏️ 1. Введите новое имя (Имя Фамилия):", reply_markup=kb)


@router.message(RoomVisiterState.CHANGE_PROFILE_NAME_PC)
async def change_user_name_state(message: types.Message, state: FSMContext):
    '''
    Подтверждение изменения имени
    '''

    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text=f'Назад',
            callback_data=f'show#profile'
        )
    )

    kb = builder.as_markup(resize_keyboard=True)

    if message.text.isdigit():
        user: User = await get_user(message.from_user.id)
        user.pc_num = message.text
        user_name = user.nickname + ' ' + user.pc_num
        result = await change_user_name(message.from_user.id, user_name)
        if result:
            log_user_info(message.from_user.id, f'Changed name to: {message.text}')
            await send_message(user.user_id, f"✅ Имя успешно изменено на {user.name}")
            await profile_settings_state(message, state)
        else:
            await handle_message(user.user_id, f"Произошла ошибка.", reply_markup=kb)
    else:
        await handle_message(message.from_user.id,f"Неверный формат номера компьютера\n✏️ 2. Введите номер компьютера, за которым вы сидите:", reply_markup=kb)