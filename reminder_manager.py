import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

REMINDERS_FILE = BASE_DIR / "reminders.json"


def load_reminders():

    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return {
            "reminders": []
        }


def save_reminders(data):

    with open(REMINDERS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_reminder(title):

    if not title:
        return "Usage: /reminder_add Reminder"

    reminders = load_reminders()

    reminders["reminders"].append(
        {
            "title": title,
            "done": False,
            "created": datetime.now().isoformat()
        }
    )

    save_reminders(reminders)

    return f"Reminder added: {title}"


def list_reminders():

    reminders = load_reminders()

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

    reminders = load_reminders()

    reminder_list = reminders["reminders"]

    if reminder_number < 1 or reminder_number > len(reminder_list):
        return "Invalid reminder number."

    reminder = reminder_list[reminder_number - 1]

    if reminder["done"]:
        return "Reminder already completed."

    reminder["done"] = True

    save_reminders(reminders)

    return f"Completed: {reminder['title']}"