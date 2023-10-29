from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot import bot
from models.room import Room
from models.server_admin import delete_cache, show_cache, update_cache, add_teacher, get_cache_file
from roles.special_roles import check_access_level, GlobalRoles
from states.admin import AdminState

router = Router()


@router.message(Command("delete_cache"))
async def delete_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await message.answer("Удаление кэша на сервере...")
        await delete_cache()
        await message.answer("Готово!")


@router.message(F.text.lower() == "посмотреть кэш")
@router.message(Command("show_cache"))
async def show_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await get_cache_file(message)


@router.message(F.text.lower() == "добавить преподавателя")
@router.message(Command("add_teacher"))
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


@router.message(F.text.lower() == "обновить кэш")
@router.message(Command("update_cache"))
async def update_server_cache(message: types.Message, state: FSMContext):
    has_access = await check_access_level(message.from_user.id, GlobalRoles.Developer)
    if has_access:
        await message.answer("Обновление кеша на сервере данными из БД...")
        await update_cache()
        await message.answer("Готово!")
        log_message = await show_cache()
        await message.answer(log_message)
