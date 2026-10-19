import re
import shlex

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

from session_manager import (
    start_session,
    stop_session,
    get_session_status,
    get_project_stats
)

from reminder_manager import (
    add_reminder,
    list_reminders,
    complete_reminder,
    reschedule_reminder,
)
import reminder_manager
import preview_manager


def _preview_session_key(chat_id):
    return preview_manager.session_key(chat_id)

def _has_command_boundary(command, command_name):
    return command == command_name or (
        command.startswith(command_name)
        and command[len(command_name)].isspace()
    )


def _edit_pending_reminder(command, chat_id):
    session_key = _preview_session_key(chat_id)
    usage = 'Usage: /edit [--title "new title"] [--date YYYY-MM-DD] [--time HH:MM]'
    try:
        arguments = shlex.split(command)
    except ValueError:
        return "Malformed /edit command. Quote titles with double quotes. " + usage

    if len(arguments) < 2:
        return usage

    updates = {}
    index = 1
    while index < len(arguments):
        option = arguments[index]
        if option not in ("--title", "--date", "--time"):
            return f"Unknown or malformed edit option: {option}. {usage}"
        if option in updates:
            return f"Edit option {option} may only be used once."
        if index + 1 >= len(arguments) or arguments[index + 1].startswith("--"):
            return f"Missing value for {option}. {usage}"

        updates[option] = arguments[index + 1]
        index += 2

    with preview_manager.lock_preview(session_key):
        preview = preview_manager.get_preview(session_key)
        if preview is None:
            return "There is no pending reminder preview to edit."
        if not isinstance(preview, dict) or preview.get("type") != "reminder":
            return "Invalid preview. The pending draft was kept."

        candidate = dict(preview)
        if "--title" in updates:
            title = updates["--title"].strip()
            if not title:
                return "Reminder title cannot be empty. The pending draft was kept."
            candidate["title"] = title

        if not isinstance(candidate.get("title"), str) or not candidate["title"].strip():
            return "Invalid reminder preview: title is required. The pending draft was kept."

        due_at = candidate.get("due_at")
        if "--date" in updates:
            date_value = updates["--date"]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
                return "Invalid date. Use YYYY-MM-DD. The pending draft was kept."
            existing_time = None
            if isinstance(due_at, str) and " " in due_at:
                existing_time = due_at.partition(" ")[2]
            due_at = f"{date_value} {existing_time}" if existing_time else date_value

        if "--time" in updates:
            time_value = updates["--time"]
            if not re.fullmatch(r"\d{2}:\d{2}", time_value):
                return "Invalid time. Use HH:MM. The pending draft was kept."
            if not isinstance(due_at, str):
                return "Set a due date before adding a time. The pending draft was kept."
            date_value = due_at.split(" ", 1)[0]
            due_at = f"{date_value} {time_value}"

        if due_at is not None and not reminder_manager._is_valid_due_at(due_at):
            return (
                "Invalid date/time. Use YYYY-MM-DD or YYYY-MM-DD HH:MM. "
                "The pending draft was kept."
            )

        candidate["due_at"] = due_at
        preview_manager.set_preview(session_key, candidate)
        return f"{preview_manager.format_preview(candidate)}\nEdit saved to preview. Reply /confirm to save or /cancel to discard."


def handle_command(command, chat_id=None):

    if command == "/confirm":
        session_key = _preview_session_key(chat_id)
        with preview_manager.lock_preview(session_key):
            preview = preview_manager.get_preview(session_key)
            if preview is None:
                return "There is no pending preview to confirm."

            if not isinstance(preview, dict) or preview.get("type") != "reminder":
                return "Invalid preview. The pending draft was kept."

            title = preview.get("title")
            due_at = preview.get("due_at")
            if not isinstance(title, str) or not title.strip():
                return "Invalid reminder preview: title is required. The pending draft was kept."

            if due_at is not None and not reminder_manager._is_valid_due_at(due_at):
                return (
                    "Invalid due date/time. Use YYYY-MM-DD or "
                    "YYYY-MM-DD HH:MM. The pending draft was kept."
                )

            if chat_id is None:
                result = add_reminder(title, due_at)
            else:
                result = add_reminder(title, due_at, chat_id=chat_id)

            if result.startswith("Reminder added: "):
                preview_manager.clear_preview(session_key)
            return result

    if command == "/cancel":
        session_key = _preview_session_key(chat_id)
        with preview_manager.lock_preview(session_key):
            if preview_manager.clear_preview(session_key) is None:
                return "There is no pending preview to cancel."
            return "Pending preview cancelled."

    if _has_command_boundary(command, "/edit"):
        return _edit_pending_reminder(command, chat_id)


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
            
    if command == "/session_start":

        return start_session()


    if command == "/session_stop":

        return stop_session()
    
    if command == "/session_status":
        return get_session_status()
    
    if command == "/project_stats":
        return get_project_stats()
    
    if _has_command_boundary(command, "/reminder_add"):

        reminder_text = command[len("/reminder_add"):].strip()
        reminder_parts = reminder_text.split()
        due_indexes = [
            index for index, part in enumerate(reminder_parts)
            if part.startswith("--due")
        ]

        if due_indexes:
            due_index = due_indexes[0]
            title = " ".join(reminder_parts[:due_index])
            if len(due_indexes) == 1 and reminder_parts[due_index] == "--due":
                due_at = " ".join(reminder_parts[due_index + 1:])
            else:
                # Treat malformed due options as invalid dates, never as title text.
                due_at = ""

            if chat_id is not None:
                return add_reminder(
                    title, due_at, chat_id=chat_id
                )
            return add_reminder(title, due_at)

        return add_reminder(reminder_text)


    if command == "/reminders":

        return list_reminders()


    if _has_command_boundary(command, "/reminder_done"):

        reminder_number = command.replace(
            "/reminder_done",
            ""
        ).strip()

        try:
            reminder_number = int(reminder_number)

        except ValueError:
            return "Reminder number must be a number."

        return complete_reminder(reminder_number)

    if _has_command_boundary(command, "/reminder_reschedule"):
        arguments = command[len("/reminder_reschedule"):].strip().split()
        if not arguments:
            return "Reminder number must be a number."

        try:
            reminder_number = int(arguments[0])
        except ValueError:
            return "Reminder number must be a number."

        if len(arguments) < 3 or arguments[1] != "--due":
            return (
                "Usage: /reminder_reschedule <number> --due "
                "<YYYY-MM-DD or YYYY-MM-DD HH:MM>"
            )

        due_at = " ".join(arguments[2:])
        return reschedule_reminder(reminder_number, due_at)

    return "Unknown command."

