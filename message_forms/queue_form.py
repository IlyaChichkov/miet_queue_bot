from firebase import get_queue_users, get_user_room
from keyboards.queue_keyboard import get_queue_kb, get_main_queue_kb, get_admin_queue_kb


def get_noqueue_members_mesg():
    return {"mesg": f"В очереди никого нет 👻",
            "kb": None}



async def get_queue_main_admin():
    return {"mesg": f"✏️Очередь для сдачи:"}


async def get_queue_main():
    return {"mesg": f"✏️Очередь для сдачи:",
            "kb": get_main_queue_kb()}


async def get_queue_list_mesg(user_id):
    room_queue = await get_queue_users(await get_user_room(user_id))
    if room_queue:
        queue_list = ''
        for i, user in enumerate(room_queue):
            queue_list += f'{i + 1}. {user}\n'
        return {"mesg": f"{queue_list}",
                "kb":get_queue_kb()}
    else:
        return {"mesg": f"Пусто 👻",
                "kb": get_queue_kb()}
