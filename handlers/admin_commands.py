from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from models.room import Room
from models.server_admin import check_admin, delete_cache, show_cache, update_cache
from states.room import RoomVisiterState
from states.welcome import WelcomeState

router = Router()


@router.message(Command("delete_cache"))
async def delete_server_cache(message: types.Message, state: FSMContext):
    is_admin = await check_admin(message.from_user.id)
    if is_admin:
        await message.answer("Удаление кэша на сервере...")
        await delete_cache()
        await message.answer("Готово!")


@router.message(Command("show_cache"))
async def show_server_cache(message: types.Message, state: FSMContext):
    is_admin = await check_admin(message.from_user.id)
    if is_admin:
        log_message = await show_cache()
        await message.answer(log_message)


@router.message(Command("update_cache"))
async def update_server_cache(message: types.Message, state: FSMContext):
    is_admin = await check_admin(message.from_user.id)
    if is_admin:
        await message.answer("Обновление кеша на сервере данными из БД...")
        await update_cache()
        await message.answer("Готово!")
        log_message = await show_cache()
        await message.answer(log_message)
