import logging
from genericMessageHandler import GenericMessageHandler


class TemplateHandler(GenericMessageHandler):
    """
    Template for handlers
    Methods that handle messages should be named message_<command>
    Methods that handle reactions should be named reaction_<event>
    """

    def __init__(self, help_text, response, reply_private, log_level=logging.WARNING):
        super().__init__(help_text, response, reply_private, log_level)
        self.log.debug("TemplateHandler initialized")
