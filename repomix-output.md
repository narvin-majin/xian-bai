reminder_manager.py
[[
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

    reminders.append(
        {
            "title": title,
            "done": False,
            "created": datetime.now().isoformat()
        }
    )

    save_reminders(reminders)

    return f"Reminder added: {title}"

]]

reminders.json
[[
    {
    "reminders": []
}
]]