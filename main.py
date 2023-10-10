import asyncio
from dotenv import load_dotenv
from bot import dp, bot
from handlers import admin_commands, welcome, room_actions, assign_screen, profile_settings, room_settings, room_welcome, main_screens, queue_screen

import models.server_users
import models.server_rooms
import events.queue_state_handler
import events.user_join_handler
import events.user_left_handler
import bot_logging
load_dotenv()


async def main():
    dp.include_routers(admin_commands.router)
    dp.include_routers(main_screens.router)
    dp.include_routers(welcome.router)
    dp.include_routers(profile_settings.router)
    dp.include_routers(room_settings.router)
    dp.include_routers(room_actions.router)
    dp.include_routers(room_welcome.router)
    dp.include_routers(queue_screen.router)
    dp.include_routers(assign_screen.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())