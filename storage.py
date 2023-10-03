
users_data = {}

async def get_data(user_id, key):
    print('Get Data For: ', user_id)
    global users_data
    print('Data: ', users_data)

    if user_id in users_data:
        print('Return Data: ', users_data[user_id][key])
        return users_data[user_id][key]
    else:
        return { 'error': 'no_user' }

async def save_data(user_id, key, val):
    global users_data
    if user_id not in users_data:
        users_data[user_id] = {}
    user_data = users_data[user_id]
    user_data[key] = val
    users_data[user_id] = user_data
    print('Save Data: ', users_data[user_id])
    print('Save Data: ', users_data)