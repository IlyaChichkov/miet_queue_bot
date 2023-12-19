import logging
import shutil

from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
import os

from aiogram.utils.media_group import MediaGroupBuilder

import bot_conf.bot_logging
from bot_conf.bot import bot
from keyboards.admin_keyboard import get_admin_kb
from models.server_admin import delete_cache, update_cache, get_cache_file
from models.server_users import get_user
from roles.special_roles import check_access_level, GlobalRoles
from routing.router import handle_message, send_document, send_message, send_group
from states.admin_state import AdminState
from states.room_state import RoomVisiterState

router = Router()


@router.message(Command('myid'))
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    await send_message(user_id, f'Ваш ID: <span class="tg-spoiler">{user_id}</span>')


@router.message(Command('update_my_role'))
async def show_user_id(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    await user.check_global_role()


@router.message(Command('admin'))
@router.callback_query(F.data == "show#admin_menu")
async def delete_server_cache(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if has_access:
        await state.set_state(RoomVisiterState.ADMIN_SETTINGS_SCREEN)
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


@router.callback_query(F.data == "action#update_server_cache")
async def update_server_cache(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if has_access:
        await callback.answer("Обновление кеша на сервере данными из БД...")
        await update_cache()
        await send_message(user_id, "Обновление кеша завершено!")


@router.callback_query(F.data == "action#get_log_files")
async def update_server_cache(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    has_access = await check_access_level(user_id, GlobalRoles.Developer)
    if not has_access:
        return

    folder_path = bot_conf.bot_logging.logs_dir
    destination_folder = 'log_buffer'
    files = [(f, os.path.getmtime(os.path.join(folder_path, f))) for f in os.listdir(folder_path)]

    files.sort(key=lambda x: x[1], reverse=True)
    last_5_files = files[:5]

    await bot.send_chat_action(user_id, ChatAction.UPLOAD_DOCUMENT)
    # Создаем папку для копий файлов, если она не существует
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Копируем последние 5 файлов в новую папку
    for file_name, _ in last_5_files:
        file_path = f'{folder_path}/{file_name}'
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy(file_path, destination_path)

    media = MediaGroupBuilder()
    for file_name, _ in last_5_files:
        try:
            file_path = f'./{destination_folder}/{file_name}'
            file_size = os.path.getsize(file_path)

            if file_size == 0:
                continue
            file = types.FSInputFile(file_path)
            media.add_document(file)

        except Exception as ex:
            logging.error(ex)

    await send_group(user_id, media)
    shutil.rmtree(destination_folder)
    await send_message(user_id, "Выгрузка лога завершена ✅")
    logging.info(f'Finished last 5 log files unload by USER_{user_id}')