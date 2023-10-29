from unittest.mock import AsyncMock
import pytest
from aiogram.types import FSInputFile

from handlers.main_screens import start_command
from message_forms.welcome_form import get_welcome_form
import firebase

@pytest.mark.asyncio
async def start_command_handler():
    message = AsyncMock()
    start_image = FSInputFile("assets/images/welcome.png")
    form_message, form_kb = await get_welcome_form(message.from_user.first_name, message.from_user.id)
    await start_command(message)
    message.answer.assert_called_with(start_image, form_message, reply_markup=form_kb)