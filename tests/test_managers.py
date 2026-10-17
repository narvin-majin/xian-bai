import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import project_manager


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


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        temp_path = Path(self.temp_dir.name)

        self.original_projects_file = project_manager.PROJECTS_FILE
        project_manager.PROJECTS_FILE = temp_path / "projects.json"
        self.addCleanup(self.restore_file_paths)

    def restore_file_paths(self):
        project_manager.PROJECTS_FILE = self.original_projects_file

    def test_create_project(self):
        result = project_manager.create_project("Study Python")

        self.assertEqual(result, "Created project: Study Python")
        self.assertEqual(
            project_manager.load_projects(),
            {
                "active_project": None,
                "projects": {
                    "Study Python": {"tasks": [], "created": ""}
                },
            },
        )

    def test_duplicate_project_name_ignores_case(self):
        project_manager.create_project("Study Python")

        result = project_manager.create_project("study python")

        self.assertEqual(result, "Project already exists.")
        self.assertEqual(len(project_manager.load_projects()["projects"]), 1)

    def test_blank_project_name_is_rejected(self):
        result = project_manager.create_project("")

        self.assertEqual(result, "Usage: /project_create Project Name")
        self.assertEqual(project_manager.load_projects()["projects"], {})

    def test_whitespace_only_project_name_is_rejected(self):
        result = project_manager.create_project("   ")

        self.assertEqual(result, "Usage: /project_create Project Name")
        self.assertEqual(project_manager.load_projects()["projects"], {})

    def test_project_task_can_be_added_and_completed(self):
        project_manager.create_project("Study Python")
        project_manager.switch_project("Study Python")

        add_result = project_manager.add_project_task("Read a chapter")
        done_result = project_manager.complete_project_task(1)

        self.assertEqual(add_result, "Task added to Study Python")
        self.assertEqual(done_result, "Completed: Read a chapter")
        self.assertEqual(
            project_manager.load_projects()["projects"]["Study Python"]["tasks"],
            [{"task": "Read a chapter", "done": True}],
        )

    def test_blank_project_task_is_rejected(self):
        project_manager.create_project("Study Python")
        project_manager.switch_project("Study Python")

        result = project_manager.add_project_task("")

        self.assertEqual(result, "Usage: /project_task_add Task Name")
        self.assertEqual(
            project_manager.load_projects()["projects"]["Study Python"]["tasks"],
            [],
        )

    def test_whitespace_only_project_task_is_rejected(self):
        project_manager.create_project("Study Python")
        project_manager.switch_project("Study Python")

        result = project_manager.add_project_task("   ")

        self.assertEqual(result, "Usage: /project_task_add Task Name")
        self.assertEqual(
            project_manager.load_projects()["projects"]["Study Python"]["tasks"],
            [],
        )

    def test_missing_projects_file_uses_empty_default(self):
        self.assertFalse(project_manager.PROJECTS_FILE.exists())
        self.assertEqual(
            project_manager.load_projects(),
            {"active_project": None, "projects": {}},
        )
        self.assertEqual(
            project_manager.create_project("First Project"),
            "Created project: First Project",
        )

    def test_malformed_projects_json_raises_and_create_preserves_bytes(self):
        original_bytes = b'{"projects": broken}'
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)

        with self.assertRaises(json.JSONDecodeError):
            project_manager.load_projects()

        result = project_manager.create_project("New Project")

        self.assertEqual(result, "Could not read projects data. Check projects.json.")
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)

    def test_projects_io_error_does_not_attempt_save(self):
        original_bytes = b"existing project data"
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)

        with patch("builtins.open", side_effect=PermissionError("read denied")):
            with patch.object(project_manager, "save_projects") as save:
                result = project_manager.create_project("New Project")

        self.assertEqual(result, "Could not read projects data. Check projects.json.")
        save.assert_not_called()
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)

    def test_all_project_operations_return_error_for_malformed_json(self):
        original_bytes = b'{"projects": broken}'
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)
        operations = [
            ("list", project_manager.list_projects),
            ("create", lambda: project_manager.create_project("New Project")),
            ("switch", lambda: project_manager.switch_project("Existing")),
            ("add task", lambda: project_manager.add_project_task("New task")),
            ("list tasks", project_manager.get_project_tasks),
            ("complete task", lambda: project_manager.complete_project_task(1)),
        ]

        with patch.object(project_manager, "save_projects") as save:
            for operation_name, operation in operations:
                with self.subTest(operation=operation_name):
                    result = operation()
                    self.assertEqual(
                        result,
                        "Could not read projects data. Check projects.json.",
                    )
                    self.assertEqual(
                        project_manager.PROJECTS_FILE.read_bytes(), original_bytes
                    )

        save.assert_not_called()

    def test_all_project_operations_return_error_for_io_failure(self):
        original_bytes = b"existing project data"
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)
        operations = [
            ("list", project_manager.list_projects),
            ("create", lambda: project_manager.create_project("New Project")),
            ("switch", lambda: project_manager.switch_project("Existing")),
            ("add task", lambda: project_manager.add_project_task("New task")),
            ("list tasks", project_manager.get_project_tasks),
            ("complete task", lambda: project_manager.complete_project_task(1)),
        ]

        with patch("builtins.open", side_effect=PermissionError("read denied")):
            with patch.object(project_manager, "save_projects") as save:
                for operation_name, operation in operations:
                    with self.subTest(operation=operation_name):
                        self.assertEqual(
                            operation(),
                            "Could not read projects data. Check projects.json.",
                        )

        save.assert_not_called()
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)

    def test_valid_projects_json_loads_and_saves(self):
        valid_data = {
            "active_project": None,
            "projects": {"Existing": {"tasks": [], "created": ""}},
        }
        project_manager.PROJECTS_FILE.write_text(
            json.dumps(valid_data), encoding="utf-8"
        )

        self.assertEqual(project_manager.load_projects(), valid_data)
        updated_data = {**valid_data, "active_project": "Existing"}
        project_manager.save_projects(updated_data)

        self.assertEqual(project_manager.load_projects(), updated_data)

    def test_project_write_failure_preserves_file_and_cleans_temporary_file(self):
        original_bytes = b'{"active_project": null, "projects": {}}'
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)

        with patch("os.replace", side_effect=OSError("replace failed")):
            result = project_manager.create_project("New Project")

        self.assertEqual(
            result, "Could not save projects data. Check projects.json and try again."
        )
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)
        self.assertEqual(
            list(project_manager.PROJECTS_FILE.parent.glob(".projects.json.*.tmp")),
            [],
        )

    def test_project_serialization_failure_preserves_file(self):
        original_bytes = b'{"active_project": null, "projects": {}}'
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)

        with patch.object(project_manager.json, "dumps", side_effect=TypeError):
            result = project_manager.create_project("New Project")

        self.assertEqual(
            result, "Could not save projects data. Check projects.json and try again."
        )
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)
        self.assertEqual(
            list(project_manager.PROJECTS_FILE.parent.glob(".projects.json.*.tmp")),
            [],
        )

    def test_project_partial_write_preserves_file_and_cleans_temporary_file(self):
        original_bytes = b'{"active_project": null, "projects": {}}'
        project_manager.PROJECTS_FILE.write_bytes(original_bytes)
        temporary_path = project_manager.PROJECTS_FILE.parent / ".projects.json.test.tmp"
        failing_temp_file = make_failing_temp_file(temporary_path)

        with patch.object(
            project_manager.tempfile,
            "NamedTemporaryFile",
            return_value=failing_temp_file,
        ):
            result = project_manager.create_project("New Project")

        self.assertEqual(
            result, "Could not save projects data. Check projects.json and try again."
        )
        self.assertEqual(project_manager.PROJECTS_FILE.read_bytes(), original_bytes)
        self.assertFalse(temporary_path.exists())

    def test_project_save_preserves_existing_file_permissions(self):
        project_manager.PROJECTS_FILE.write_text("{}", encoding="utf-8")
        project_manager.PROJECTS_FILE.chmod(0o640)

        project_manager.save_projects({"active_project": None, "projects": {}})

        self.assertEqual(
            stat.S_IMODE(project_manager.PROJECTS_FILE.stat().st_mode), 0o640
        )



if __name__ == "__main__":
    unittest.main()
