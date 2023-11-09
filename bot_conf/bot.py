from aiogram import Bot, Dispatcher
from options import env_tokens

bot = Bot(token=env_tokens['BOT_TOKEN'])
dp = Dispatcher()
