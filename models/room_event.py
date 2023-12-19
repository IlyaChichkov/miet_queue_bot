import datetime
import enum
import json


class RoomEventType(enum.Enum):
    # DO NOT CHANGE ORDER
    CREATE = enum.auto()
    DELETE = enum.auto()

    NOTE_CREATED = enum.auto()

    USER_JOIN = enum.auto()
    USER_LEFT = enum.auto()
    USER_ASSIGNED = enum.auto()
    USER_ENTER_QUEUE = enum.auto()
    USER_LEAVE_QUEUE = enum.auto()


class RoomEvent:
    def __init__(self, event_type: RoomEventType, event_data):
        self.event_type: RoomEventType = event_type
        self.event_data = event_data
        self.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            "event_type": self.event_type.value,
            "event_data": self.event_data,
            "datetime": self.datetime
        }

    @staticmethod
    def from_dict(event_dict):
        r_event = RoomEvent(RoomEventType(event_dict['event_type']), event_dict['event_data'])
        r_event.datetime = event_dict['datetime']
        return r_event

    @staticmethod
    def CreateRoom(created_by):
        event_data = {
            "created_by": created_by
        }
        return RoomEvent(RoomEventType.CREATE, event_data)

    @staticmethod
    def DeleteRoom(deleted_by):
        event_data = {
            "deleted_by": deleted_by
        }
        return RoomEvent(RoomEventType.DELETE, event_data)

    @staticmethod
    def NoteCreated(note_id):
        event_data = {
            "note_id": note_id
        }
        return RoomEvent(RoomEventType.NOTE_CREATED, event_data)

    @staticmethod
    def UserJoin(user_id):
        event_data = {
            "user_id": user_id
        }
        return RoomEvent(RoomEventType.USER_JOIN, event_data)

    @staticmethod
    def UserLeft(user_id):
        event_data = {
            "user_id": user_id
        }
        return RoomEvent(RoomEventType.USER_LEFT, event_data)

    @staticmethod
    def UserAssigned(user_id):
        event_data = {
            "user_id": user_id
        }
        return RoomEvent(RoomEventType.USER_ASSIGNED, event_data)

    @staticmethod
    def UserEnterQueue(user_id):
        event_data = {
            "user_id": user_id
        }
        return RoomEvent(RoomEventType.USER_ENTER_QUEUE, event_data)

    @staticmethod
    def UserLeaveQueue(user_id):
        event_data = {
            "user_id": user_id
        }
        return RoomEvent(RoomEventType.USER_LEAVE_QUEUE, event_data)