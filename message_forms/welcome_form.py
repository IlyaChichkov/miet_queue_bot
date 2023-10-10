from aiogram.types import FSInputFile
from keyboards.welcome_keyboard import get_welcome_kb, get_owner_rooms_kb


async def get_owner_rooms_form(user_id):
    keyboard = await get_owner_rooms_kb(user_id)
    message = "Ваши комнаты:"

    return message, keyboard


async def get_welcome_form(user_name, user_id):
    keyboard = await get_welcome_kb(user_id)
    message = f"Добро пожаловать {user_name}! Пожалуйста выберите действие:"

    return message, keyboard
