import datetime
import enum


class RoomEventType:
    CREATE = enum.auto()
    DELETE = enum.auto()

    NOTE_CREATED = enum.auto()

    USER_JOIN = enum.auto()
    USER_LEFT = enum.auto()
    USER_ASSIGNED = enum.auto()
    USER_ENTER_QUEUE = enum.auto()
    USER_LEAVE_QUEUE = enum.auto()


class RoomEvent:
    def __init__(self, event_type: RoomEventType, event_data: str):
        self.event_type: RoomEventType = event_type
        self.event_data = event_data
        self.datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')