import datetime
import json
import logging

from aiogram.types import FSInputFile
from firebase_admin import db
from pathlib import Path

from models.score import Score
from models.server_passwords import server_passwords
from models.server_rooms import server_rooms, load_room_from_json, add_room
from models.server_score import usersScore
from models.server_users import server_users, load_user_from_json, add_user, get_user
from models.user import User


async def get_cache_file(message):
    '''
    Отправка файла с кешем сервера
    '''
    message_text = await show_cache()
    Path("./temp_files").mkdir(parents=True, exist_ok=True)
    file_path = './temp_files/server_cache.txt'
    with open(file_path, 'w+') as file:
        file.write(message_text)

    send_file = FSInputFile(file_path, f'Кэш_сервера_{datetime.datetime.now().time().strftime("%H_%M_%S")}.txt')
    await message.answer_document(send_file)
    Path(file_path).unlink()
    await message.answer("Готово!")


async def show_cache():
    '''
    Составление текста с кешем для отправки или записи в файл
    '''
    message = 'Score:\n'
    num = 0
    for user_id, scores_list in usersScore.scores.items():
        score_dicts = [await score.to_dict() for score in scores_list]
        r = json.dumps({user_id: score_dicts})
        loaded_r = json.loads(r)
        message += f' {num+1}) {json.dumps(loaded_r, indent=2, ensure_ascii=False)}\n'
        num = num + 1

    message += 'Rooms:\n'
    for num, room in enumerate(server_rooms):
        r = json.dumps(room.to_log())
        loaded_r = json.loads(r)
        message += f' {num+1}) {json.dumps(loaded_r, indent=2, ensure_ascii=False)}\n'

    message += 'Users:\n'
    for num, user in enumerate(server_users):
        r = json.dumps(user.to_dict())
        loaded_r = json.loads(r)
        message += f' {num+1}) {json.dumps(loaded_r, indent=2, ensure_ascii=False)}\n'

    return message


async def __load_rooms():
    '''
    Загрузка данных комнта на сервер из БД
    '''
    logging.info('Loading rooms data from Firebase and caching it')
    try:
        rooms_ref = db.reference(f'/rooms').get()
        if rooms_ref is not None:
            rooms_list = list(rooms_ref.items())
            for room in rooms_list:
                room_key, room_data = room
                loaded_room = load_room_from_json(room_key, room_data)
                await add_room(loaded_room)
    except Exception as ex:
        logging.error(f'Failed to load rooms data from Firebase: {ex}')
    finally:
        logging.info('Caching completed!')


async def __load_users():
    '''
    Загрузка данных пользователей на сервер из БД
    '''
    logging.info('Loading users data from Firebase and caching it')
    try:
        users_ref = db.reference(f'/users').get()
        if users_ref is not None:
            users_list = list(users_ref.items())
            for user in users_list:
                user_key, user_data = user
                loaded_user = load_user_from_json(user_key, user_data)
                await add_user(loaded_user)
    except Exception as ex:
        logging.error(f'Failed to load users data from Firebase: {ex}')
    finally:
        logging.info('Caching completed!')


async def add_teacher(teacher_id):
    '''
    Добавление специальной роли "преподаватель" пользователю
    '''
    global_roles_ref = db.reference('/special_roles')
    global_roles = global_roles_ref.get()
    global_roles.update({teacher_id: 2})
    global_roles_ref.set(global_roles)
    user: User = await get_user(teacher_id)
    await user.check_global_role()


async def update_cache():
    await delete_cache()
    await load_cache()


async def delete_cache():
    server_rooms.clear()
    server_users.clear()
    server_passwords.clear()


async def load_cache():
    print('Load cache')
    await __load_rooms()
    await __load_users()
