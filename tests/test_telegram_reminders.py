import unittest
import tempfile
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path

import command_router
import reminder_manager
import preview_manager
import reminder_intent
import telegram_ui


class FakeBot:
    def __init__(self):
        self.handlers = {}
        self.chat_handler = None
        self.command_menu = []
        self.replies = []

    def set_my_commands(self, commands):
        self.command_menu = commands

    def message_handler(self, commands=None, func=None):
        def register_handler(callback):
            if commands:
                for command in commands:
                    self.handlers[command] = callback
            if func is not None:
                self.chat_handler = callback
            return callback

        return register_handler

    def reply_to(self, message, text):
        self.replies.append((message, text))


class TelegramReminderHandlerTests(unittest.TestCase):
    def setUp(self):
        self.bot = FakeBot()
        self.chat_history = []
        self.save_chat_history = Mock()
        telegram_ui.register_handlers(
            bot=self.bot,
            client=None,
            state={},
            projects={},
            chat_history=self.chat_history,
            save_chat_history=self.save_chat_history,
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
                message.chat = SimpleNamespace(id=9876)
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

                handle_command.assert_called_once_with(
                    expected_command, chat_id=9876
                )
                if len(manager_args) == 2:
                    add_reminder.assert_called_once_with(
                        *manager_args, chat_id=9876
                    )
                else:
                    add_reminder.assert_called_once_with(*manager_args)
                self.assertEqual(self.bot.replies, [(message, result)])

    def test_telegram_timed_reminder_is_saved_with_due_time(self):
        message = SimpleNamespace(
            text="/reminder_add test --due 2026-10-17 21:25",
            chat=SimpleNamespace(id=9876),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                reminder_manager,
                "REMINDERS_FILE",
                Path(temp_dir) / "reminders.json",
            ):
                self.bot.handlers["reminder_add"](message)
                saved = reminder_manager.load_reminders()["reminders"][0]

        self.assertEqual(saved["title"], "test")
        self.assertEqual(saved["due_at"], "2026-10-17 21:25")
        self.assertEqual(saved["chat_id"], 9876)
        self.assertEqual(
            self.bot.replies,
            [(message, "Reminder added: test")],
        )

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

    def test_confirm_and_cancel_handlers_pass_telegram_chat_id(self):
        message = SimpleNamespace(text="/confirm", chat=SimpleNamespace(id=4321))
        with patch.object(
            telegram_ui, "handle_command", return_value="There is no pending preview to confirm."
        ) as handle_command:
            self.bot.handlers["confirm"](message)

        handle_command.assert_called_once_with("/confirm", chat_id=4321)
        self.assertEqual(
            self.bot.replies[-1],
            (message, "There is no pending preview to confirm."),
        )

        message.text = "/cancel"
        with patch.object(
            telegram_ui, "handle_command", return_value="Pending preview cancelled."
        ) as handle_command:
            self.bot.handlers["cancel"](message)

        handle_command.assert_called_once_with("/cancel", chat_id=4321)
        self.assertEqual(
            self.bot.replies[-1], (message, "Pending preview cancelled.")
        )

    def test_edit_handler_passes_chat_id_and_command_is_in_menu(self):
        message = SimpleNamespace(
            text='/edit --title "Telegram updated"',
            chat=SimpleNamespace(id=4322),
        )
        with patch.object(
            telegram_ui, "handle_command", return_value="Reminder preview updated"
        ) as handle_command:
            self.bot.handlers["edit"](message)

        handle_command.assert_called_once_with(
            '/edit --title "Telegram updated"', chat_id=4322
        )
        self.assertEqual(self.bot.replies[-1], (message, "Reminder preview updated"))
        self.assertIn("edit", [command.command for command in self.bot.command_menu])

    def test_edit_handler_changes_only_calling_telegram_session(self):
        first_key = preview_manager.session_key(4323)
        second_key = preview_manager.session_key(4324)
        terminal_key = preview_manager.session_key()
        preview_manager.set_preview(
            first_key, {"type": "reminder", "title": "First chat"}
        )
        preview_manager.set_preview(
            second_key, {"type": "reminder", "title": "Second chat"}
        )
        preview_manager.set_preview(
            terminal_key, {"type": "reminder", "title": "Terminal"}
        )
        self.addCleanup(preview_manager.clear_preview, first_key)
        self.addCleanup(preview_manager.clear_preview, second_key)
        self.addCleanup(preview_manager.clear_preview, terminal_key)
        message = SimpleNamespace(
            text='/edit --title "First chat edited"',
            chat=SimpleNamespace(id=4323),
        )

        self.bot.handlers["edit"](message)

        self.assertEqual(preview_manager.get_preview(first_key)["title"], "First chat edited")
        self.assertEqual(preview_manager.get_preview(second_key)["title"], "Second chat")
        self.assertEqual(preview_manager.get_preview(terminal_key)["title"], "Terminal")

    def test_telegram_natural_reminder_stages_without_chat_history_or_storage_write(self):
        message = SimpleNamespace(
            text="Buy books tomorrow",
            chat=SimpleNamespace(id=7654),
        )
        key = preview_manager.session_key(7654)
        with tempfile.TemporaryDirectory() as temp_dir:
            reminders_file = Path(temp_dir) / "reminders.json"
            with patch.object(reminder_manager, "REMINDERS_FILE", reminders_file):
                with patch(
                    "telegram_ui.handle_reminder_request",
                    side_effect=lambda text, session: reminder_intent.handle_reminder_request(
                        text, session, now=datetime(2030, 6, 1, 12)
                    ),
                ) as handle_request:
                    self.bot.chat_handler(message)

                handle_request.assert_called_once_with("Buy books tomorrow", key)
                self.assertFalse(reminders_file.exists())
                self.assertEqual(self.chat_history, [])
                self.save_chat_history.assert_not_called()
                self.assertEqual(
                    preview_manager.get_preview(key)["due_at"], "2030-06-02"
                )
                self.assertIn("/confirm", self.bot.replies[-1][1])

                other_message = SimpleNamespace(
                    text="/confirm", chat=SimpleNamespace(id=7655)
                )
                self.bot.handlers["confirm"](other_message)
                self.assertFalse(reminders_file.exists())
                self.assertIsNotNone(preview_manager.get_preview(key))

                self.bot.handlers["confirm"](message)
                saved = reminder_manager.load_reminders()["reminders"]

        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["chat_id"], 7654)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_ordinary_telegram_chat_still_uses_normal_chat_path(self):
        message = SimpleNamespace(
            text="How are you?",
            chat=SimpleNamespace(id=8765),
        )
        with patch(
            "telegram_ui.process_message", return_value="Normal reply"
        ) as process_message:
            self.bot.chat_handler(message)

        process_message.assert_called_once_with(
            "How are you?", {}, {}, self.chat_history, None
        )
        self.save_chat_history.assert_called_once_with(self.chat_history)
        self.assertEqual(self.bot.replies, [(message, "Normal reply")])


if __name__ == "__main__":
    unittest.main()
