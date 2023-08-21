import os
import json
import logging
from templateHandler import TemplateHandler
from common import member_check, hide,disable, DiscordString
from githubWrapper import GitHubWrapper
from canvasWrapper import CanvasWrapper


class StudentHandler(TemplateHandler):
    """
    Integration with GitHub Classroom
    """

    def __init__(self, help_text, response, reply_private, log_level=logging.WARNING):
        super().__init__(help_text, response, reply_private, log_level)
        self.log.debug("StudentHandler initialized")
        self.classroom = GitHubWrapper()
        self.canvas = CanvasWrapper()

    @hide
    @member_check
    async def message_roll_assignment_grading(self, message) -> None:
        self.log.debug("Rolling grading")
        content = message.content.split()
        if len(content) < 2:
            await self.reply(message, "Please specify an assignment")
            return
        assignment = content[1]
        self.log.debug(f"Assignment: {assignment}")
        await self.reply(message, self.classroom.grading_repos_roll(4, assignment))
        self.log.debug("Rolled grading")

    @hide
    @member_check
    @disable
    async def message_students(self, message) -> None:
        """
        List students, defaults to both canvas and github
        Args: [platform] (canvas, github)
        """
        self.log.debug("Listing students")
        students = DiscordString("Students:\n")
        canvas_students = []
        github_students = []
        platform = (
            message.content.split()[1] if len(message.content.split()) > 1 else None
        )
        match platform:
            case "canvas":
                canvas_students = self.canvas.get_students()
            case "github":
                github_students = self.classroom.get_students()
            case _:
                canvas_students = self.canvas.get_students()
                github_students = self.classroom.get_students()

        for student in canvas_students:
            if len(students + student) > 1900:
                await self.reply(message, students.to_code_block(""), private=True)
                students = DiscordString("")
            students += student

        for student in github_students:
            if len(students + student) > 1900:
                await self.reply(message, students.to_code_block(""), private=True)
                students = DiscordString("")
            students += student

        await self.reply(message, students.to_code_block(""), private=True)
        self.log.debug("Listed students")

    @hide
    @member_check
    async def message_roll_undo(self, message) -> None:
        self.log.debug("Undoing roll")
        content = message.content.split()
        if len(content) < 2:
            await self.reply(
                message,
                self.classroom.assignments_previous_get_all(),
            )
            return
        assignment = content[1]
        self.classroom.grading_remove(assignment)
        self.log.debug("Roll undone")

    @hide
    @member_check
    async def message_roll_undo_all(self, message) -> None:
        self.log.debug("Undoing all rolls")
        self.classroom.grading_clear()
        self.log.debug("All rolls undone")

    async def message_next_deadline(self, message, _) -> None:
        """
        Get the next assignment, deadline and remaining time
        """
        self.log.debug("Getting next deadline")
        next_deadline = self.classroom.next_deadline()
        time_until_deadline = self.classroom.time_until_next_deadline()
        reply = DiscordString("Next deadline:\n")
        reply += DiscordString(
            f"{next_deadline.name} is due [{next_deadline.date}], in {time_until_deadline}"
        ).to_code_block()
        await self.reply(message, reply)
        self.log.debug("Got next deadline")

    async def message_list_ta(self, message, _) -> None:
        """
        List TAs in the course
        """
        self.log.debug("Listing TAs")
        reply = DiscordString("TAs:\n")
        for ta in self.classroom.ta_get_all():
            reply += DiscordString(f"{ta.name} : {ta.email}\n")
        await self.reply(message, reply)
        self.log.debug("Listed TAs")
