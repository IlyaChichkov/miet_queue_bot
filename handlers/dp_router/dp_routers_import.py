from bot_conf.bot import dp
from handlers import admin_commands, own_rooms_handler, welcome, room_actions, assign_screen, profile_settings, room_settings, room_welcome, main_screens, queue_screen, queue_settings
from handlers.setting_menus import ban_menu

async def import_routers():
    dp.include_routers(admin_commands.router)
    dp.include_routers(queue_settings.router)
    dp.include_routers(main_screens.router)
    dp.include_routers(own_rooms_handler.router)
    dp.include_routers(welcome.router)
    dp.include_routers(profile_settings.router)
    dp.include_routers(room_settings.router)
    dp.include_routers(room_actions.router)
    dp.include_routers(room_welcome.router)
    dp.include_routers(queue_screen.router)
    dp.include_routers(assign_screen.router)
    dp.include_routers(ban_menu.router)