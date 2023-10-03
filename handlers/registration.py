import random
import string

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from firebase import is_login_exists, auth
import json

from aiogram.utils.keyboard import InlineKeyboardBuilder

from storage import save_data

router = Router()

auth_data = {
    'login': '',
    'password': ''
}

class RegistrationState(StatesGroup):
    CHOOSE_ROLE = State()
    MODERATOR_LOGIN = State()
    MODERATOR_PASSWORD = State()
    USER_LOGIN = State()
    USER_PASSWORD = State()


# Generate a random nickname for new users
def generate_random_nickname():
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(8))


# Start command handler
@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = [
        [
            types.KeyboardButton(text="Преподаватель", callback_data="login_moderator"),
            types.KeyboardButton(text="Студент", callback_data="login_user")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите тип учетной записи"
    )
    await message.answer("Добро пожаловать в QueueBot! Пожалуйста выберите тип учетной записи:", reply_markup=keyboard)
    await state.set_state(RegistrationState.CHOOSE_ROLE)


@router.message(F.text.lower() == "преподаватель")
async def set_state_login_moderator(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста введите ваш логин:")
    await state.set_state(RegistrationState.MODERATOR_LOGIN)


@router.message(RegistrationState.MODERATOR_LOGIN)
async def login_moderator(message: types.Message, state: FSMContext):
    auth_data['login'] = message.text
    await message.answer("Пожалуйста введите ваш пароль:")
    await state.set_state(RegistrationState.MODERATOR_PASSWORD)

@router.message(RegistrationState.MODERATOR_PASSWORD)
async def password_moderator(message: types.Message, state: FSMContext):
    auth_data['password'] = message.text

    user = auth(auth_data)

    if user:
        await save_data(message.from_user.id, 'user', user)
        await state.clear()
    else:
        await message.answer("Данные введены неверно.")
        await message.answer("Пожалуйста введите ваш логин:")
        await state.set_state(RegistrationState.MODERATOR_LOGIN)


@router.message(Command("state"))
async def get_all_questions(message: Message, state: FSMContext):
    current_state = await state.get_state()
    await message.answer(f"State: {current_state}")


@router.message(Command("cancel"))
async def get_all_questions(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено",
        reply_markup=ReplyKeyboardRemove()
    )