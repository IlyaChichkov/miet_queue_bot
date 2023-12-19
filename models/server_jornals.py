import logging

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
    journals_ref = db.reference(f'/room_journals/{room_id}')
    compressed_data = journals_ref.get()
    journal.decompress_journal(compressed_data)


update_max_cooldown = 10
update_cooldown = update_max_cooldown
async def update_room_journal(room_id):
    global update_cooldown, update_max_cooldown
    if update_cooldown < 1:

        journal = await get_room_journal(room_id)
        save_data = journal.compress_journal()

        try:
            rooms_ref = db.reference('/room_journals')
            rooms_ref.child(room_id).set(save_data)
        except Exception as ex:
            logging.error(f"Got journal update error! {ex}")
            return

        update_cooldown = update_max_cooldown
    else:
        update_cooldown -= 1