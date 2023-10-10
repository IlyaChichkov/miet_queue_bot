import asyncio
import logging
from firebase_admin import db

from bot_logging import log_database_update
from events.queue_events import user_leave_event


class User:
    def __init__(self, name):
        self.db_key: str = ''
        self.user_id: str = ''
        self.current_role: str = ''
        self.name: str = ''
        self.room: str = ''

        self.name = name

    def set_user_id(self, user_id):
        self.user_id = user_id

    ''' UPDATE ROLE '''
    async def update_role(self, role):
        asyncio.create_task(self.__update_role_task(role))
        asyncio.create_task(self.__update_database())

    async def __update_role_task(self, role):
        self.current_role = role

    ''' UPDATE NAME '''
    async def update_name(self, new_name):
        asyncio.create_task(self.__update_name_task(new_name))
        asyncio.create_task(self.__update_database())

    async def __update_name_task(self, new_name):
        self.name = new_name

    ''' SET ROOM '''
    async def set_room(self, room_id):
        asyncio.create_task(self.__set_room_task(room_id))
        asyncio.create_task(self.__update_database())

    async def __set_room_task(self, room_id):
        self.room = room_id

    ''' LEAVE ROOM '''
    async def leave_room(self):
        await (self.__leave_room_task())
        await (self.__update_database())

    async def __leave_room_task(self):
        self.current_role = ''
        self.room = ''
        await user_leave_event.fire(self.user_id)

    ''' ! UPDATE DATABASE ! '''
    async def __update_database(self):
        if self.user_id == '':
            logging.error('User in cache has empty ID!')
            return
        rooms_ref = db.reference('/users')
        rooms_ref.child(self.db_key).set(self.to_dict())

    def to_dict(self):
        return {
            "tg_id": self.user_id,
            "name": self.name,
            "current_role": self.current_role,
            "room": self.room
        }