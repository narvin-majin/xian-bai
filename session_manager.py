import json
from pathlib import Path
from datetime import datetime
from project_manager import load_projects
from project_manager import load_projects

BASE_DIR = Path(__file__).resolve().parent

SESSIONS_FILE = BASE_DIR / "sessions.json"


def load_sessions():

    try:
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return {
            "active_session": None,
            "sessions": []
        }


def save_sessions(data):

    with open(SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)



def start_session():

    sessions = load_sessions()

    if sessions["active_session"] is not None:
        return "A session is already running."

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project. Use /project_switch first."

    sessions["active_session"] = {
        "project": active_project,
        "start": datetime.now().isoformat()
    }

    save_sessions(sessions)

    return (
        "Session started.\n"
        f"Project: {active_project}"
    )

def stop_session():

    sessions = load_sessions()

    active_session = sessions["active_session"]

    if active_session is None:
        return "No active session."

    end_time = datetime.now()

    start_time = datetime.fromisoformat(
        active_session["start"]
    )

    duration = int(
        (end_time - start_time).total_seconds() / 60
    )

    sessions["sessions"].append(
        {
            "project": active_session["project"],
            "start": active_session["start"],
            "end": end_time.isoformat(),
            "duration_minutes": duration
        }
    )

    sessions["active_session"] = None

    save_sessions(sessions)

    return (
        "Session completed.\n"
        f"Duration: {duration} minutes"
    )

def get_session_status():

    sessions = load_sessions()

    active_session = sessions["active_session"]

    if active_session is None:
        return "No active session."

    return (
        "Active Session\n"
        f"Project: {active_session['project']}\n"
        f"Started: {active_session['start']}"
    )

def get_project_stats():

    sessions = load_sessions()

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:
        return "No active project."

    project_sessions = []

    for session in sessions["sessions"]:

        if session["project"] == active_project:
            project_sessions.append(session)

    if not project_sessions:
        return "No sessions found for this project."

    total_minutes = sum(
        session["duration_minutes"]
        for session in project_sessions
    )

    average = int(
        total_minutes / len(project_sessions)
    )

    last_session = project_sessions[-1]["end"]

    return (
        f"Project: {active_project}\n\n"
        f"Sessions: {len(project_sessions)}\n"
        f"Total Time: {total_minutes} minutes\n"
        f"Average Session: {average} minutes\n"
        f"Last Session:\n"
        f"{last_session}"
    )