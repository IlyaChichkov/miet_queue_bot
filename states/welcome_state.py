from aiogram.fsm.state import StatesGroup, State


class WelcomeState(StatesGroup):
    WELCOME_SCREEN = State()
    CREATE_ROOM_SCREEN = State()
    JOIN_ROOM_SCREEN = State()
