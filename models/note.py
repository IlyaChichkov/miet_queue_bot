import json
import logging
from datetime import datetime

class StudyNote:
    def __init__(self, room_id, room_name, teacher_id, teacher, pupil, text):
        # Default values
        self.room_id = room_id
        self.room_name = room_name
        self.teacher_id = teacher_id
        self.teacher = teacher
        self.pupil = pupil
        self.text = text
        self.made_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "teacher": self.teacher,
            "pupil": self.pupil,
            "text": self.text,
            "time": self.made_time
        }


def __export_notes_json(notes: list[StudyNote]):
    notes_data = [
        {
            "Комната": note.room_name,
            "Преподаватель": note.teacher,
            "Студент": note.pupil,
            "Заметка": note.text,
            "Время": note.made_time
        }
        for note in notes
    ]

    file_text = json.dumps({"notes": notes_data}, ensure_ascii=False, indent=2)
    logging.info(f'Export notes in JSON format:\n{file_text}')
    return file_text


def __export_notes_csv(notes: list[StudyNote]):
    file_text = 'Комната,Преподаватель,Студент,Заметка,Время\n'
    for note in notes:
        file_text += f'{note.room_name},{note.teacher},{note.pupil},{note.text},{note.made_time}\n'

    logging.info(f'Export notes in CSV format:\n{file_text}')
    return file_text


def __export_notes_message(notes: list[StudyNote]):
    file_text = ''
    for i, note in enumerate(notes):
        file_text += f'{i+1}. Комната «{note.room_name}» - Студент <b>{note.pupil}</b>\n{note.text}, <i>{note.made_time}</i>\n'

    if file_text == '':
        file_text = 'Заметок нет'
    return file_text


def export_study_notes(notes: list[StudyNote], export_type: str):
    export_type_dict = {
        'csv': __export_notes_csv,
        'message': __export_notes_message,
        'json': __export_notes_json
    }
    return export_type_dict[export_type](notes)


def export_study_notes_by_user(notes: list[StudyNote], user_id):
    file_text = ''
    for i, note in enumerate(notes):
        if note.teacher_id == user_id:
            file_text += f'{i+1}. Комната «{note.room_name}» - Студент <b>{note.pupil}</b>\n✏️ {note.text}, <i>{note.made_time}</i>\n'

    if file_text == '':
        file_text = 'Заметок нет'
    return file_text