import json
import os
from pathlib import Path
import stat
import tempfile

BASE_DIR = Path(__file__).resolve().parent

PROJECTS_FILE = BASE_DIR / "projects.json"


def load_projects():

    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        return {
            "active_project": None,
            "projects": {}
        }


def save_projects(data):

    serialized = json.dumps(data, indent=4)
    destination = Path(PROJECTS_FILE).resolve()

    try:
        existing_mode = stat.S_IMODE(destination.stat().st_mode)
    except FileNotFoundError:
        existing_mode = None

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(serialized)
            temporary_file.flush()

        if existing_mode is not None:
            os.chmod(temporary_path, existing_mode)

        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass

def list_projects():

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    if not projects["projects"]:
        return "No projects found."

    output = "Projects:\n\n"

    for project_name in projects["projects"]:

        marker = ""

        if project_name == projects["active_project"]:
            marker = " (ACTIVE)"

        output += f"- {project_name}{marker}\n"

    return output

def create_project(name):

    if not name.strip():
        return "Usage: /project_create Project Name"

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    for existing_project in projects["projects"]:

        if existing_project.lower() == name.lower():
            return "Project already exists."

    projects["projects"][name] = {
        "tasks": [],
        "created": ""
    }

    try:
        save_projects(projects)
    except (OSError, TypeError, ValueError):
        return "Could not save projects data. Check projects.json and try again."

    return f"Created project: {name}"

def switch_project(name):

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    search_name = name.lower()

    matched_project = None

    for existing_project in projects["projects"]:

        if existing_project.lower() == search_name:
            matched_project = existing_project
            break

    if matched_project is None:
        return "Project not found."

    projects["active_project"] = matched_project

    try:
        save_projects(projects)
    except (OSError, TypeError, ValueError):
        return "Could not save projects data. Check projects.json and try again."

    return f"Active project: {matched_project}"

def add_project_task(task_name):

    if not task_name.strip():
        return "Usage: /project_task_add Task Name"

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project."

    projects["projects"][active_project]["tasks"].append(
        {
            "task": task_name,
            "done": False
        }
    )

    try:
        save_projects(projects)
    except (OSError, TypeError, ValueError):
        return "Could not save projects data. Check projects.json and try again."

    return f"Task added to {active_project}"

def get_project_tasks():

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project."

    tasks = projects["projects"][active_project]["tasks"]

    if not tasks:
        return f"Project: {active_project}\n\nNo tasks found."

    output = f"Project: {active_project}\n\n"

    for index, task in enumerate(tasks, start=1):

        status = "[x]" if task["done"] else "[ ]"

        output += f"{index}. {status} {task['task']}\n"

    return output

def complete_project_task(task_number):

    try:
        projects = load_projects()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read projects data. Check projects.json."

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project."

    tasks = projects["projects"][active_project]["tasks"]

    if task_number < 1 or task_number > len(tasks):
        return "Invalid task number."

    task = tasks[task_number - 1]

    if task["done"]:
        return "Task already completed."

    task["done"] = True

    try:
        save_projects(projects)
    except (OSError, TypeError, ValueError):
        return "Could not save projects data. Check projects.json and try again."

    return f"Completed: {task['task']}"

