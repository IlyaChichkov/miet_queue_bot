import asyncio
import hashlib

from firebase_admin import db


class Score:
    def __init__(self, added_by, score, room_name, datetime):
        self.added_by = added_by
        self.score = score
        self.room_name = room_name
        self.datetime = datetime

    def generate_identifier(self):
        return f"{self.added_by}_{self.score}_{self.datetime}"

    async def to_dict(self):
        result = {
            'added_by': self.added_by,
            'score': self.score,
            'room_name': self.room_name,
            'datetime': self.datetime
        }
        return result


class UsersScore:
    def __init__(self):
        self.scores: dict[str, list[Score]] = {}

    async def add_score(self, add_to_id, added_by, score, room_name, date):
        s = Score(added_by, score, room_name, date)
        user_score_list = self.scores.get(str(add_to_id), [])
        user_score_list.append(s)
        self.scores[str(add_to_id)] = user_score_list

    async def to_dict(self):
        result = {}
        for key, scores_list in self.scores.items():
            for score in scores_list:
                value = f"{score.added_by}_{score.score}_{score.datetime}"
                result[str(key)] = value
        return result

    async def update_database(self):
        asyncio.create_task(self.__update_database())

    async def __update_database(self):
        rooms_ref = db.reference('/score')
        rooms_ref.set(self.to_dict())