from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from firebase_manager.firebase import is_user_in_queue, get_room_queue_enabled_by_userid, is_user_name_default
from models.server_users import get_user
from models.user import User


async def get_admin_welcome_kb(user: User, is_room_favorite):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(text="Список пользователей",
                                   callback_data='show#users_list'),
        types.InlineKeyboardButton(text="Посмотреть очередь",
                                   callback_data='show#queue_list')
    )

    builder.row(
        types.InlineKeyboardButton(
            text="Принять первого в очереди",
            callback_data='action#queue_pop')
    )
    builder.row(
        types.InlineKeyboardButton(text="Сделать уведомление",
                                   callback_data='action#make_announcement'),
        types.InlineKeyboardButton(text="Настройки комнаты",
                                   callback_data='show#room_settings')
    )

    builder.row(
        types.InlineKeyboardButton(
            text="Выйти",
            callback_data='action#exit_room'
        ),
        types.InlineKeyboardButton(text=f"Избранное {'❤️' if is_room_favorite else '🤍'}",
                                   callback_data='action#favorite'),
        types.InlineKeyboardButton(
            text="Профиль",
            callback_data='show#profile'
        )
    )
    return builder.as_markup(resize_keyboard=True)


async def get_moderator_welcome_kb(user: User, is_room_favorite):
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Список пользователей",
            callback_data='show#users_list'
        ),
        types.InlineKeyboardButton(
            text="Посмотреть очередь",
            callback_data='show#queue_list'
        )
    )

    builder.row(types.InlineKeyboardButton(
        text="Принять первого в очереди",
        callback_data='action#queue_pop'
    ))

    builder.row(
        types.InlineKeyboardButton(
            text="Выйти",
            callback_data='action#exit_room'
        ),
        types.InlineKeyboardButton(text="Избранное",
                                   callback_data='action#favorite'),
        types.InlineKeyboardButton(
            text="Профиль",
            callback_data='show#profile'
        )
    )
    return builder.as_markup(resize_keyboard=True)


async def get_user_welcome_kb(user: User, is_room_favorite):
    user_id = user.user_id
    default_name = await is_user_name_default(user_id)
    builder = InlineKeyboardBuilder()

    result = await is_user_in_queue(user_id)
    user_in_queue = result['result']
    user_place = result['place']
    queue_len = result['len']

    queue_enabled = await get_room_queue_enabled_by_userid(user_id)
    if queue_enabled:
        if not user_in_queue:
            if default_name:
                builder.row(types.InlineKeyboardButton(text="Поменять имя",
                                                       callback_data='action#change_name'))
            else:
                builder.row(types.InlineKeyboardButton(text="Занять место",
                                                       callback_data='action#enter_queue'))

        else:
            if user_place + 1 < queue_len:
                builder.row(
                    types.InlineKeyboardButton(
                        text="Пропустить вперед",
                        callback_data='action#skip_turn'
                    ),
                    types.InlineKeyboardButton(
                        text="Выйти из очереди",
                        callback_data='action#exit_queue'
                    )
                )
            else:
                builder.row(
                    types.InlineKeyboardButton(
                        text="Выйти из очереди",
                        callback_data='action#exit_queue'
                    )
                )

    builder.row(
        types.InlineKeyboardButton(
            text="Выйти",
            callback_data='action#exit_room'
        ),
        types.InlineKeyboardButton(text="Избранное",
                                   callback_data='action#favorite'),
        types.InlineKeyboardButton(
            text="Профиль",
            callback_data='show#profile'
        )
    )
    return builder.as_markup(resize_keyboard=True)


def get_users_list_kb():
    builder = InlineKeyboardBuilder()

    builder.row(
        types.InlineKeyboardButton(
            text="Назад",
            callback_data='show#room_menu'
        )
    )
    return builder.as_markup(resize_keyboard=True)
