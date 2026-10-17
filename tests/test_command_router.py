import unittest
from unittest.mock import patch

import command_router


class ReminderCommandRoutingTests(unittest.TestCase):
    def test_reminder_name_prefixes_are_unknown_commands(self):
        with patch.object(command_router, "add_reminder") as add_reminder:
            with patch.object(command_router, "complete_reminder") as complete_reminder:
                self.assertEqual(
                    command_router.handle_command("/reminder_additional note"),
                    "Unknown command.",
                )
                self.assertEqual(
                    command_router.handle_command("/reminder_done1"),
                    "Unknown command.",
                )

        add_reminder.assert_not_called()
        complete_reminder.assert_not_called()

    def test_reminder_commands_with_arguments_are_dispatched(self):
        with patch.object(
            command_router, "add_reminder", return_value="Reminder added: Sample reminder"
        ) as add_reminder:
            result = command_router.handle_command("/reminder_add Sample reminder")

        self.assertEqual(result, "Reminder added: Sample reminder")
        add_reminder.assert_called_once_with("Sample reminder")

        with patch.object(
            command_router, "complete_reminder", return_value="Completed: Sample reminder"
        ) as complete_reminder:
            result = command_router.handle_command("/reminder_done 1")

        self.assertEqual(result, "Completed: Sample reminder")
        complete_reminder.assert_called_once_with(1)

    def test_reminder_add_dispatches_optional_due_date_and_time(self):
        with patch.object(
            command_router,
            "add_reminder",
            return_value="Reminder added: Call dentist",
        ) as add_reminder:
            result = command_router.handle_command(
                "/reminder_add Call dentist --due 2030-06-02 09:30"
            )

        self.assertEqual(result, "Reminder added: Call dentist")
        add_reminder.assert_called_once_with("Call dentist", "2030-06-02 09:30")

    def test_reminder_commands_without_arguments_keep_existing_validation(self):
        with patch.object(
            command_router, "add_reminder", return_value="Usage: /reminder_add Reminder"
        ) as add_reminder:
            result = command_router.handle_command("/reminder_add")

        self.assertEqual(result, "Usage: /reminder_add Reminder")
        add_reminder.assert_called_once_with("")

        self.assertEqual(
            command_router.handle_command("/reminder_done"),
            "Reminder number must be a number.",
        )


if __name__ == "__main__":
    unittest.main()
