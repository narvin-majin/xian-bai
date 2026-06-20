import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PROJECTS_FILE = BASE_DIR / "projects.json"


def load_projects():

    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return {
            "active_project": None,
            "projects": {}
        }


def save_projects(data):

    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def list_projects():

    projects = load_projects()

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

    projects = load_projects()

    for existing_project in projects["projects"]:

        if existing_project.lower() == name.lower():
            return "Project already exists."

    projects["projects"][name] = {
        "tasks": [],
        "created": ""
    }

    save_projects(projects)

    return f"Created project: {name}"

def switch_project(name):

    projects = load_projects()

    search_name = name.lower()

    matched_project = None

    for existing_project in projects["projects"]:

        if existing_project.lower() == search_name:
            matched_project = existing_project
            break

    if matched_project is None:
        return "Project not found."

    projects["active_project"] = matched_project

    save_projects(projects)

    return f"Active project: {matched_project}"

def add_project_task(task_name):

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project."

    projects["projects"][active_project]["tasks"].append(
        {
            "task": task_name,
            "done": False
        }
    )

    save_projects(projects)

    return f"Task added to {active_project}"

def get_project_tasks():

    projects = load_projects()

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

    projects = load_projects()

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

    save_projects(projects)

    return f"Completed: {task['task']}"

