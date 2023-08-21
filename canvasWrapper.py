import os
import json
import canvasapi
from common import DiscordString


class CanvasWrapper:
    def __init__(self):
        self.canvas_handler = canvasapi.Canvas(
            os.environ["CANVAS_URL"], os.environ["CANVAS_TOKEN"]
        )
        self.course = self.canvas_handler.get_course(os.environ["CANVAS_COURSE_ID"])

    def get_students(self):
        students = []
        message = DiscordString("Canvas students:\n")
        for student in self.course.get_users(enrollment_type="student"):
            student = student.get_profile()
            id = (
                student["login_id"],
            )
            message += DiscordString(f"{id}\n")
            if len(message) > 1900:
                students.append(message)
                message = DiscordString("")
        students.append(message)
        return students
