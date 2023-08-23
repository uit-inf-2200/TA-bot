from constants import Permissions


class DiscordString(str):
    def __new__(self, value):
        obj = str.__new__(self, value)
        return obj

    def __add__(self, __s: str) -> str:
        return DiscordString(super().__add__(__s))

    def to_code_block(self, format_type="ml"):
        return f"```{format_type}\n{self.__str__()}```"

    def to_code_inline(self):
        return f"`{self.__str__()}`"


def hide(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    inner.hidden = True
    return inner


def is_hidden(func):
    return getattr(func, "hidden", False)


def member_check(function):
    async def inner(self, message, permission):
        if permission < Permissions.member:
            return
        await function(self, message)

    return inner


def admin_check(function):
    async def inner(self, message, permission):
        if permission < Permissions.admin:
            return
        await function(self, message, permission)

    return inner
