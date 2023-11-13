from events.event import AsyncEvent

users_notify_queue_skipped = AsyncEvent()
users_notify_queue_changed_event = AsyncEvent()

update_queue_event = AsyncEvent()
user_assigned_event = AsyncEvent()
queue_enable_state_event = AsyncEvent()
user_joined_event = AsyncEvent()
user_leave_event = AsyncEvent()

username_changed_event = AsyncEvent()

user_joined_queue_event = AsyncEvent()

delete_room_event = AsyncEvent()
update_room_event = AsyncEvent()
update_user_event = AsyncEvent()

# update_queue_event.add_handler(update_list_for_users)