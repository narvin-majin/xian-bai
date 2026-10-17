import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import reminder_manager


def make_failing_temp_file(path):
    temp_file = MagicMock()
    temp_file.name = str(path)
    temp_file.__enter__.return_value = temp_file
    temp_file.__exit__.return_value = False

    def write_partial_data(contents):
        path.write_text(contents[:10], encoding="utf-8")
        raise OSError("simulated write failure")

    temp_file.write.side_effect = write_partial_data
    return temp_file


class ReminderManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.enterContext(
            patch.object(
                reminder_manager,
                "REMINDERS_FILE",
                Path(self.temp_dir.name) / "reminders.json",
            )
        )

    def test_create_list_and_complete_reminder(self):
        add_result = reminder_manager.add_reminder("Buy groceries")
        listing = reminder_manager.list_reminders()
        done_result = reminder_manager.complete_reminder(1)

        self.assertEqual(add_result, "Reminder added: Buy groceries")
        self.assertIn("1. [ ] Buy groceries", listing)
        self.assertEqual(done_result, "Completed: Buy groceries")
        self.assertEqual(
            reminder_manager.load_reminders()["reminders"][0]["done"], True
        )

    def test_empty_reminder_title_is_rejected_without_creating_file(self):
        result = reminder_manager.add_reminder("")

        self.assertEqual(result, "Usage: /reminder_add Reminder")
        self.assertFalse(reminder_manager.REMINDERS_FILE.exists())

    def test_whitespace_only_reminder_title_is_rejected_without_modifying_file(self):
        original_bytes = b'{"reminders": []}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        result = reminder_manager.add_reminder("   ")

        self.assertEqual(result, "Usage: /reminder_add Reminder")
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_valid_reminder_title_is_stored(self):
        result = reminder_manager.add_reminder("Buy groceries")

        self.assertEqual(result, "Reminder added: Buy groceries")
        reminder = reminder_manager.load_reminders()["reminders"][0]
        self.assertEqual(reminder["title"], "Buy groceries")
        self.assertFalse(reminder["done"])
        self.assertNotIn("due_at", reminder)

    def test_due_date_and_time_are_stored_and_listed(self):
        original_data = {
            "reminders": [
                {"title": "Legacy reminder", "done": False, "created": "today"}
            ],
            "other_data": {"preserve": True},
        }
        reminder_manager.REMINDERS_FILE.write_text(
            json.dumps(original_data), encoding="utf-8"
        )

        date_result = reminder_manager.add_reminder("Pay rent", "2030-06-01")
        date_time_result = reminder_manager.add_reminder(
            "Call dentist", "2030-06-02 09:30"
        )

        saved_data = reminder_manager.load_reminders()
        self.assertEqual(date_result, "Reminder added: Pay rent")
        self.assertEqual(date_time_result, "Reminder added: Call dentist")
        self.assertEqual(saved_data["reminders"][0], original_data["reminders"][0])
        self.assertEqual(saved_data["other_data"], original_data["other_data"])
        self.assertEqual(saved_data["reminders"][1]["due_at"], "2030-06-01")
        self.assertEqual(saved_data["reminders"][2]["due_at"], "2030-06-02 09:30")

        listing = reminder_manager.list_reminders()
        self.assertIn("1. [ ] Legacy reminder\n", listing)
        self.assertIn("2. [ ] Pay rent (due: 2030-06-01)\n", listing)
        self.assertIn("3. [ ] Call dentist (due: 2030-06-02 09:30)\n", listing)

    def test_timed_telegram_reminder_stores_its_chat_id(self):
        result = reminder_manager.add_reminder(
            "Call dentist", "2030-06-02 09:30", chat_id=9876
        )

        self.assertEqual(result, "Reminder added: Call dentist")
        reminder = reminder_manager.load_reminders()["reminders"][0]
        self.assertEqual(reminder["chat_id"], 9876)

    def test_invalid_due_dates_are_rejected_without_modifying_data(self):
        original_bytes = b'{"reminders": [{"title": "Existing", "done": false}]}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)
        invalid_due_values = (
            "",
            "2030/06/01",
            "2030-02-30",
            "2030-06-01 24:00",
            "2030-06-01 09:60",
        )

        for due_at in invalid_due_values:
            with self.subTest(due_at=due_at):
                result = reminder_manager.add_reminder("New reminder", due_at)

                self.assertEqual(
                    result,
                    "Invalid due date/time. Use YYYY-MM-DD or YYYY-MM-DD HH:MM.",
                )
                self.assertEqual(
                    reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes
                )

    def test_non_numeric_reminder_number_is_rejected_without_modifying_file(self):
        original_bytes = b'{"reminders": [{"title": "Buy groceries", "done": false}]}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        result = reminder_manager.complete_reminder("not-a-number")

        self.assertEqual(result, "Reminder number must be a number.")
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_zero_and_negative_reminder_numbers_are_rejected_without_modifying_file(self):
        original_bytes = b'{"reminders": [{"title": "Buy groceries", "done": false}]}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        for reminder_number in (0, -1):
            with self.subTest(reminder_number=reminder_number):
                result = reminder_manager.complete_reminder(reminder_number)

                self.assertEqual(result, "Invalid reminder number.")
                self.assertEqual(
                    reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes
                )

    def test_number_above_reminder_count_is_rejected_without_modifying_file(self):
        original_bytes = b'{"reminders": [{"title": "Buy groceries", "done": false}]}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        result = reminder_manager.complete_reminder(2)

        self.assertEqual(result, "Invalid reminder number.")
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_already_completed_reminder_is_not_saved_again(self):
        original_bytes = b'{"reminders": [{"title": "Buy groceries", "done": true}]}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        result = reminder_manager.complete_reminder(1)

        self.assertEqual(result, "Reminder already completed.")
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_missing_reminders_file_uses_empty_default(self):
        self.assertFalse(reminder_manager.REMINDERS_FILE.exists())
        self.assertEqual(reminder_manager.load_reminders(), {"reminders": []})
        self.assertEqual(
            reminder_manager.add_reminder("First reminder"),
            "Reminder added: First reminder",
        )

    def test_malformed_reminders_json_raises_and_add_preserves_bytes(self):
        original_bytes = b'{"reminders": broken}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        with self.assertRaises(json.JSONDecodeError):
            reminder_manager.load_reminders()

        result = reminder_manager.add_reminder("New reminder")

        self.assertEqual(
            result, "Could not read reminders data. Check reminders.json."
        )
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_reminders_io_error_does_not_attempt_save(self):
        original_bytes = b"existing reminder data"
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        with patch("builtins.open", side_effect=PermissionError("read denied")):
            with patch.object(reminder_manager, "save_reminders") as save:
                result = reminder_manager.add_reminder("New reminder")

        self.assertEqual(
            result, "Could not read reminders data. Check reminders.json."
        )
        save.assert_not_called()
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_all_reminder_operations_return_error_for_malformed_json(self):
        original_bytes = b'{"reminders": broken}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)
        operations = [
            ("add", lambda: reminder_manager.add_reminder("New reminder")),
            ("list", reminder_manager.list_reminders),
            ("complete", lambda: reminder_manager.complete_reminder(1)),
        ]

        with patch.object(reminder_manager, "save_reminders") as save:
            for operation_name, operation in operations:
                with self.subTest(operation=operation_name):
                    self.assertEqual(
                        operation(),
                        "Could not read reminders data. Check reminders.json.",
                    )
                    self.assertEqual(
                        reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes
                    )

        save.assert_not_called()

    def test_all_reminder_operations_return_error_for_io_failure(self):
        original_bytes = b"existing reminder data"
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)
        operations = [
            ("add", lambda: reminder_manager.add_reminder("New reminder")),
            ("list", reminder_manager.list_reminders),
            ("complete", lambda: reminder_manager.complete_reminder(1)),
        ]

        with patch("builtins.open", side_effect=PermissionError("read denied")):
            with patch.object(reminder_manager, "save_reminders") as save:
                for operation_name, operation in operations:
                    with self.subTest(operation=operation_name):
                        self.assertEqual(
                            operation(),
                            "Could not read reminders data. Check reminders.json.",
                        )

        save.assert_not_called()
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)

    def test_valid_reminders_json_loads_and_saves(self):
        valid_data = {
            "reminders": [
                {"title": "Existing", "done": False, "created": "today"}
            ]
        }
        reminder_manager.REMINDERS_FILE.write_text(
            json.dumps(valid_data), encoding="utf-8"
        )

        self.assertEqual(reminder_manager.load_reminders(), valid_data)
        updated_data = {"reminders": valid_data["reminders"] + [
            {"title": "Next", "done": False, "created": "today"}
        ]}
        reminder_manager.save_reminders(updated_data)

        self.assertEqual(reminder_manager.load_reminders(), updated_data)

    def test_reminder_write_failure_preserves_file_and_cleans_temporary_file(self):
        original_bytes = b'{"reminders": []}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        with patch("os.replace", side_effect=OSError("replace failed")):
            result = reminder_manager.add_reminder("New reminder")

        self.assertEqual(
            result,
            "Could not save reminders data. Check reminders.json and try again.",
        )
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)
        self.assertEqual(
            list(reminder_manager.REMINDERS_FILE.parent.glob(".reminders.json.*.tmp")),
            [],
        )

    def test_reminder_serialization_failure_preserves_file(self):
        original_bytes = b'{"reminders": []}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)

        with patch.object(reminder_manager.json, "dumps", side_effect=TypeError):
            result = reminder_manager.add_reminder("New reminder")

        self.assertEqual(
            result,
            "Could not save reminders data. Check reminders.json and try again.",
        )
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)
        self.assertEqual(
            list(reminder_manager.REMINDERS_FILE.parent.glob(".reminders.json.*.tmp")),
            [],
        )

    def test_reminder_partial_write_preserves_file_and_cleans_temporary_file(self):
        original_bytes = b'{"reminders": []}'
        reminder_manager.REMINDERS_FILE.write_bytes(original_bytes)
        temporary_path = reminder_manager.REMINDERS_FILE.parent / ".reminders.json.test.tmp"
        failing_temp_file = make_failing_temp_file(temporary_path)

        with patch.object(
            reminder_manager.tempfile,
            "NamedTemporaryFile",
            return_value=failing_temp_file,
        ):
            result = reminder_manager.add_reminder("New reminder")

        self.assertEqual(
            result,
            "Could not save reminders data. Check reminders.json and try again.",
        )
        self.assertEqual(reminder_manager.REMINDERS_FILE.read_bytes(), original_bytes)
        self.assertFalse(temporary_path.exists())

    def test_reminder_save_preserves_existing_file_permissions(self):
        reminder_manager.REMINDERS_FILE.write_text("{}", encoding="utf-8")
        reminder_manager.REMINDERS_FILE.chmod(0o640)

        reminder_manager.save_reminders({"reminders": []})

        self.assertEqual(
            stat.S_IMODE(reminder_manager.REMINDERS_FILE.stat().st_mode), 0o640
        )


if __name__ == "__main__":
    unittest.main()
