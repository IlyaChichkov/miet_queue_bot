import asyncio
import base64
import gzip
import json
import logging

from firebase_admin import db

from bot_conf.bot_logging import log_database_update
from events.queue_events import update_room_event, update_queue_event, users_notify_queue_changed_event, \
    users_notify_queue_skipped, user_leave_room_event
from models.note import StudyNote
from models.server_users import get_user
from models.user import User
from roles.user_roles_enum import UserRoles
from utils import generate_password, generate_code


class Room:
    def __init__(self, name, admin_id = None):
        # Default values
        self.room_id = ''
        self.name = ''
        self.users_join_code = ''
        self.moderators_join_code = ''
        self.is_queue_enabled = False
        self.is_queue_on_join = False
        self.admins = []
        self.moderators = []
        self.users = []

        self.queue = []
        self.banned = []

        self.study_notes: list[StudyNote] = []

        # Cache only

        # Set values
        self.name = name
        if admin_id:
            self.admins.append(admin_id)
        self.moderators_join_code = generate_password(7)
        self.users_join_code = generate_code(4)

    def role_to_list(self, role):
        t = {
            UserRoles.User: self.users,
            UserRoles.Moderator: self.moderators,
            UserRoles.Admin: self.admins
        }
        return t[role]

    def set_room_id(self, room_id):
        self.room_id = room_id

    ''' BAN USER '''
    async def ban_user(self, initiator_id, user_id):
        user_id = str(user_id)
        print('initiator_id:', initiator_id)
        print('self.admins:', self.admins)
        print('Is admin:', int(initiator_id) in self.admins)
        print('not banned:', user_id not in self.banned)
        if user_id not in self.banned and int(initiator_id) in self.admins:
            self.banned.append(user_id)
            logging.info(f'USER_{user_id} was banned in ROOM_{self.room_id} by USER_{initiator_id}')
            await update_room_event.fire(self)
            return True
        return False

    ''' REMOVE BAN '''
    async def remove_ban(self, initiator_id, user_id):
        user_id = str(user_id)
        if user_id in self.banned and int(initiator_id) in self.admins:
            self.banned.remove(user_id)
            logging.info(f'USER_{user_id} ban was removed in ROOM_{self.room_id} by USER_{initiator_id}')
            await update_room_event.fire(self)
            return True
        return False


    ''' CHECK BAN '''
    async def check_banned(self, user_id):
        user_id = str(user_id)
        if user_id in self.banned:
            return True
        return False


    ''' GET USER GROUP '''
    def get_user_group(self, user_id) -> str:
        if user_id in self.users:
            return 'users'
        if user_id in self.moderators:
            return 'moderators'
        if user_id in self.admins:
            return 'admins'
        return None

    ''' GET USER ROLE '''
    def get_user_role(self, user_id) -> UserRoles:
        if user_id in self.users:
            return UserRoles.User
        if user_id in self.moderators:
            return UserRoles.Moderator
        if user_id in self.admins:
            return UserRoles.Admin
        return None

    ''' AUTO QUEUE ON JOIN '''
    async def switch_autoqueue_enabled(self):
        await (self.__switch_autoqueue_enabled_task())
        await asyncio.create_task(update_room_event.fire(self))
        return self.is_queue_on_join

    async def __switch_autoqueue_enabled_task(self):
        self.is_queue_on_join = not self.is_queue_on_join

    ''' QUEUE ENABLE '''
    async def switch_queue_enabled(self):
        await (self.__switch_queue_enabled_task())
        await asyncio.create_task(update_room_event.fire(self))

    async def __switch_queue_enabled_task(self):
        self.is_queue_enabled = not self.is_queue_enabled
        if not self.is_queue_enabled:
            await self.queue_clear()

    ''' QUEUE POP '''
    async def queue_pop(self, user_id):
        role = self.get_user_role(user_id)
        if role is UserRoles.User:
            return None
        user_pop_id = await self.__queue_pop_task()
        await asyncio.create_task(update_room_event.fire(self))
        return user_pop_id

    async def __queue_pop_task(self):
        if len(self.queue) > 0:
            try:
                users_notify = self.queue[1:]
                if users_notify:
                    await users_notify_queue_changed_event.fire(users_notify, 0)
            except Exception as ex:
                logging.error(f'Failed to fire event of queue update to users: {ex}')

            returned_user = self.queue.pop(0)
            await update_queue_event.fire(self.room_id, returned_user)
            return returned_user
        return None

    ''' QUEUE SET '''
    async def firebase_update_queue(self):
        rooms_ref = db.reference(f'/rooms')
        rooms_ref.update({
            f'{self.room_id}/queue': self.queue
        })

    ''' QUEUE SET '''
    async def set_queue(self, queue_list):
        self.queue = queue_list
        await self.firebase_update_queue()

    ''' QUEUE ADD '''
    async def queue_add(self, user_id):
        await (self.__queue_add_task(user_id))
        await update_room_event.fire(self)

    async def __queue_add_task(self, user_id):
        if user_id not in self.queue:
            self.queue.append(user_id)

    ''' QUEUE REMOVE '''
    async def queue_remove(self, user_id):
        await self.queue_remove_task(int(user_id))
        await asyncio.create_task(update_room_event.fire(self))
        await asyncio.create_task(update_queue_event.fire(self.room_id, user_id))

    async def queue_remove_task(self, user_id):
        if user_id not in self.queue:
            return

        try:
            user_index = self.queue.index(user_id)
            if len(self.queue) > user_index + 1:
                users_notify = self.queue[user_index + 1:]
                logging.error(f"QUEUE: {self.queue} USERS NOTIFY: {users_notify}")
                if len(users_notify) > 0:
                    await users_notify_queue_changed_event.fire(users_notify, user_index)
        except Exception as ex:
            logging.error(f'Queue remove task notification failed. Error: {ex}')

        self.queue.remove(user_id)

    ''' QUEUE CLEAR '''
    async def queue_clear(self):
        # await (self.queue_clear_task())
        self.queue.clear()
        await asyncio.create_task(update_queue_event.fire(self.room_id, None))
        await asyncio.create_task(update_room_event.fire(self))

    async def queue_clear_task(self):
        self.queue.clear()

    ''' ADD USER '''
    async def add_user(self, user_id, role: UserRoles):
        await (self.__add_user_task(user_id, role))
        await update_room_event.fire(self)
        # await (self.__update_users())
        # asyncio.create_task(self.__add_user_task(user_id, role))
        # asyncio.create_task(self.__update_database())

    async def __add_user_task(self, user_id, role: UserRoles):
        users_list = self.role_to_list(role)
        if user_id not in users_list:
            users_list.append(user_id)

    ''' REMOVE USER '''
    async def remove_user(self, user_id):
        await self.__remove_user_task(user_id)
        await self.__update_database()

    async def __remove_user_task(self, user_id):
        # if user_id not in self.admins:
        user_id = int(user_id)
        if user_id in self.queue:
            self.queue.remove(user_id)
            await asyncio.create_task(update_queue_event.fire(self.room_id, user_id))
        self.role_to_list(self.get_user_role(user_id)).remove(user_id)

        await asyncio.create_task(user_leave_room_event.fire(self.room_id, user_id))
        user: User = await get_user(user_id)
        await asyncio.create_task(user.leave_room())

    ''' UPDATE NAME '''
    async def update_name(self, new_name):
        await (self.__update_name_task(new_name))
        await update_room_event.fire(self)

    async def __update_name_task(self, new_name):
        self.name = new_name
    ''' USER SKIP QUEUE PLACE '''
    async def skip_queue_place(self, user: User):
        user_id = user.user_id
        if user_id in self.queue:
            user_index = self.queue.index(user_id)
            pass_user_id = self.queue[user_index + 1] if user_index + 1 < len(self.queue) else None
            if pass_user_id:
                self.queue[user_index] = pass_user_id
                self.queue[user_index + 1] = user_id
                await asyncio.create_task(update_room_event.fire(self))
                await asyncio.create_task(update_queue_event.fire(self.room_id, None))
                await users_notify_queue_skipped.fire(pass_user_id, user.name, user_index + 1)
                return pass_user_id
        return None


    ''' GET USERS LIST '''
    def get_users_list(self):
        users = []

        for user_id in self.users:
            users.append(user_id)

        for user_id in self.moderators:
            users.append(user_id)

        for user_id in self.admins:
            users.append(user_id)

        return users

    ''' CHECK IF USER IN ADMINS LIST '''
    async def is_user_admin(self, user_id):
        role: UserRoles = self.get_user_role(user_id)
        if role != UserRoles.Admin:
            return False
        return True

    ''' GET USERS COUNT '''
    def get_users_count(self):
        return len(self.get_users_list())

    ''' DELETE ROOM '''
    async def delete(self):
        logging.info(f'Deleting room, id: {self.room_id}, name: {self.name}')
        await self.__delete_task()
        await self.__delete_room()

    async def __delete_task(self):
        for user_id in self.users:
            user: User = await get_user(user_id)
            await user.leave_room()

        for user_id in self.moderators:
            user: User = await get_user(user_id)
            await user.leave_room()

        for user_id in self.admins:
            user: User = await get_user(user_id)
            await user.leave_room()

    ''' ! UPDATE DATABASE ! '''
    async def __update_database(self):
        if self.room_id == '':
            logging.error('Room in cache has empty ID!')
            return
        log_database_update('>>> UPDATE DATABASE (Room) <<<')
        log_database_update(self.to_dict())
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(self.room_id).set(self.to_dict())

    ''' DELETE ROOM '''
    async def __delete_room(self):
        if self.room_id == '':
            logging.error('Room in cache has empty ID!')
            return
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(self.room_id).delete()

    ''' UPDATE USERS '''
    async def __update_users(self):
        if self.room_id == '':
            logging.error('Room in cache has empty ID!')
            return
        log_database_update('>>> UPDATE USERS (Room) <<<')
        rooms_ref = db.reference('/rooms')
        rooms_ref.child(self.room_id).child('users').update(self.users)

    def compress_notes(self):
        if len(self.study_notes) < 1:
            return None
        study_notes_json = json.dumps([note.to_dict() for note in self.study_notes])
        compressed_data = gzip.compress(study_notes_json.encode())
        encoded_data = base64.b64encode(compressed_data).decode('utf-8')
        return encoded_data

    def decompress_notes(self, encoded_data):
        if encoded_data is not None:
            decoded_data = base64.b64decode(encoded_data)
            decompressed_data = gzip.decompress(decoded_data)
            study_notes = [StudyNote.from_dict(note_dict) for note_dict in json.loads(decompressed_data)]
            return study_notes
        return None


    def to_dict(self):
        return {
            "name": self.name,
            "admins": self.admins,
            "moderators": self.moderators,
            "users": self.users,
            "queue": self.queue,
            "queue_enabled": self.is_queue_enabled,
            "queue_on_join": self.is_queue_on_join,
            "join_code": self.users_join_code,
            "mod_password": self.moderators_join_code,
            "banned": self.banned,
            "notes": self.compress_notes()
        }

    def to_log(self):
        return {
            "room_id": self.room_id,
            "name": self.name,
            "admins": self.admins,
            "moderators": self.moderators,
            "users": self.users,
            "queue": self.queue,
            "queue_enabled": self.is_queue_enabled,
            "queue_on_join": self.is_queue_on_join,
            "join_code": self.users_join_code,
            "mod_password": self.moderators_join_code,
            "study_notes": [note.to_dict() for note in self.study_notes],
            "banned": self.banned
        }
