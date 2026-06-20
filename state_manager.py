import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

STATE_FILE = BASE_DIR / "state.json"

# ==================================================
# STATE
# ==================================================

def load_state():

    defaults = {
        "current_task": "none",
        "status": "idle",
        "streak": 0,
        "focus_level": 5,
        "fatigue_level": 0
    }

    try:

        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        for key, value in defaults.items():

            if key not in state:
                state[key] = value

        return state

    except Exception:

        return defaults


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def track_task(task):

    if not task:
        return "Use: /track Python"

    state = load_state()

    state["current_task"] = task
    state["status"] = "working"

    save_state(state)

    return f"Tracking: {task}"

def complete_task():

    state = load_state()

    if state["current_task"] == "none":
        return "No active task. Use /track first."

    state["status"] = "idle"
    state["current_task"] = "none"
    state["streak"] += 1

    save_state(state)

    return "Nice. Marked as done."

def get_status():

    state = load_state()

    return (
        f"Task: {state['current_task']}\n"
        f"Status: {state['status']}\n"
        f"Streak: {state['streak']}\n"
        f"Focus: {state['focus_level']}\n"
        f"Fatigue: {state['fatigue_level']}"
    )