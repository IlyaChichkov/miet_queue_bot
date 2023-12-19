import asyncio
import logging

from dotenv import load_dotenv
from bot_conf.bot import dp, bot
from handlers.dp_router.dp_routers_import import import_routers
from models.server_admin import load_cache

''' DO NOT REMOVE | EVENTS '''
import models.server_users
import models.server_rooms
import models.server_jornals
import events.room_delete_handler
import events.user_left_handler
import events.user_join_queue_handler
import events.update_queue_handler
import events.users_notify_queue_skipped_handler
import bot_conf.bot_logging
''' DO NOT REMOVE | EVENTS '''
load_dotenv()


async def main():
    logging.info('------------------ Start bot pooling ------------------')
    await import_routers()
    await load_cache()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())