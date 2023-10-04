class Room:
    id = ''
    name = ''
    users_join_code = ''
    moderators_join_code = ''
    is_queue_enabled = False
    is_queue_on_join = True

    admins = []
    moderators = []
    users = []

    def __init__(self, id, name):
        self.id = id
        self.name = name
