import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import project_manager
import session_manager


PROJECT_READ_ERROR = "Could not read projects data. Check projects.json."
STARTUP_READ_ERROR = (
    "Could not read projects data. Check projects.json before starting Xiao Bai."
)


class SessionErrorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        temp_path = Path(self.temp_dir.name)

        self.original_projects_file = project_manager.PROJECTS_FILE
        self.original_sessions_file = session_manager.SESSIONS_FILE
        project_manager.PROJECTS_FILE = temp_path / "projects.json"
        session_manager.SESSIONS_FILE = temp_path / "sessions.json"
        self.addCleanup(self.restore_file_paths)

    def restore_file_paths(self):
        project_manager.PROJECTS_FILE = self.original_projects_file
        session_manager.SESSIONS_FILE = self.original_sessions_file

    def test_start_session_returns_error_when_projects_cannot_load(self):
        read_errors = [
            json.JSONDecodeError("invalid JSON", "{", 1),
            OSError("read failed"),
        ]

        for error in read_errors:
            with self.subTest(error=type(error).__name__):
                with patch.object(
                    session_manager, "load_projects", side_effect=error
                ):
                    with patch.object(session_manager, "save_sessions") as save:
                        result = session_manager.start_session()

                self.assertEqual(result, PROJECT_READ_ERROR)
                save.assert_not_called()

    def test_project_stats_returns_error_when_projects_cannot_load(self):
        read_errors = [
            json.JSONDecodeError("invalid JSON", "{", 1),
            OSError("read failed"),
        ]

        for error in read_errors:
            with self.subTest(error=type(error).__name__):
                with patch.object(
                    session_manager, "load_projects", side_effect=error
                ):
                    result = session_manager.get_project_stats()

                self.assertEqual(result, PROJECT_READ_ERROR)


class StartupErrorTests(unittest.TestCase):
    def make_module(self, name, **attributes):
        module = ModuleType(name)
        for attribute, value in attributes.items():
            setattr(module, attribute, value)
        return module

    def test_startup_stops_clearly_when_project_data_cannot_load(self):
        read_errors = [
            json.JSONDecodeError("invalid JSON", "{", 1),
            OSError("read failed"),
        ]
        app_path = Path(__file__).resolve().parents[1] / "app.py"

        for error in read_errors:
            with self.subTest(error=type(error).__name__):
                load_projects = Mock(side_effect=error)
                telebot_client = Mock(side_effect=AssertionError("bot must not start"))
                gemini_client = Mock(side_effect=AssertionError("API must not start"))

                telebot_module = self.make_module("telebot")
                telebot_module.TeleBot = telebot_client
                google_module = self.make_module(
                    "google",
                    genai=SimpleNamespace(Client=gemini_client),
                )
                bot_module = self.make_module(
                    "project_manager", load_projects=load_projects
                )
                modules = {
                    "terminal_ui": self.make_module(
                        "terminal_ui", start_terminal=Mock()
                    ),
                    "telegram_ui": self.make_module(
                        "telegram_ui", register_handlers=Mock()
                    ),
                    "dotenv": self.make_module("dotenv", load_dotenv=Mock()),
                    "telebot": telebot_module,
                    "google": google_module,
                    "state_manager": self.make_module(
                        "state_manager", load_state=Mock(return_value={})
                    ),
                    "chat_manager": self.make_module(
                        "chat_manager",
                        load_chat_history=Mock(return_value=[]),
                        save_chat_history=Mock(),
                    ),
                    "project_manager": bot_module,
                }

                with patch.dict(sys.modules, modules):
                    with self.assertRaises(SystemExit) as raised:
                        runpy.run_path(str(app_path), run_name="xiaobai_startup_test")

                self.assertEqual(str(raised.exception), STARTUP_READ_ERROR)
                load_projects.assert_called_once()
                telebot_client.assert_not_called()
                gemini_client.assert_not_called()
