from models.room_event import RoomEvent


class RoomJournal:
    def __init__(self):
        self.events = []

    async def add_event(self, event: RoomEvent):
        self.events.append(event)