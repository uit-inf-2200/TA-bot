import os
import json
import random
import github
from datetime import datetime, timedelta
from dateutil.tz import tzlocal
from typing import TypeVar
from github import Github, Auth
from common import DiscordString


class Deadline:
    def __init__(self, name: str, date: datetime) -> None:
        self.name = name
        self.date = date


class TimeToDeadline:
    def __init__(self, days: int, hours: int, minutes: int, seconds: int) -> None:
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def from_timedelta(timedelta: timedelta):
        days = timedelta.days
        hours, remainder = divmod(timedelta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return TimeToDeadline(days, hours, minutes, seconds)

    def to_timedelta(self) -> timedelta:
        return datetime.timedelta(
            days=self.days, hours=self.hours, minutes=self.minutes, seconds=self.seconds
        )

    def __str__(self) -> str:
        return f"{self.days}d {self.hours}h {self.minutes}m {self.seconds}s"


class GitHubWrapper:
    def __init__(self) -> None:
        self.github = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))
        self.organization = self.github.get_organization(
            os.getenv("GITHUB_ORGANIZATION")
        )
        self.grading_load()

    def grading_load(self) -> None:
        try:
            with open(os.getenv("GRADING_FILE"), "r") as f:
                self.assignments_previous = json.load(f)
        except FileNotFoundError:
            self.assignments_previous = {}

    def grading_store(self) -> None:
        with open(os.getenv("GRADING_FILE"), "w") as f:
            json.dump(self.assignments_previous, f)

    def grading_add(self, assignment: str, grading_list: DiscordString) -> None:
        self.assignments_previous[assignment] = grading_list
        self.grading_store()

    def grading_clear(self) -> None:
        self.assignments_previous = {}
        self.grading_store()

    def grading_remove(self, assignment: str) -> None:
        try:
            del self.assignments_previous[assignment]
            self.grading_store()
        except KeyError:
            pass

    def repo_template_get_all(self) -> list[github.Repository.Repository]:
        """
        Get all template repos for org.
        """
        reply = DiscordString("Templates:\n")
        for r in self.ta_repo_get_all():
            if r.is_template:
                reply += DiscordString(f"{r.name} : <{r.html_url}>\n")

        return [r for r in self.team_get("TA").get_repos() if r.is_template]

    def assignments_previous_get_all(self) -> DiscordString:
        """
        Get name of all previous assignments.
        """
        if not self.assignments_previous:
            return DiscordString("No previous assignments")
        reply = DiscordString("")
        for assignment in self.assignments_previous:
            reply += DiscordString(f"{assignment}\n")
        return reply

    def assignment_get_deadline(self, assignment: str) -> str:
        pass

    def team_get(self, name: str) -> github.Team.Team:
        """
        Get a team by name.
        """
        return [t for t in self.organization.get_teams() if t.name == name][0]

    def ta_get_all(self) -> list[github.NamedUser.NamedUser]:
        """
        Get all TAs in the organization.
        """
        return [
            m
            for t in self.organization.get_teams()
            if t.name == "TA"
            for m in t.get_members()
        ]

    def ta_get(self, username: str) -> github.NamedUser.NamedUser:
        """
        Get a TA by username.
        """
        return [m for m in self.ta_get_all() if m.login == username][0]

    def ta_repo_get_all(self) -> list[github.Repository.Repository]:
        """
        Get all repos for the TA team.
        """
        return [r for r in self.team_get("TA").get_repos()]

    def student_get(self, username: str) -> github.NamedUser.NamedUser:
        """
        Get a student by username.
        """
        return [m for m in self.organization.get_members() if m.login == username][0]

    def get_students(self) -> list[DiscordString]:
        """
        Get all students in the organization.
        """
        students = []
        messsage = DiscordString("Github students:\n")
        for m in self.organization.get_members():
            name = m.login
            email = m.email
            messsage += DiscordString(f"{name} : {email}\n")
            if len(messsage) > 1900:
                students.append(messsage)
                messsage = DiscordString("")
        students.append(messsage)
        return students

    def student_repo_get(
        self, username: str, assignment_name: str
    ) -> github.Repository.Repository:
        """
        Get a student repo for a given assignment.
        """
        return [
            r
            for r in self.organization.get_repos()
            if username in r.name and assignment_name in r.name
        ][0]

    def student_repo_get_all(self, username: str) -> list[github.Repository.Repository]:
        """
        Get all student repos for a given assignment.
        """
        return [r for r in self.organization.get_repos() if username in r.name]

    def student_all_repo_get(
        self,
        assignment_name: str,
    ) -> list[github.Repository.Repository]:
        """
        Get all student repos for a given assignment.
        """
        ta_repos = self.ta_repo_get_all()
        return [
            r
            for r in self.organization.get_repos()
            if assignment_name in r.name and r not in ta_repos
        ]

    def student_all_repo_get_all(
        self,
    ) -> list[github.Repository.Repository]:
        """
        Get all student repos.
        """
        ta_repos = self.ta_repo_get_all()
        return [r for r in self.organization.get_repos() if r not in ta_repos]

    ta_grading_list = TypeVar(
        "ta_grading_list", list[list[github.Repository.Repository]], None
    )

    def grading_repos_roll(
        self, number_of_tas: int, assignment: str
    ) -> ta_grading_list:
        if assignment in self.assignments_previous:
            return self.assignments_previous[assignment]
        repositories = self.student_all_repo_get(assignment)
        random.shuffle(repositories)
        num_repos = len(repositories)
        grading_pr_ta = num_repos // number_of_tas
        leftover = num_repos % number_of_tas

        ta_grading_list = [
            repositories[ta * grading_pr_ta : ta * grading_pr_ta + grading_pr_ta]
            for ta in range(number_of_tas)
        ]
        [
            ta_grading_list[i % number_of_tas].append(repositories.pop())
            for i in range(leftover)
        ]
        reply = DiscordString("Grading list:\n")
        for i, ta in enumerate(ta_grading_list):
            reply += DiscordString(f"TA {i + 1}:").to_code_block()
            for repo in ta:
                reply += DiscordString(f"{repo.name} : <{repo.html_url}>\n")
        self.grading_add(assignment, reply)

        return reply

    def next_deadline(self) -> Deadline:
        """
        date format = "2021-09-30 23:59:59+00:00"
        """
        deadlines = self.organization.get_repo(os.environ["TA_REPO"])
        # .get_contents("deadlines.json")
        deadlines = deadlines.get_contents(os.environ["DEADLINE_FILE"])
        deadlines = json.loads(deadlines.decoded_content.decode("utf-8"))
        next = Deadline(
            "", datetime.now(tz=tzlocal()).replace(year=datetime.now().year + 1)
        )
        today = datetime.now(tz=tzlocal())
        for assignment, deadline in deadlines.items():
            deadline = datetime.fromisoformat(deadline)
            if deadline < next.date and deadline > today:
                next.name = assignment
                next.date = deadline
        return next

    def time_until_next_deadline(self) -> TimeToDeadline:
        return TimeToDeadline.from_timedelta(
            self.next_deadline().date
            - datetime.now(tz=tzlocal()).replace(microsecond=0)
        )
