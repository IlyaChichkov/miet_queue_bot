from events.event import AsyncEvent

update_queue_event = AsyncEvent()
user_assigned_event = AsyncEvent()
queue_enable_state_event = AsyncEvent()
user_joined_event = AsyncEvent()
user_leave_event = AsyncEvent()

# update_queue_event.add_handler(update_list_for_users)