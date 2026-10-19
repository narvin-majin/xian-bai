import json
import importlib
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import reminder_manager
import reminder_scheduler


class ReminderSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.reminders_file = Path(self.temp_dir.name) / "reminders.json"
        self.path_patch = patch.object(
            reminder_manager, "REMINDERS_FILE", self.reminders_file
        )
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def write_reminders(self, reminders):
        self.reminders_file.write_text(
            json.dumps({"reminders": reminders}), encoding="utf-8"
        )

    def test_due_timed_reminder_sends_once_and_stays_marked_after_restart(self):
        self.write_reminders([
            {
                "title": "Pay rent",
                "done": False,
                "due_at": "2030-06-02 09:30",
                "chat_id": 12345,
            }
        ])
        sender = Mock()
        now = datetime(2030, 6, 2, 10, 0)

        first_check = reminder_scheduler.check_due_reminders(sender, now=now)
        restarted_scheduler = importlib.reload(reminder_scheduler)
        second_check = restarted_scheduler.check_due_reminders(sender, now=now)

        self.assertEqual(first_check, 1)
        self.assertEqual(second_check, 0)
        sender.assert_called_once_with(12345, "Reminder: Pay rent")
        self.assertTrue(reminder_manager.load_reminders()["reminders"][0]["notified"])

    def test_rescheduled_previously_notified_reminder_sends_again_at_new_time(self):
        self.write_reminders([
            {
                "title": "Pay rent",
                "done": False,
                "due_at": "2030-06-02 08:00",
                "chat_id": 12345,
            }
        ])
        sender = Mock()
        first_time = datetime(2030, 6, 2, 8, 0)
        sent = reminder_scheduler.check_due_reminders(sender, now=first_time)
        self.assertEqual(sent, 1)
        sender.assert_called_once_with(12345, "Reminder: Pay rent")
        self.assertTrue(reminder_manager.load_reminders()["reminders"][0]["notified"])

        sender.reset_mock()
        reschedule_result = reminder_manager.reschedule_reminder(
            1, "2030-06-03 09:00"
        )
        self.assertEqual(reschedule_result, "Rescheduled: Pay rent")
        self.assertFalse(reminder_manager.load_reminders()["reminders"][0]["notified"])

        intermediate_time = datetime(2030, 6, 2, 12, 0)
        self.assertEqual(
            reminder_scheduler.check_due_reminders(sender, now=intermediate_time), 0
        )
        sender.assert_not_called()

        new_due_time = datetime(2030, 6, 3, 9, 0)
        self.assertEqual(
            reminder_scheduler.check_due_reminders(sender, now=new_due_time), 1
        )
        sender.assert_called_once_with(12345, "Reminder: Pay rent")
        self.assertTrue(reminder_manager.load_reminders()["reminders"][0]["notified"])

    def test_only_timed_incomplete_and_addressable_reminders_are_sent(self):
        self.write_reminders([
            {"title": "Date only", "done": False, "due_at": "2030-06-01", "chat_id": 1},
            {"title": "No recipient", "done": False, "due_at": "2030-06-01 08:00"},
            {"title": "Completed", "done": True, "due_at": "2030-06-01 08:00", "chat_id": 2},
            {"title": "Future", "done": False, "due_at": "2030-06-02 10:00", "chat_id": 3},
            {"title": "Due now", "done": False, "due_at": "2030-06-01 08:00", "chat_id": 4},
        ])
        sender = Mock()

        sent_count = reminder_scheduler.check_due_reminders(
            sender, now=datetime(2030, 6, 1, 8, 0)
        )

        self.assertEqual(sent_count, 1)
        sender.assert_called_once_with(4, "Reminder: Due now")

    def test_failed_read_does_not_send_or_write(self):
        original_bytes = b'{"reminders": broken}'
        self.reminders_file.write_bytes(original_bytes)
        sender = Mock()

        with self.assertLogs(reminder_scheduler.logger, level="ERROR"):
            sent_count = reminder_scheduler.check_due_reminders(
                sender, now=datetime(2030, 6, 1, 8, 0)
            )

        self.assertEqual(sent_count, 0)
        sender.assert_not_called()
        self.assertEqual(self.reminders_file.read_bytes(), original_bytes)

    def test_failed_save_prevents_notification(self):
        self.write_reminders([
            {
                "title": "Pay rent",
                "done": False,
                "due_at": "2030-06-01 08:00",
                "chat_id": 12345,
            }
        ])
        original_bytes = self.reminders_file.read_bytes()
        sender = Mock()

        with patch.object(
            reminder_manager, "save_reminders", side_effect=OSError("disk full")
        ):
            with self.assertLogs(reminder_scheduler.logger, level="ERROR"):
                sent_count = reminder_scheduler.check_due_reminders(
                    sender, now=datetime(2030, 6, 1, 8, 0)
                )

        self.assertEqual(sent_count, 0)
        sender.assert_not_called()
        self.assertEqual(self.reminders_file.read_bytes(), original_bytes)

    def test_sender_failure_does_not_repeat_on_later_check(self):
        self.write_reminders([
            {
                "title": "Pay rent",
                "done": False,
                "due_at": "2030-06-01 08:00",
                "chat_id": 12345,
            }
        ])
        sender = Mock(side_effect=OSError("delivery uncertain"))
        now = datetime(2030, 6, 1, 8, 0)

        with self.assertLogs(reminder_scheduler.logger, level="ERROR"):
            first_check = reminder_scheduler.check_due_reminders(sender, now=now)
        second_check = reminder_scheduler.check_due_reminders(sender, now=now)

        self.assertEqual(first_check, 0)
        self.assertEqual(second_check, 0)
        sender.assert_called_once()

    def test_scheduler_starts_a_daemon_thread_without_blocking(self):
        fake_thread = Mock()
        with patch.object(
            reminder_scheduler.threading, "Event", return_value=object()
        ), patch.object(reminder_scheduler.threading, "Thread", return_value=fake_thread) as thread:
            stop_event, started_thread = reminder_scheduler.start_scheduler(
                Mock(), interval_seconds=15
            )

        self.assertIs(started_thread, fake_thread)
        self.assertIsNotNone(stop_event)
        thread.assert_called_once()
        self.assertTrue(thread.call_args.kwargs["daemon"])
        fake_thread.start.assert_called_once_with()

    def test_polling_lifecycle_starts_once_and_stops_scheduler_on_exit(self):
        bot = Mock()
        stop_event = Mock()
        scheduler_thread = Mock()
        with patch.object(
            reminder_scheduler,
            "start_scheduler",
            return_value=(stop_event, scheduler_thread),
        ) as start_scheduler:
            reminder_scheduler.run_with_polling(bot, Mock())

        start_scheduler.assert_called_once()
        bot.infinity_polling.assert_called_once_with()
        stop_event.set.assert_called_once_with()
        scheduler_thread.join.assert_called_once_with(timeout=5)

    def test_polling_lifecycle_stops_scheduler_when_polling_raises(self):
        bot = Mock()
        bot.infinity_polling.side_effect = KeyboardInterrupt
        stop_event = Mock()
        scheduler_thread = Mock()
        with patch.object(
            reminder_scheduler,
            "start_scheduler",
            return_value=(stop_event, scheduler_thread),
        ) as start_scheduler:
            with self.assertRaises(KeyboardInterrupt):
                reminder_scheduler.run_with_polling(bot, Mock())

        start_scheduler.assert_called_once()
        stop_event.set.assert_called_once_with()
        scheduler_thread.join.assert_called_once_with(timeout=5)

    def test_scheduler_loop_checks_immediately_before_waiting(self):
        class StopAfterFirstWait:
            def __init__(self):
                self.stopped = False

            def is_set(self):
                return self.stopped

            def wait(self, interval_seconds):
                self.stopped = True
                return True

        stop_event = StopAfterFirstWait()
        sender = Mock()
        with patch.object(reminder_scheduler, "check_due_reminders") as check:
            reminder_scheduler._run_scheduler(sender, 30, stop_event)

        check.assert_called_once_with(sender)

    def test_concurrent_adds_are_not_lost_during_scheduler_updates(self):
        scheduled = {
            "title": "Due now",
            "done": False,
            "due_at": "2030-06-01 08:00",
            "chat_id": 12345,
        }
        self.write_reminders([scheduled])
        sender = Mock()

        with ThreadPoolExecutor(max_workers=8) as executor:
            additions = [
                executor.submit(reminder_manager.add_reminder, f"Task {number}")
                for number in range(20)
            ]
            scheduled_check = executor.submit(
                reminder_scheduler.check_due_reminders,
                sender,
                datetime(2030, 6, 1, 8, 0),
            )
            for addition in additions:
                self.assertIn("Reminder added:", addition.result())
            self.assertEqual(scheduled_check.result(), 1)

        saved_reminders = reminder_manager.load_reminders()["reminders"]
        self.assertEqual(len(saved_reminders), 21)
        self.assertTrue(saved_reminders[0]["notified"])
        self.assertEqual(
            {reminder["title"] for reminder in saved_reminders[1:]},
            {f"Task {number}" for number in range(20)},
        )


if __name__ == "__main__":
    unittest.main()
