import json
import logging
from typing import List
from firebase_admin import db

server_passwords: List[str] = []


async def load_passwords():
    logging.info('Loading create room codes from database.')
    pass_ref = db.reference(f'/root_passwords')
    passwords: List[str] = pass_ref.get()
    for root_password in passwords:
        server_passwords.append(root_password)


async def check_password(input_code):
    logging.info(f'Checking input create room code: {input_code}')
    if input_code in server_passwords:
        return True

    await load_passwords()

    if input_code in server_passwords:
        return True
    return False