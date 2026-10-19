import json
import threading
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import command_router
import preview_manager
import project_manager
import reminder_manager


class PreviewManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.reminders_file = root / "reminders.json"
        self.projects_file = root / "projects.json"
        self.reminders_patch = patch.object(
            reminder_manager, "REMINDERS_FILE", self.reminders_file
        )
        self.projects_patch = patch.object(
            project_manager, "PROJECTS_FILE", self.projects_file
        )
        self.reminders_patch.start()
        self.projects_patch.start()
        self.addCleanup(self.reminders_patch.stop)
        self.addCleanup(self.projects_patch.stop)
        self.session_keys = []

    def set_preview(self, session_key, preview):
        self.session_keys.append(session_key)
        preview_manager.set_preview(session_key, preview)

    def tearDown(self):
        for session_key in self.session_keys:
            preview_manager.clear_preview(session_key)

    def test_preview_can_be_set_retrieved_formatted_and_cleared(self):
        key = ("terminal",)
        preview = {"type": "reminder", "title": "Pay rent", "due_at": "2030-06-01"}
        self.set_preview(key, preview)

        self.assertEqual(preview_manager.get_preview(key), preview)
        self.assertEqual(
            preview_manager.format_preview(preview),
            "Reminder preview: Pay rent (due: 2030-06-01)",
        )
        self.assertEqual(preview_manager.clear_preview(key), preview)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_confirm_saves_valid_reminder_once_and_clears_preview(self):
        key = ("telegram", 1001)
        self.set_preview(
            key,
            {"type": "reminder", "title": "Call dentist", "due_at": "2030-06-02 09:30"},
        )

        with patch.object(command_router, "add_reminder", wraps=reminder_manager.add_reminder) as add:
            result = command_router.handle_command("/confirm", chat_id=1001)

        self.assertEqual(result, "Reminder added: Call dentist")
        add.assert_called_once_with("Call dentist", "2030-06-02 09:30", chat_id=1001)
        saved = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["reminders"]), 1)
        self.assertEqual(saved["reminders"][0]["chat_id"], 1001)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_cancel_clears_preview_without_changing_reminder_or_project_data(self):
        self.reminders_file.write_text('{"reminders": []}', encoding="utf-8")
        self.projects_file.write_text(
            '{"active_project": null, "projects": {}}', encoding="utf-8"
        )
        original_reminders = self.reminders_file.read_bytes()
        original_projects = self.projects_file.read_bytes()
        key = ("terminal",)
        self.set_preview(key, {"type": "reminder", "title": "Discard this"})

        result = command_router.handle_command("/cancel")

        self.assertEqual(result, "Pending preview cancelled.")
        self.assertIsNone(preview_manager.get_preview(key))
        self.assertEqual(self.reminders_file.read_bytes(), original_reminders)
        self.assertEqual(self.projects_file.read_bytes(), original_projects)

    def test_confirm_without_draft_returns_clear_message(self):
        self.assertEqual(
            command_router.handle_command("/confirm"),
            "There is no pending preview to confirm.",
        )

    def test_edit_can_change_title_date_and_time_together(self):
        key = ("terminal",)
        self.set_preview(
            key,
            {"type": "reminder", "title": "Call dentist", "due_at": "2030-06-02"},
        )

        result = command_router.handle_command(
            '/edit --title "Call my dentist" --date 2030-06-03 --time 09:30'
        )

        self.assertIn("Reminder preview: Call my dentist (due: 2030-06-03 09:30)", result)
        self.assertEqual(
            preview_manager.get_preview(key),
            {
                "type": "reminder",
                "title": "Call my dentist",
                "due_at": "2030-06-03 09:30",
            },
        )

    def test_edit_title_only_and_date_only_preserve_existing_values(self):
        key = ("terminal",)
        self.set_preview(
            key,
            {"type": "reminder", "title": "Old title", "due_at": "2030-06-02 08:15"},
        )

        command_router.handle_command('/edit --title "New title with spaces"')
        self.assertEqual(preview_manager.get_preview(key)["due_at"], "2030-06-02 08:15")
        self.assertEqual(
            preview_manager.get_preview(key)["title"], "New title with spaces"
        )

        command_router.handle_command("/edit --date 2030-06-04")
        self.assertEqual(
            preview_manager.get_preview(key)["due_at"], "2030-06-04 08:15"
        )

    def test_editing_time_promotes_date_only_draft_to_timed(self):
        key = ("terminal",)
        self.set_preview(
            key, {"type": "reminder", "title": "Buy books", "due_at": "2030-06-02"}
        )

        result = command_router.handle_command("/edit --time 17:45")

        self.assertIn("due: 2030-06-02 17:45", result)
        self.assertEqual(
            preview_manager.get_preview(key)["due_at"], "2030-06-02 17:45"
        )

    def test_invalid_edit_and_malformed_command_preserve_original_preview(self):
        key = ("terminal",)
        original = {
            "type": "reminder",
            "title": "Keep this draft",
            "due_at": "2030-06-02 08:15",
        }
        self.set_preview(key, original)

        for command in (
            '/edit --title "Changed" --date 2030-02-30',
            "/edit --time 25:61",
            '/edit --title "',
            "/edit --color blue",
        ):
            with self.subTest(command=command):
                result = command_router.handle_command(command)
                self.assertTrue(result)
                self.assertEqual(preview_manager.get_preview(key), original)

    def test_edit_without_draft_returns_clear_message(self):
        result = command_router.handle_command('/edit --title "No draft"')
        self.assertEqual(result, "There is no pending reminder preview to edit.")

    def test_cancel_after_edit_discards_only_the_in_memory_draft(self):
        key = ("terminal",)
        self.set_preview(key, {"type": "reminder", "title": "Original"})
        self.reminders_file.write_text('{"reminders": []}', encoding="utf-8")
        self.projects_file.write_text(
            '{"active_project": null, "projects": {}}', encoding="utf-8"
        )
        reminders_before = self.reminders_file.read_bytes()
        projects_before = self.projects_file.read_bytes()

        command_router.handle_command('/edit --title "Edited draft"')
        self.assertEqual(
            command_router.handle_command("/cancel"), "Pending preview cancelled."
        )

        self.assertEqual(self.reminders_file.read_bytes(), reminders_before)
        self.assertEqual(self.projects_file.read_bytes(), projects_before)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_confirmation_saves_edited_preview_and_clears_it(self):
        key = ("telegram", 7444)
        self.set_preview(
            key,
            {"type": "reminder", "title": "Old title", "due_at": "2030-06-02"},
        )
        command_router.handle_command(
            '/edit --title "Edited title" --time 10:20', chat_id=7444
        )

        result = command_router.handle_command("/confirm", chat_id=7444)

        self.assertEqual(result, "Reminder added: Edited title")
        saved = json.loads(self.reminders_file.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["reminders"]), 1)
        self.assertEqual(saved["reminders"][0]["title"], "Edited title")
        self.assertEqual(saved["reminders"][0]["due_at"], "2030-06-02 10:20")
        self.assertEqual(saved["reminders"][0]["chat_id"], 7444)
        self.assertIsNone(preview_manager.get_preview(key))

    def test_edit_waits_for_confirmation_and_then_sees_no_pending_draft(self):
        key = ("telegram", 7555)
        self.set_preview(key, {"type": "reminder", "title": "Confirm first"})
        save_started = threading.Event()
        release_save = threading.Event()

        def save_reminder(title, due_at=None, chat_id=None):
            save_started.set()
            if not release_save.wait(timeout=5):
                raise TimeoutError("Test did not release the save")
            return f"Reminder added: {title}"

        with patch.object(command_router, "add_reminder", side_effect=save_reminder):
            with ThreadPoolExecutor(max_workers=2) as executor:
                confirmation = executor.submit(
                    command_router.handle_command, "/confirm", 7555
                )
                self.assertTrue(save_started.wait(timeout=2))
                edit = executor.submit(
                    command_router.handle_command,
                    '/edit --title "Too late"',
                    7555,
                )
                self.assertFalse(edit.done())
                release_save.set()
                self.assertEqual(
                    confirmation.result(timeout=2), "Reminder added: Confirm first"
                )
                self.assertEqual(
                    edit.result(timeout=2),
                    "There is no pending reminder preview to edit.",
                )

        self.assertIsNone(preview_manager.get_preview(key))

    def test_invalid_draft_and_storage_failure_keep_preview(self):
        invalid_key = ("terminal",)
        self.set_preview(
            invalid_key,
            {"type": "reminder", "title": "Bad date", "due_at": "2030-02-30"},
        )
        invalid_result = command_router.handle_command("/confirm")
        self.assertIn("Invalid due date/time", invalid_result)
        self.assertIsNotNone(preview_manager.get_preview(invalid_key))
        self.assertFalse(self.reminders_file.exists())

        failure_key = ("telegram", 2002)
        self.set_preview(
            failure_key,
            {"type": "reminder", "title": "Storage failure"},
        )
        with patch.object(
            reminder_manager, "save_reminders", side_effect=OSError("disk full")
        ):
            failure_result = command_router.handle_command("/confirm", chat_id=2002)

        self.assertIn("Could not save reminders data", failure_result)
        self.assertIsNotNone(preview_manager.get_preview(failure_key))

        with patch.object(
            reminder_manager, "save_reminders", wraps=reminder_manager.save_reminders
        ) as save:
            retry_result = command_router.handle_command("/confirm", chat_id=2002)

        self.assertEqual(retry_result, "Reminder added: Storage failure")
        save.assert_called_once()
        self.assertIsNone(preview_manager.get_preview(failure_key))

    def test_concurrent_confirmations_for_one_session_save_only_once(self):
        key = ("telegram", 4001)
        self.set_preview(key, {"type": "reminder", "title": "One save"})
        first_save_started = threading.Event()
        release_first_save = threading.Event()
        second_lock_requested = threading.Event()
        call_count = 0
        count_lock = threading.Lock()
        original_lock_preview = preview_manager.lock_preview

        @contextmanager
        def observe_lock_request(session_key):
            nonlocal call_count
            with count_lock:
                call_count += 1
                if call_count == 2:
                    second_lock_requested.set()
            with original_lock_preview(session_key):
                yield

        def save_reminder(title, due_at=None, chat_id=None):
            first_save_started.set()
            if not release_first_save.wait(timeout=5):
                raise TimeoutError("Test did not release the first save")
            return f"Reminder added: {title}"

        with patch.object(preview_manager, "lock_preview", observe_lock_request):
            with patch.object(command_router, "add_reminder", side_effect=save_reminder) as add:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    first = executor.submit(
                        command_router.handle_command, "/confirm", 4001
                    )
                    self.assertTrue(first_save_started.wait(timeout=2))
                    second = executor.submit(
                        command_router.handle_command, "/confirm", 4001
                    )
                    self.assertTrue(second_lock_requested.wait(timeout=2))
                    release_first_save.set()
                    results = (first.result(timeout=2), second.result(timeout=2))

        self.assertEqual(add.call_count, 1)
        self.assertCountEqual(
            results,
            ["Reminder added: One save", "There is no pending preview to confirm."],
        )
        self.assertIsNone(preview_manager.get_preview(key))

    def test_different_sessions_can_confirm_while_one_save_is_blocked(self):
        first_key = ("telegram", 5001)
        second_key = ("telegram", 5002)
        self.set_preview(first_key, {"type": "reminder", "title": "First"})
        self.set_preview(second_key, {"type": "reminder", "title": "Second"})
        first_save_started = threading.Event()
        release_first_save = threading.Event()

        def save_reminder(title, due_at=None, chat_id=None):
            if title == "First":
                first_save_started.set()
                if not release_first_save.wait(timeout=5):
                    raise TimeoutError("Test did not release the first save")
            return f"Reminder added: {title}"

        with patch.object(command_router, "add_reminder", side_effect=save_reminder):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(
                    command_router.handle_command, "/confirm", 5001
                )
                self.assertTrue(first_save_started.wait(timeout=2))
                second = executor.submit(
                    command_router.handle_command, "/confirm", 5002
                )
                try:
                    self.assertEqual(second.result(timeout=2), "Reminder added: Second")
                finally:
                    release_first_save.set()
                self.assertEqual(first.result(timeout=2), "Reminder added: First")

        self.assertIsNone(preview_manager.get_preview(first_key))
        self.assertIsNone(preview_manager.get_preview(second_key))

    def test_cancel_waits_for_confirmation_and_cannot_duplicate_or_clear_early(self):
        key = ("telegram", 6001)
        self.set_preview(key, {"type": "reminder", "title": "Confirm wins"})
        first_save_started = threading.Event()
        release_first_save = threading.Event()
        cancel_lock_requested = threading.Event()
        lock_calls = 0
        count_lock = threading.Lock()
        original_lock_preview = preview_manager.lock_preview

        @contextmanager
        def observe_lock_request(session_key):
            nonlocal lock_calls
            with count_lock:
                lock_calls += 1
                if lock_calls == 2:
                    cancel_lock_requested.set()
            with original_lock_preview(session_key):
                yield

        def save_reminder(title, due_at=None, chat_id=None):
            first_save_started.set()
            if not release_first_save.wait(timeout=5):
                raise TimeoutError("Test did not release the save")
            return f"Reminder added: {title}"

        with patch.object(preview_manager, "lock_preview", observe_lock_request):
            with patch.object(command_router, "add_reminder", side_effect=save_reminder) as add:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    confirmation = executor.submit(
                        command_router.handle_command, "/confirm", 6001
                    )
                    self.assertTrue(first_save_started.wait(timeout=2))
                    cancellation = executor.submit(
                        command_router.handle_command, "/cancel", 6001
                    )
                    self.assertTrue(cancel_lock_requested.wait(timeout=2))
                    self.assertFalse(cancellation.done())
                    release_first_save.set()
                    confirm_result = confirmation.result(timeout=2)
                    cancel_result = cancellation.result(timeout=2)

        self.assertEqual(confirm_result, "Reminder added: Confirm wins")
        self.assertEqual(cancel_result, "There is no pending preview to cancel.")
        add.assert_called_once()
        self.assertIsNone(preview_manager.get_preview(key))

    def test_session_keys_isolate_telegram_chats_and_terminal(self):
        first_key = ("telegram", 3001)
        second_key = ("telegram", 3002)
        terminal_key = ("terminal",)
        self.set_preview(first_key, {"type": "reminder", "title": "First chat"})
        self.set_preview(second_key, {"type": "reminder", "title": "Second chat"})
        self.set_preview(terminal_key, {"type": "reminder", "title": "Terminal"})

        first_result = command_router.handle_command("/confirm", chat_id=3001)
        self.assertEqual(first_result, "Reminder added: First chat")
        self.assertIsNone(preview_manager.get_preview(first_key))
        self.assertEqual(
            preview_manager.get_preview(second_key)["title"], "Second chat"
        )
        self.assertEqual(
            preview_manager.get_preview(terminal_key)["title"], "Terminal"
        )
        self.assertEqual(
            command_router.handle_command("/confirm", chat_id=9999),
            "There is no pending preview to confirm.",
        )


if __name__ == "__main__":
    unittest.main()
