from events.queue_events import user_leave_event
from roles.role_cache import delete_user_role_cache


async def leave_role_cache_remove(user_id):
    await delete_user_role_cache(user_id)


user_leave_event.add_handler(leave_role_cache_remove)