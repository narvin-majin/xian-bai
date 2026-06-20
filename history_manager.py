import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "history.json"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ==================================================
# HISTORY
# ==================================================

def log_history(task, status):
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except Exception:
        history = []

    history.append(
        {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "status": status
        }
    )

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# ==================================================
# DAILY LOGS
# ==================================================

def write_daily_log(message):
    today = datetime.now().strftime("%Y-%m-%d")

    log_file = LOGS_DIR / f"{today}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")