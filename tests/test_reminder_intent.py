import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import command_router
import preview_manager
import project_manager
import reminder_intent
import reminder_manager
import reminder_scheduler
import terminal_ui


class ReminderIntentTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.reminders_file = root / "reminders.json"
        self.projects_file = root / "projects.json"
        self.enterContext(
            patch.object(reminder_manager, "REMINDERS_FILE", self.reminders_file)
        )
        self.enterContext(
            patch.object(project_manager, "PROJECTS_FILE", self.projects_file)
        )
        self.now = datetime(2030, 6, 1, 12, 0)
        self.session_keys = []

    def set_preview(self, key, preview):
        self.session_keys.append(key)
        preview_manager.set_preview(key, preview)

    def tearDown(self):
        for key in self.session_keys:
            preview_manager.clear_preview(key)

    def test_parser_handles_supported_date_only_and_timed_patterns(self):
        self.assertEqual(
            reminder_intent.parse_reminder_request("Buy books tomorrow", self.now),
            {"status": "preview", "title": "Buy books", "due_at": "2030-06-02"},
        )
        self.assertEqual(
            reminder_intent.parse_reminder_request(
                "Call Mom at 10 PM tomorrow", self.now
            ),
            {
                "status": "preview",
                "title": "Call Mom",
                "due_at": "2030-06-02 22:00",
            },
        )
        self.assertEqual(
            reminder_intent.parse_reminder_request(
                "Please remind me to buy milk", self.now
            ),
            {"status": "preview", "title": "buy milk", "due_at": None},
        )

    def test_weekday_and_next_weekday_rules_are_deterministic(self):
        tuesday = datetime(2030, 6, 4, 9, 0)
        self.assertEqual(
            reminder_intent.parse_reminder_request("Call Mom Monday", tuesday),
            {"status": "preview", "title": "Call Mom", "due_at": "2030-06-10"},
        )

        monday = datetime(2030, 6, 3, 9, 0)
        self.assertEqual(
            reminder_intent.parse_reminder_request("Call Mom Monday", monday),
            {"status": "preview", "title": "Call Mom", "due_at": "2030-06-03"},
        )
        self.assertEqual(
            reminder_intent.parse_reminder_request("Call Mom next Monday", monday),
            {"status": "preview", "title": "Call Mom", "due_at": "2030-06-10"},
        )

    def test_explicit_calendar_dates_support_both_orders_and_optional_time(self):
        cases = (
            ("Buy books 25 October", "2030-10-25"),
            ("Buy books October 25", "2030-10-25"),
            ("Call Mom at 10 PM 25 October", "2030-10-25 22:00"),
            ("Call Mom October 25 at 10:15 AM", "2030-10-25 10:15"),
            ("Call Mom 25 October 2031 at 10 PM", "2031-10-25 22:00"),
            ("Call Mom October 25, 2031 at 10 PM", "2031-10-25 22:00"),
        )
        for text, due_at in cases:
            with self.subTest(text=text):
                parsed = reminder_intent.parse_reminder_request(text, self.now)
                self.assertEqual(parsed["status"], "preview")
                self.assertEqual(parsed["due_at"], due_at)

    def test_calendar_dates_observe_year_boundaries_and_leap_days(self):
        december_31 = datetime(2030, 12, 31, 9, 0)
        self.assertEqual(
            reminder_intent.parse_reminder_request("Buy books tomorrow", december_31)["due_at"],
            "2031-01-01",
        )
        self.assertEqual(
            reminder_intent.parse_reminder_request("Call Mom next Monday", december_31)["due_at"],
            "2031-01-06",
        )
        self.assertEqual(
            reminder_intent.parse_reminder_request(
                "Call Mom 29 February 2028", datetime(2028, 2, 1, 9, 0)
            )["due_at"],
            "2028-02-29",
        )
        invalid_leap_day = reminder_intent.parse_reminder_request(
            "Call Mom 29 February", datetime(2027, 2, 1, 9, 0)
        )
        self.assertEqual(invalid_leap_day["status"], "clarify")

    def test_past_and_invalid_or_incomplete_calendar_dates_clarify(self):
        cases = (
            ("Buy books 25 October", datetime(2030, 10, 26, 9, 0)),
            ("Buy books October 25", datetime(2030, 10, 26, 9, 0)),
            ("Buy books 31 February", self.now),
            ("Buy books October", self.now),
            ("Buy books 25", self.now),
            ("Buy books last Monday", self.now),
        )
        for text, now in cases:
            with self.subTest(text=text):
                parsed = reminder_intent.parse_reminder_request(text, now)
                self.assertEqual(parsed["status"], "clarify")

    def test_unsupported_or_ambiguous_dates_request_clarification(self):
        for text in (
            "Buy books next week",
            "Call Mom at 25 PM tomorrow",
            "Remind me to buy milk in 30 seconds",
        ):
            with self.subTest(text=text):
                parsed = reminder_intent.parse_reminder_request(text, self.now)
                self.assertEqual(parsed["status"], "clarify")

        self.assertEqual(
            reminder_intent.parse_reminder_request("I might buy books tomorrow", self.now),
            None,
        )

    def test_relative_minutes_hours_and_days_use_defined_formats(self):
        cases = (
            ("Remind me to stretch in 30 minutes.", "stretch", "2030-06-01 12:30"),
            ("Call Mom in two hours.", "Call Mom", "2030-06-01 14:00"),
            (
                "Finish the assignment in three days.",
                "Finish the assignment",
                "2030-06-04",
            ),
        )
        for text, title, due_at in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    reminder_intent.parse_reminder_request(text, self.now),
                    {"status": "preview", "title": title, "due_at": due_at},
                )

    def test_relative_durations_cross_midnight_month_and_year_boundaries(self):
        cases = (
            (
                "Call Mom in 30 minutes",
                datetime(2030, 6, 1, 23, 45),
                "2030-06-02 00:15",
            ),
            (
                "Call Mom in two hours",
                datetime(2030, 1, 31, 23, 30),
                "2030-02-01 01:30",
            ),
            (
                "Call Mom in two hours",
                datetime(2030, 12, 31, 23, 30),
                "2031-01-01 01:30",
            ),
            (
                "Finish the assignment in three days",
                datetime(2030, 12, 31, 23, 30),
                "2031-01-03",
            ),
        )
        for text, now, due_at in cases:
            with self.subTest(text=text, now=now):
                parsed = reminder_intent.parse_reminder_request(text, now)
                self.assertEqual(parsed["status"], "preview")
                self.assertEqual(parsed["due_at"], due_at)

    def test_invalid_malformed_unsupported_and_overflowing_durations_clarify(self):
        for text in (
            "Remind me to stretch in 0 minutes",
            "Remind me to stretch in zero hours",
            "Remind me to stretch in -2 days",
            "Remind me to stretch in a couple of hours",
            "Remind me to stretch in 30 seconds",
            "Remind me to stretch in 999999999999999999999999 hours",
        ):
            with self.subTest(text=text):
                parsed = reminder_intent.parse_reminder_request(text, self.now)
                self.assertEqual(parsed["status"], "clarify")

    def test_recognized_request_creates_only_an_in_memory_preview(self):
        key = preview_manager.session_key()
        self.session_keys.append(key)

        reply = reminder_intent.handle_reminder_request(
            "Buy books tomorrow", key, now=self.now
        )

        self.assertEqual(
            reply,
            "Reminder preview: Buy books (due: 2030-06-02)\n"
            "Reply /confirm to save or /cancel to discard.",
        )
        self.assertEqual(
            preview_manager.get_preview(key),
            {"type": "reminder", "title": "Buy books", "due_at": "2030-06-02"},
        )
        self.assertFalse(self.reminders_file.exists())
        self.assertFalse(self.projects_file.exists())

    def test_relative_request_has_no_persistent_write_until_confirmation(self):
        key = preview_manager.session_key()
        self.session_keys.append(key)

        reminder_intent.handle_reminder_request(
            "Remind me to stretch in 30 minutes", key, now=self.now
        )

        self.assertFalse(self.reminders_file.exists())
        self.assertFalse(self.projects_file.exists())
        self.assertEqual(
            command_router.handle_command("/confirm"), "Reminder added: stretch"
        )
        stored = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(stored["reminders"][0]["due_at"], "2030-06-01 12:30")

    def test_confirm_saves_staged_request_and_cancel_leaves_data_unchanged(self):
        key = preview_manager.session_key()
        self.session_keys.append(key)
        reminder_intent.handle_reminder_request(
            "Call Mom at 10 PM tomorrow", key, now=self.now
        )
        self.assertFalse(self.reminders_file.exists())

        confirmed = command_router.handle_command("/confirm")

        self.assertEqual(confirmed, "Reminder added: Call Mom")
        reminders = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(reminders["reminders"][0]["due_at"], "2030-06-02 22:00")
        self.assertIsNone(preview_manager.get_preview(key))

        self.projects_file.write_text(
            '{"active_project": null, "projects": {}}', encoding="utf-8"
        )
        reminders_before = self.reminders_file.read_bytes()
        projects_before = self.projects_file.read_bytes()
        reminder_intent.handle_reminder_request(
            "Buy pens tomorrow", key, now=self.now
        )

        cancelled = command_router.handle_command("/cancel")

        self.assertEqual(cancelled, "Pending preview cancelled.")
        self.assertEqual(self.reminders_file.read_bytes(), reminders_before)
        self.assertEqual(self.projects_file.read_bytes(), projects_before)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_timed_request_confirms_and_scheduler_notifies_at_most_once(self):
        key = preview_manager.session_key(8123)
        self.session_keys.append(key)
        reminder_intent.handle_reminder_request(
            "Call Mom at 10 PM tomorrow", key, now=self.now
        )
        self.assertFalse(self.reminders_file.exists())

        self.assertEqual(
            command_router.handle_command("/confirm", chat_id=8123),
            "Reminder added: Call Mom",
        )
        saved = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["reminders"]), 1)
        self.assertEqual(saved["reminders"][0]["title"], "Call Mom")
        self.assertEqual(saved["reminders"][0]["due_at"], "2030-06-02 22:00")
        self.assertEqual(saved["reminders"][0]["chat_id"], 8123)

        sender = Mock()
        due_time = datetime(2030, 6, 2, 22, 0)
        self.assertEqual(
            reminder_scheduler.check_due_reminders(sender, now=due_time), 1
        )
        self.assertEqual(
            reminder_scheduler.check_due_reminders(sender, now=due_time), 0
        )
        sender.assert_called_once_with(8123, "Reminder: Call Mom")

    def test_date_only_request_confirms_without_timed_scheduler_delivery(self):
        key = preview_manager.session_key(8124)
        self.session_keys.append(key)
        reminder_intent.handle_reminder_request("Buy books tomorrow", key, now=self.now)

        self.assertEqual(
            command_router.handle_command("/confirm", chat_id=8124),
            "Reminder added: Buy books",
        )
        saved = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["reminders"][0]["due_at"], "2030-06-02")
        self.assertEqual(saved["reminders"][0]["chat_id"], 8124)

        sender = Mock()
        self.assertEqual(
            reminder_scheduler.check_due_reminders(
                sender, now=datetime(2030, 6, 2, 23, 59)
            ),
            0,
        )
        sender.assert_not_called()

    def test_past_timed_request_is_rejected_with_controlled_clock(self):
        now = datetime(2030, 6, 1, 22, 1)

        parsed = reminder_intent.parse_reminder_request(
            "Call Mom at 10 PM today", now=now
        )

        self.assertEqual(parsed["status"], "clarify")

    def test_ordinary_terminal_chat_still_uses_normal_chat_path(self):
        chat_history = []
        save_history = Mock()
        with patch("builtins.input", side_effect=["How are you?", "exit"]):
            with patch("terminal_ui.process_message", return_value="Normal reply") as process:
                with patch("builtins.print"):
                    terminal_ui.start_terminal(
                        state={},
                        projects={},
                        chat_history=chat_history,
                        client=object(),
                        save_chat_history=save_history,
                    )

        process.assert_called_once_with(
            "How are you?", {}, {}, chat_history, unittest.mock.ANY
        )
        save_history.assert_called_once_with(chat_history)

    def test_terminal_intercepts_request_without_calling_ai_or_saving_history(self):
        key = preview_manager.session_key()
        self.session_keys.append(key)
        chat_history = []
        save_history = Mock()
        output = []

        with patch("builtins.input", side_effect=["Buy books tomorrow", "exit"]):
            with patch(
                "terminal_ui.handle_reminder_request",
                side_effect=lambda text, session: reminder_intent.handle_reminder_request(
                    text, session, now=self.now
                ),
            ) as handle_request:
                with patch("terminal_ui.process_message") as process_message:
                    with patch("builtins.print", side_effect=lambda *args: output.append(args)):
                        terminal_ui.start_terminal(
                            state={},
                            projects={},
                            chat_history=chat_history,
                            client=None,
                            save_chat_history=save_history,
                        )

        handle_request.assert_called_once_with("Buy books tomorrow", key)
        process_message.assert_not_called()
        save_history.assert_not_called()
        self.assertEqual(chat_history, [])
        self.assertEqual(
            preview_manager.get_preview(key)["due_at"], "2030-06-02"
        )


if __name__ == "__main__":
    unittest.main()
