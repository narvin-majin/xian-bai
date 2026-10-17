import unittest
from types import SimpleNamespace
from unittest.mock import patch

import command_router
import telegram_ui


class FakeBot:
    def __init__(self):
        self.handlers = {}
        self.command_menu = []
        self.replies = []

    def set_my_commands(self, commands):
        self.command_menu = commands

    def message_handler(self, commands=None, func=None):
        def register_handler(callback):
            if commands:
                for command in commands:
                    self.handlers[command] = callback
            return callback

        return register_handler

    def reply_to(self, message, text):
        self.replies.append((message, text))


class TelegramProjectHandlerTests(unittest.TestCase):
    def setUp(self):
        self.bot = FakeBot()
        telegram_ui.register_handlers(
            bot=self.bot,
            client=None,
            state={},
            projects={},
            chat_history=[],
            save_chat_history=lambda history: None,
        )

    def test_projects_handler_routes_through_dispatcher_and_replies(self):
        message = SimpleNamespace(text="/projects@xiaobai_bot")

        with patch.object(
            command_router, "list_projects", return_value="No projects found."
        ) as list_projects:
            with patch.object(
                telegram_ui,
                "handle_command",
                wraps=command_router.handle_command,
            ) as handle_command:
                self.bot.handlers["projects"](message)

        handle_command.assert_called_once_with("/projects")
        list_projects.assert_called_once_with()
        self.assertEqual(self.bot.replies, [(message, "No projects found.")])


if __name__ == "__main__":
    unittest.main()
