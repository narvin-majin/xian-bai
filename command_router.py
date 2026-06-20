from project_manager import (
    list_projects,
    create_project,
    switch_project,
    add_project_task,
    get_project_tasks,
    complete_project_task
)

from state_manager import (
    track_task,
    complete_task,
    get_status
)


def handle_command(command):


    if command == "/projects":
        return list_projects()

    if command.startswith("/project_create "):

        name = command.replace(
            "/project_create",
            ""
        ).strip()

        return create_project(name)
    
    if command.startswith("/project_switch "):

        name = command.replace(
            "/project_switch",
            ""
        ).strip()

        return switch_project(name)
    
    if command.startswith("/project_task_add "):

        task_name = command.replace(
            "/project_task_add",
            ""
        ).strip()

        return add_project_task(task_name)


    if command == "/project_tasks":
        return get_project_tasks()

    if command.startswith("/project_task_done "):

        task_number = command.replace(
            "/project_task_done",
            ""
        ).strip()

        try:
            task_number = int(task_number)
        except ValueError:
            return "Task number must be a number."

        return complete_project_task(task_number)
    

    if command.startswith("/track "):

        task = command.replace(
            "/track",
            ""
        ).strip()

        return track_task(task)
    
    if command == "/done":

        return complete_task()
    
    if command == "/status":

        return get_status()
            
    return "Unknown command."
