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


class TelegramReminderHandlerTests(unittest.TestCase):
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

    def test_add_handler_routes_through_dispatcher_with_optional_due(self):
        cases = (
            (
                "/reminder_add@xiaobai_bot Sample reminder",
                "/reminder_add Sample reminder",
                ("Sample reminder",),
                "Reminder added: Sample reminder",
            ),
            (
                "/reminder_add@xiaobai_bot Call dentist --due 2030-06-02 09:30",
                "/reminder_add Call dentist --due 2030-06-02 09:30",
                ("Call dentist", "2030-06-02 09:30"),
                "Reminder added: Call dentist",
            ),
        )

        for message_text, expected_command, manager_args, result in cases:
            with self.subTest(message_text=message_text):
                message = SimpleNamespace(text=message_text)
                self.bot.replies.clear()
                with patch.object(
                    command_router, "add_reminder", return_value=result
                ) as add_reminder:
                    with patch.object(
                        telegram_ui,
                        "handle_command",
                        wraps=command_router.handle_command,
                    ) as handle_command:
                        self.bot.handlers["reminder_add"](message)

                handle_command.assert_called_once_with(expected_command)
                add_reminder.assert_called_once_with(*manager_args)
                self.assertEqual(self.bot.replies, [(message, result)])

    def test_list_handler_routes_through_dispatcher_and_replies(self):
        message = SimpleNamespace(text="/reminders")
        results = [
            "Reminders:\n\n1. [ ] Sample reminder\n",
            "No reminders found.",
        ]

        for result in results:
            with self.subTest(result=result):
                self.bot.replies.clear()
                with patch.object(
                    command_router, "list_reminders", return_value=result
                ) as list_reminders:
                    with patch.object(
                        telegram_ui,
                        "handle_command",
                        wraps=command_router.handle_command,
                    ) as handle_command:
                        self.bot.handlers["reminders"](message)

                handle_command.assert_called_once_with("/reminders")
                list_reminders.assert_called_once_with()
                self.assertEqual(self.bot.replies, [(message, result)])

    def test_done_handler_completes_valid_number_and_replies(self):
        message = SimpleNamespace(text="/reminder_done 1")
        with patch.object(
            telegram_ui,
            "complete_reminder",
            return_value="Completed: Sample reminder",
        ) as complete_reminder:
            self.bot.handlers["reminder_done"](message)

        complete_reminder.assert_called_once_with(1)
        self.assertEqual(
            self.bot.replies,
            [(message, "Completed: Sample reminder")],
        )

    def test_done_handler_replies_to_invalid_number_without_manager_call(self):
        message = SimpleNamespace(text="/reminder_done not-a-number")
        with patch.object(telegram_ui, "complete_reminder") as complete_reminder:
            self.bot.handlers["reminder_done"](message)

        complete_reminder.assert_not_called()
        self.assertEqual(
            self.bot.replies,
            [(message, "Reminder number must be a number.")],
        )


if __name__ == "__main__":
    unittest.main()
