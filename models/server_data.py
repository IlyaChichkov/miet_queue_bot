from models.room import Room

server_rooms = []

async def server_add_room(room_id, room_name):
    server_rooms.append(Room(room_id, room_name))