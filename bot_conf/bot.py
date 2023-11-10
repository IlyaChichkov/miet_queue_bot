from aiogram import Bot, Dispatcher

from bot_conf.options import env_tokens

bot = Bot(token=env_tokens['BOT_TOKEN'])
dp = Dispatcher()
