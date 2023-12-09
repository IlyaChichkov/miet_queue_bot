from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot_conf.bot import bot
from keyboards.admin_keyboard import get_admin_kb
from models.server_admin import delete_cache, update_cache, add_teacher, get_cache_file
from roles.special_roles import check_access_level, GlobalRoles
from routing.router import handle_message
from states.admin_state import AdminState

router = Router()


@router.callback_query(F.data == "show#admin_menu")
async def delete_server_cache(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if has_access:
        kb = await get_admin_kb(user_id)
        await handle_message(user_id, "Управление:", kb)


@router.callback_query(F.data == "action#delete_server_cache")
async def delete_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await message.answer("Удаление кэша на сервере...")
        await delete_cache()
        await message.answer("Готово!")


@router.callback_query(F.data == "show#server_cache")
@router.message(Command("show_cache"))
async def show_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await get_cache_file(message, state)


@router.callback_query(F.data == "action#add_tutor")
async def add_teacher_action(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await state.set_state(AdminState.ADD_TEACHER)
        await message.answer("Добавление преподавателя. Введите ID:")


@router.message(AdminState.ADD_TEACHER)
async def add_teacher_state(message: types.Message, state: FSMContext):
    await add_teacher(message.text)
    await message.answer("Готово!")
    await state.set_state(None)
    try:
        await bot.send_message(int(message.text), "Вы получили права «<b>Преподавателя</b>»!", parse_mode="HTML")
    except Exception as e:
        await message.answer(str(e))


@router.callback_query(F.data == "action#update_server_cache")
async def update_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await message.answer("Обновление кеша на сервере данными из БД...")
        await update_cache()
        await message.answer("Готово!")
