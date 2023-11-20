import asyncio
import logging

from dotenv import load_dotenv
from bot_conf.bot import dp, bot
from handlers import admin_commands, own_rooms_handler, welcome, room_actions, assign_screen, profile_settings, \
    room_settings, room_welcome, main_screens, queue_screen, queue_settings, addscore_screen
from models.server_admin import load_cache

''' DO NOT REMOVE | EVENTS '''
import models.server_users
import models.server_rooms
import events.queue_state_handler
import events.room_delete_handler
import events.user_join_handler
import events.user_left_handler
import events.user_join_queue_handler
import events.update_queue_handler
import events.users_notify_queue_skipped_handler
import bot_conf.bot_logging
''' DO NOT REMOVE | EVENTS '''
load_dotenv()


async def main():
    logging.info('------------------ Start bot pooling ------------------')
    dp.include_routers(admin_commands.router)
    dp.include_routers(queue_settings.router)
    dp.include_routers(main_screens.router)
    dp.include_routers(own_rooms_handler.router)
    dp.include_routers(welcome.router)
    dp.include_routers(profile_settings.router)
    dp.include_routers(room_settings.router)
    dp.include_routers(room_actions.router)
    dp.include_routers(room_welcome.router)
    dp.include_routers(addscore_screen.router)
    dp.include_routers(queue_screen.router)
    dp.include_routers(assign_screen.router)
    await load_cache()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())