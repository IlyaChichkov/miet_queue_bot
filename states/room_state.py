from aiogram.fsm.state import StatesGroup, State

class RoomVisiterState(StatesGroup):
    # Main screen
    ROOM_WELCOME_SCREEN = State()
    ADMIN_SETTINGS_SCREEN = State()
    ADMIN_ROLES_SCREEN = State()
    # Room settings
    ROOM_SETTINGS_SCREEN = State()
    CHANGE_ROOM_NAME = State()
    # Queue screen
    ROOM_QUEUE_SCREEN = State()
    ROOM_QUEUE_SETTINGS_SCREEN = State()
    QUEUE_SETTINGS_REMOVE = State()
    # Assignment screen
    ROOM_ASSIGN_SCREEN = State()
    ASSIGN_NOTE_SCREEN = State()
    # Announcement screen
    MAKE_ANNOUNCEMENT_SCREEN = State()
    # Profile settings
    PROFILE_SETTINGS_SCREEN = State()
    CHANGE_PROFILE_NAME = State()
    CHANGE_PROFILE_NAME_PC = State()



