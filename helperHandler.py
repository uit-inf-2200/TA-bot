import os
import inspect
from common import member_check, admin_check, hide, DiscordString
from templateHandler import TemplateHandler


class HelperHandler(TemplateHandler):
    def __init__(self, handlers: list) -> None:
        super().__init__("Help", "Help", False)
        self.log.debug("HelperHandler initialized")
        self.handlers = handlers

    @hide
    def is_hidden(self, func):
        return getattr(func, "hidden", False)

    async def message_help(self, message, _):
        """
        Print this message
        """
        reply = DiscordString(
            f"Welcome to {os.environ['GITHUB_ORGANIZATION']}'s Discord. Here's available commands:\n"
        )
        commands = DiscordString("")
        for handler in self.handlers:
            for name, method in inspect.getmembers(handler, predicate=inspect.ismethod):
                if name.startswith(self.message_prefix) and not self.is_hidden(method):
                    commands += (
                        f"{name.removeprefix(self.message_prefix)}: {method.__doc__}\n"
                    )
        await self.reply(message, reply + commands.to_code_block(""))

    @hide
    @admin_check
    async def message_list_commands_admin(self, message, _):
        reply = DiscordString("Commands:\n")
        commands = DiscordString("")
        for handler in self.handlers:
            for name, method in inspect.getmembers(handler, predicate=inspect.ismethod):
                if name.startswith(self.message_prefix):
                    commands += f"{name.removeprefix(self.message_prefix)}\n"
        await self.reply(message, reply + commands.to_code_block())
