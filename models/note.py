from datetime import datetime

class StudyNote:
    def __init__(self, teacher, pupil, text):
        # Default values
        self.teacher = teacher
        self.pupil = pupil
        self.text = text
        self.made_time = datetime.now()

    def to_dict(self):
        return {
            "teacher": self.teacher,
            "pupil": self.pupil,
            "text": self.text,
            "time": self.made_time
        }


def __export_notes_csv(notes: list[StudyNote]):
    file_text = 'Преподаватель,Студент,Заметка,Время\n'
    for note in notes:
        file_text += f'{note.teacher},{note.pupil},{note.text},{note.made_time}\n'

    return file_text


def __export_notes_message(notes: list[StudyNote]):
    file_text = ''
    for i, note in enumerate(notes):
        file_text += f'{i+1}. Студент <b>{note.pupil}</b>\n{note.text}, <i>{note.made_time.date()} {note.made_time.hour}:{note.made_time.minute}</i>\n'

    if file_text == '':
        file_text = 'Заметок нет'
    return file_text


def export_study_notes(notes: list[StudyNote], export_type: str):
    export_type_dict = {
        'csv': __export_notes_csv,
        'message': __export_notes_message
    }
    return export_type_dict[export_type](notes)