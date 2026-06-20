import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CHAT_HISTORY_FILE = BASE_DIR / "chat_history.json"


def load_chat_history():

    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return []


def save_chat_history(chat_history):

    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)