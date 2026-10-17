import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import project_manager
import reminder_manager
import session_manager
import state_manager
import terminal_ui


class TerminalSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        temp_path = Path(self.temp_dir.name)

        # Redirect every manager data path that this command flow could use.
        self.enterContext(
            patch.object(project_manager, "PROJECTS_FILE", temp_path / "projects.json")
        )
        self.enterContext(
            patch.object(reminder_manager, "REMINDERS_FILE", temp_path / "reminders.json")
        )
        self.enterContext(
            patch.object(session_manager, "SESSIONS_FILE", temp_path / "sessions.json")
        )
        self.enterContext(
            patch.object(state_manager, "STATE_FILE", temp_path / "state.json")
        )

    def test_terminal_command_flow_uses_temporary_data_and_no_external_services(self):
        commands = [
            "/projects",
            "/reminders",
            "/project_create Smoke Test",
            "/projects",
            "/project_switch Smoke Test",
            "/project_task_add Sample task",
            "/project_tasks",
            "/project_task_done 1",
            "/project_tasks",
            "/reminder_add Sample reminder",
            "/reminders",
            "/reminder_done 1",
            "/reminders",
            "/session_start",
            "/session_status",
            "/session_stop",
            "/project_stats",
            "exit",
        ]
        chat_history = []
        save_history = Mock()
        output = io.StringIO()

        # Slash commands must stay in the router; they must not call Gemini.
        with patch("builtins.input", side_effect=commands):
            with patch("terminal_ui.process_message") as process_message:
                with redirect_stdout(output):
                    terminal_ui.start_terminal(
                        state={},
                        projects={},
                        chat_history=chat_history,
                        client=None,
                        save_chat_history=save_history,
                    )

        process_message.assert_not_called()
        self.assertEqual(save_history.call_count, len(commands) - 1)
        save_history.assert_called_with(chat_history)
        terminal_output = output.getvalue()

        expected_results = [
            "No projects found.",
            "No reminders found.",
            "Created project: Smoke Test",
            "- Smoke Test",
            "Active project: Smoke Test",
            "Task added to Smoke Test",
            "1. [ ] Sample task",
            "Completed: Sample task",
            "1. [x] Sample task",
            "Reminder added: Sample reminder",
            "1. [ ] Sample reminder",
            "Completed: Sample reminder",
            "1. [x] Sample reminder",
            "Session started.\nProject: Smoke Test",
            "Active Session\nProject: Smoke Test",
            "Session completed.\nDuration: ",
            "Project: Smoke Test\n\nSessions: 1\nTotal Time: ",
            "Average Session: ",
            "Last Session:",
        ]
        for expected in expected_results:
            with self.subTest(expected=expected):
                self.assertIn(expected, terminal_output)

        self.assertTrue(project_manager.PROJECTS_FILE.is_file())
        self.assertTrue(reminder_manager.REMINDERS_FILE.is_file())
        self.assertTrue(session_manager.SESSIONS_FILE.is_file())
        self.assertFalse(state_manager.STATE_FILE.exists())


if __name__ == "__main__":
    unittest.main()
