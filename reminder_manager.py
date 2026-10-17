import json
import os
from pathlib import Path
from datetime import datetime
import stat
import tempfile

BASE_DIR = Path(__file__).resolve().parent

REMINDERS_FILE = BASE_DIR / "reminders.json"


def load_reminders():

    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        return {
            "reminders": []
        }


def save_reminders(data):

    serialized = json.dumps(data, indent=4)
    destination = Path(REMINDERS_FILE).resolve()

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


def add_reminder(title):

    if not title.strip():
        return "Usage: /reminder_add Reminder"

    try:
        reminders = load_reminders()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read reminders data. Check reminders.json."

    reminders["reminders"].append(
        {
            "title": title,
            "done": False,
            "created": datetime.now().isoformat()
        }
    )

    try:
        save_reminders(reminders)
    except (OSError, TypeError, ValueError):
        return "Could not save reminders data. Check reminders.json and try again."

    return f"Reminder added: {title}"


def list_reminders():

    try:
        reminders = load_reminders()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read reminders data. Check reminders.json."

    reminder_list = reminders["reminders"]

    if not reminder_list:
        return "No reminders found."

    output = "Reminders:\n\n"

    for index, reminder in enumerate(reminder_list, start=1):

        status = "[x]" if reminder["done"] else "[ ]"

        output += (
            f"{index}. {status} {reminder['title']}\n"
        )

    return output

def complete_reminder(reminder_number):

    try:
        reminders = load_reminders()
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "Could not read reminders data. Check reminders.json."

    reminder_list = reminders["reminders"]

    if not isinstance(reminder_number, int):
        return "Reminder number must be a number."

    if reminder_number < 1 or reminder_number > len(reminder_list):
        return "Invalid reminder number."

    reminder = reminder_list[reminder_number - 1]

    if reminder["done"]:
        return "Reminder already completed."

    reminder["done"] = True

    try:
        save_reminders(reminders)
    except (OSError, TypeError, ValueError):
        return "Could not save reminders data. Check reminders.json and try again."

    return f"Completed: {reminder['title']}"
