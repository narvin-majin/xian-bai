import unittest
from unittest.mock import patch

import command_router
import preview_manager


class ReminderCommandRoutingTests(unittest.TestCase):
    def test_confirm_and_cancel_commands_use_terminal_session(self):
        terminal_key = ("terminal",)
        preview_manager.set_preview(
            terminal_key, {"type": "reminder", "title": "Terminal draft"}
        )
        self.addCleanup(preview_manager.clear_preview, terminal_key)

        with patch.object(command_router, "add_reminder", return_value="Reminder added: Terminal draft") as add:
            self.assertEqual(
                command_router.handle_command("/confirm"),
                "Reminder added: Terminal draft",
            )
        add.assert_called_once_with("Terminal draft", None)
        self.assertIsNone(preview_manager.get_preview(terminal_key))

        self.assertEqual(
            command_router.handle_command("/cancel"),
            "There is no pending preview to cancel.",
        )

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
            with patch.object(command_router, "reschedule_reminder") as reschedule:
                self.assertEqual(
                    command_router.handle_command("/reminder_reschedule1 --due 2030-06-01"),
                    "Unknown command.",
                )
                reschedule.assert_not_called()

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

    def test_reminder_add_passes_telegram_chat_id_for_delivery(self):
        with patch.object(
            command_router,
            "add_reminder",
            return_value="Reminder added: Call dentist",
        ) as add_reminder:
            result = command_router.handle_command(
                "/reminder_add Call dentist --due 2030-06-02 09:30",
                chat_id=9876,
            )

        self.assertEqual(result, "Reminder added: Call dentist")
        add_reminder.assert_called_once_with(
            "Call dentist", "2030-06-02 09:30", chat_id=9876
        )

    def test_reminder_reschedule_dispatches_date_only_and_timed_due_values(self):
        for due_at in ("2030-06-02", "2030-06-02 09:30"):
            with self.subTest(due_at=due_at):
                with patch.object(
                    command_router,
                    "reschedule_reminder",
                    return_value="Rescheduled: Call dentist",
                ) as reschedule:
                    result = command_router.handle_command(
                        f"/reminder_reschedule 2 --due {due_at}"
                    )

                self.assertEqual(result, "Rescheduled: Call dentist")
                reschedule.assert_called_once_with(2, due_at)

    def test_reminder_reschedule_rejects_malformed_arguments(self):
        malformed_commands = (
            "/reminder_reschedule",
            "/reminder_reschedule nope --due 2030-06-02",
            "/reminder_reschedule 1",
            "/reminder_reschedule 1 --date 2030-06-02",
        )
        with patch.object(command_router, "reschedule_reminder") as reschedule:
            for command in malformed_commands:
                with self.subTest(command=command):
                    result = command_router.handle_command(command)
                    self.assertNotEqual(result, "Unknown command.")
            reschedule.assert_not_called()

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
