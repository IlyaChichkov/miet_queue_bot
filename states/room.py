from aiogram.fsm.state import StatesGroup, State

class RoomVisiterState(StatesGroup):
    # Main screen
    ROOM_WELCOME_SCREEN = State()
    # Room settings
    ROOM_SETTINGS_SCREEN = State()
    CHANGE_ROOM_NAME = State()
    # Queue screen
    ROOM_QUEUE_SCREEN = State()
    # Assignment screen
    ROOM_ASSIGN_SCREEN = State()
    # Profile settings
    PROFILE_SETTINGS_SCREEN = State()
    CHANGE_PROFILE_NAME = State()


