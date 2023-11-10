import asyncio
import logging
import re

from firebase_admin import db
from events.queue_events import user_leave_event, update_queue_event, user_joined_queue_event


class User:
    def __init__(self, name):
        self.db_key: str = ''
        self.user_id: str = ''
        self.current_role: str = ''
        self.name: str = ''
        self.room: str = ''
        self.global_role = ''
        self.owned_rooms = []

        self.has_default_name = True

        # Cache only
        self.assigned_user_id = ''

        self.name = name

    async def check_global_role(self):
        global_roles_ref = db.reference('/special_roles')
        global_roles = global_roles_ref.get()
        if str(self.user_id) in list(global_roles.keys()):
            self.global_role = global_roles[str(self.user_id)]
        else:
            self.global_role = None

    async def get_global_role(self):
        if self.global_role == '':
            await self.check_global_role()

        return self.global_role

    def set_user_id(self, user_id):
        self.user_id = user_id

    ''' UPDATE ROLE '''
    async def update_role(self, role):
        self.__update_role_task(role)
        asyncio.create_task(self.__update_database())

    def __update_role_task(self, role):
        self.current_role = role

    ''' UPDATE NAME '''

    def default_name_regular(self, input_text):
        pattern = re.compile(r"User_[0-9]+", re.IGNORECASE)
        return pattern.match(input_text)

    def check_has_default_name(self):
        self.has_default_name = self.default_name_regular(self.name)
        return self.has_default_name

    async def update_name(self, new_name):
        self.__update_name_task(new_name)
        asyncio.create_task(self.__update_database())

    def __update_name_task(self, new_name):
        self.name = new_name
        self.check_has_default_name()

    ''' ADD OWNED ROOM '''
    async def add_owned_room(self, room_id):
        asyncio.create_task(self.__add_owned_room_task(room_id))
        asyncio.create_task(self.__update_database())

    async def __add_owned_room_task(self, room_id):
        self.owned_rooms.append(room_id)

    ''' REMOVE OWNED ROOM '''
    async def remove_owned_room(self, room_id):
        asyncio.create_task(self.__remove_owned_room_task(room_id))
        asyncio.create_task(self.__update_database())

    async def __remove_owned_room_task(self, room_id):
        self.owned_rooms.remove(room_id)

    def is_owner_of_room(self, room_id):
        return str(room_id) in self.owned_rooms

    ''' SET ROOM '''
    async def set_room(self, room_id):
        self.__set_room_task(room_id)
        asyncio.create_task(self.__update_database())

    def __set_room_task(self, room_id):
        logging.info(f"Set USER_{self.user_id} room_id to ROOM_{room_id}")
        self.room = room_id

    ''' EXIT QUEUE '''
    async def exit_queue(self):
        await (self.__exit_queue_task())
        await (self.__update_database())

    async def __exit_queue_task(self):
        from models.server_rooms import get_room
        room = await get_room(self.room)
        if room and self.user_id in room.queue:
            await room.queue_remove(self.user_id)
            await update_queue_event.fire(room.room_id, self.user_id)
        return True

    ''' SET QUEUE ENTER '''
    async def set_queue_enter(self, room, place):
        asyncio.create_task(user_joined_queue_event.fire(room, self.user_id, place + 1, False))
        asyncio.create_task(self.__update_database())

    ''' ENTER QUEUE '''
    async def enter_queue(self, notify_mod: bool = True):
        queue_place = await (self.__enter_queue_task(notify_mod))
        asyncio.create_task(self.__update_database())
        # await (self.__update_database())
        return queue_place

    async def __enter_queue_task(self, notify_mod: bool = True):
        from models.server_rooms import get_room
        room = await get_room(self.room)
        if room:
            if room and self.user_id in room.queue:
                return -1
            place = len(room.queue) + 1
            await room.queue_add(self.user_id)
            asyncio.create_task(user_joined_queue_event.fire(room, self.user_id, place, notify_mod))
            await update_queue_event.fire(room.room_id, self.user_id, notify=False)
            return place
        return None

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
            "room": self.room,
            "own_rooms": self.owned_rooms
        }