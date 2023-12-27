import logging
import sys

from firebase_admin import db

from models.room_journal import RoomJournal

room_journals: dict[str, RoomJournal] = {}


async def get_room_journal(room_id) -> RoomJournal:
    journal = None
    if room_id in room_journals:
        journal = room_journals[room_id]
    else:
        journal = await create_room_journal(room_id)
        await load_from_database(room_id, journal)

    return journal


async def add_room_journal(room_id, journal):
    room_journals[room_id] = journal


async def create_room_journal(room_id):
    journal = RoomJournal(room_id)
    await add_room_journal(room_id, journal)
    return journal


async def load_from_database(room_id, journal):
    file_name = f"./room_journals/{room_id}.txt"

    with open(file_name, 'r', encoding='utf-8') as file:
        compressed_data = file.read()

    #journals_ref = db.reference(f'/room_journals/{room_id}')
    #compressed_data = journals_ref.get()

    # Размер строки в байтах
    size_in_bytes = sys.getsizeof(compressed_data)

    # Размер строки в килобайтах
    size_in_kb = size_in_bytes / 1024

    print(f"Загрузка журнала\nРазмер строки в байтах: {size_in_bytes} байт")
    print(f"Размер строки в килобайтах: {size_in_kb:.2f} КБ")

    journal.decompress_journal(compressed_data)


update_cooldown = 1
async def update_room_journal(room_id):
    from firebase_manager.firebase import get_db_data
    update_max_cooldown: int = int(await get_db_data("journal_update_cooldown"))
    global update_cooldown
    if update_cooldown < 1:

        journal = await get_room_journal(room_id)
        save_data = journal.compress_journal()

        try:

            # Размер строки в байтах
            size_in_bytes = sys.getsizeof(save_data)

            # Размер строки в килобайтах
            size_in_kb = size_in_bytes / 1024

            print(f"Загрузка журнала\nРазмер строки в байтах: {size_in_bytes} байт")
            print(f"Размер строки в килобайтах: {size_in_kb:.2f} КБ")

            file_name = f"./room_journals/{room_id}.txt"

            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(save_data)

            # rooms_ref = db.reference('/room_journals')
            # rooms_ref.child(room_id).set(save_data)
        except Exception as ex:
            logging.error(f"Got journal update error! {ex}")
            return

        update_cooldown = update_max_cooldown
    else:
        update_cooldown -= 1