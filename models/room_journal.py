import asyncio
import base64
import gzip
import json

from models.room_event import RoomEvent, RoomEventType


class RoomJournal:
    def __init__(self, room_id):
        self.room_id = str(room_id)
        self.events: list[RoomEvent] = []

    async def add_event(self, event: RoomEvent):
        self.events.append(event)
        from models.server_jornals import update_room_journal
        await asyncio.create_task(update_room_journal(self.room_id))

    def compress_journal(self):
        if len(self.events) < 1:
            return None
        room_events_json = json.dumps([event.to_dict() for event in self.events])
        print(room_events_json)
        compressed_data = gzip.compress(room_events_json.encode())
        encoded_data = base64.b64encode(compressed_data).decode('utf-8')

        size_in_bytes = len(encoded_data.encode('utf-8'))
        size_in_kb = size_in_bytes / 1024

        print(f"Размер сохраненного журнала: {size_in_kb} КБ ({size_in_bytes} Б)")
        return encoded_data

    def decompress_journal(self, encoded_data):
        decoded_data = base64.b64decode(encoded_data)
        decompressed_data = gzip.decompress(decoded_data)
        events = [RoomEvent.from_dict(ev_dict) for ev_dict in json.loads(decompressed_data)]
        if events is not None and len(events) > 0:
            self.events = events
        return events

    def to_dict(self):
        events_data = [ev.to_dict() for ev in self.events]
        json_data = json.dumps(events_data, indent=4)
        print(json_data)
        return json_data

    def get_events_by_type(self, event_type: RoomEventType) -> list[RoomEvent]:
        return [ev for ev in self.events if ev.event_type == event_type]