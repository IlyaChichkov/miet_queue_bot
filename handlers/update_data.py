from aiogram import Router, F, types
from bot import bot

router = Router()


async def send_update_msg(user_id, message: types.Message):
    await bot.send_message(user_id, message)
