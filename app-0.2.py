import os
import json
from pathlib import Path
from datetime import datetime

from terminal_ui import start_terminal
from dotenv import load_dotenv
import telebot
from google import genai

# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

STATE_FILE = BASE_DIR / "state.json"
HISTORY_FILE = BASE_DIR / "history.json"
CHAT_HISTORY_FILE = BASE_DIR / "chat_history.json"

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PROJECTS_FILE = BASE_DIR / "projects.json"

# ==================================================
# ENV
# ==================================================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise SystemExit(
        "Missing TELEGRAM_TOKEN or GEMINI_API_KEY in .env"
    )

# ==================================================
# BOT + GEMINI
# ==================================================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# ==================================================
# STATE
# ==================================================

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "current_task": "none",
            "status": "idle",
            "streak": 0,
            "focus_level": 5,
            "fatigue_level": 0
        }


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


state = load_state()


# ==================================================
# PROJECTS
# ==================================================

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

projects = load_projects()

# ==================================================
# CHAT MEMORY
# ==================================================

def load_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_chat_history():
    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)


chat_history = load_chat_history()

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

# ==================================================
# COMMANDS
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Assistant ready.\n\n"
        "/track <task>\n"
        "/done\n"
        "/status"
    )


@bot.message_handler(commands=["track"])
def track(message):

    task = message.text.replace("/track", "").strip()

    if not task:
        bot.reply_to(
            message,
            "Use: /track Python"
        )
        return

    state["current_task"] = task
    state["status"] = "working"

    save_state()

    write_daily_log(
        f"TRACKED: {task}"
    )

    bot.reply_to(
        message,
        f"Tracking: {task}"
    )


@bot.message_handler(commands=["done"])
def done(message):

    if state["current_task"] == "none":

        bot.reply_to(
            message,
            "No active task. Use /track first."
        )
        return

    task = state["current_task"]

    state["status"] = "idle"
    state["current_task"] = "none"
    state["streak"] += 1

    save_state()

    log_history(
        task,
        "done"
    )

    write_daily_log(
        f"DONE: {task}"
    )

    bot.reply_to(
        message,
        "Nice. Marked as done."
    )


@bot.message_handler(commands=["status"])
def status(message):

    bot.reply_to(
        message,
        f"Task: {state['current_task']}\n"
        f"Status: {state['status']}\n"
        f"Streak: {state['streak']}\n"
        f"Focus: {state['focus_level']}\n"
        f"Fatigue: {state['fatigue_level']}"
    )

@bot.message_handler(commands=["project_create"])
def project_create(message):

    name = message.text.replace(
        "/project_create",
        ""
    ).strip()

    if not name:

        bot.reply_to(
            message,
            "Usage: /project_create ProjectName"
        )

        return

    for existing_project in projects["projects"]:

        if existing_project.lower() == name.lower():

            bot.reply_to(
                message,
                "Project already exists."
            )

            return

    projects["projects"][name] = {
        "tasks": [],
        "notes": [],
        "sessions": [],
        "created": datetime.now().isoformat()
    }

    save_projects(projects)                         #changed 16-06-2026

    bot.reply_to(
        message,
        f"Created project: {name}"
    )

@bot.message_handler(commands=["projects"])
def list_projects(message):

    if not projects["projects"]:

        bot.reply_to(
            message,
            "No projects found."
        )

        return

    output = "Projects:\n\n"

    for project_name in projects["projects"]:

        marker = ""

        if project_name == projects["active_project"]:
            marker = " (ACTIVE)"

        output += f"- {project_name}{marker}\n"

    bot.reply_to(
        message,
        output
    )


@bot.message_handler(commands=["project_switch"])
def project_switch(message):

    global projects

    project_name = (
        message.text
        .replace("/project_switch", "")
        .strip()
    )

    if not project_name:
        bot.reply_to(
            message,
            "Use: /project_switch Project Name"
        )
        return

    projects = load_projects()

    search_name = project_name.lower()

    matched_project = None

    for existing_project in projects["projects"]:
        if existing_project.lower() == search_name:
            matched_project = existing_project
            break

    if matched_project is None:
        bot.reply_to(message, "Project not found.")
        return

    projects["active_project"] = matched_project
    save_projects(projects)

    bot.reply_to(
        message,
        f"Active project: {matched_project}"
    )

@bot.message_handler(commands=["project_task_add"])
def project_task_add(message):

    global projects

    task_name = (
        message.text
        .replace("/project_task_add", "")
        .strip()
    )

    if not task_name:

        bot.reply_to(
            message,
            "Usage: /project_task_add Task Name"
        )

        return

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:

        bot.reply_to(
            message,
            "No active project. Use /project_switch first."
        )

        return

    projects["projects"][active_project]["tasks"].append(
        {
            "task": task_name,
            "done": False,
            "created": datetime.now().isoformat()
        }
    )

    save_projects(projects)

    bot.reply_to(
        message,
        f"Task added to {active_project}"
    )

@bot.message_handler(commands=["project_tasks"])
def project_tasks(message):

    global projects

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:

        bot.reply_to(
            message,
            "No active project."
        )

        return

    tasks = projects["projects"][active_project]["tasks"]

    if not tasks:

        bot.reply_to(
            message,
            f"Project: {active_project}\n\nNo tasks found."
        )

        return

    output = f"Project: {active_project}\n\n"

    for index, task in enumerate(tasks, start=1):

        status = "[x]" if task["done"] else "[ ]"

        output += (
            f"{index}. {status} {task['task']}\n"
        )

    bot.reply_to(
        message,
        output
    )

@bot.message_handler(commands=["project_task_done"])
def project_task_done(message):

    task_number = (
        message.text
        .replace("/project_task_done", "")
        .strip()
    )

    if not task_number:

        bot.reply_to(
            message,
            "Usage: /project_task_done TaskNumber"
        )

        return

    try:
        task_number = int(task_number)

    except ValueError:

        bot.reply_to(
            message,
            "Task number must be a number."
        )

        return

    global projects

    projects = load_projects()

    active_project = projects["active_project"]

    if active_project is None:

        bot.reply_to(
            message,
            "No active project."
        )

        return

    tasks = projects["projects"][active_project]["tasks"]

    if task_number < 1 or task_number > len(tasks):

        bot.reply_to(
            message,
            "Invalid task number."
        )

        return

    task = tasks[task_number - 1]

    if task["done"]:

        bot.reply_to(
            message,
            "Task already completed."
        )

        return

    task["done"] = True

    save_projects(projects)

    bot.reply_to(
        message,
        f"Completed: {task['task']}"
    )

# ==================================================
# CHAT
# ==================================================

@bot.message_handler(func=lambda message: True)
def chat(message):

    global chat_history

    

    user_text = message.text.strip()

    if user_text.startswith("/"):
        bot.reply_to(
            message,
            "Unknown command."
        )
        return

    chat_history.append(
        {
            "role": "user",
            "text": user_text
        }
    )

    recent_chat = "\n".join(
        [
            f"{msg['role']}: {msg['text']}"
            for msg in chat_history[-10:]
        ]
    )

    prompt = f"""
You are Xian Bai.

You are a direct, practical and friendly
personal productivity assistant.

Current State:
{state}

Active Project:
{projects["active_project"]}

Recent Conversation:
{recent_chat}
Keep answers concise.
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            #model="gemini-2.5",
            contents=prompt
        )

        reply = (
            response.text
            if response.text
            else "No response generated."
        )

    except Exception:

        reply = (
            "Gemini is busy right now. "
            "Please try again in a minute."
        )

    chat_history.append(
        {
            "role": "assistant",
            "text": reply
        }
    )

    chat_history = chat_history[-20:]

    save_chat_history()

    bot.reply_to(
        message,
        reply
    )

# ==================================================
# RUN
# ==================================================

# print("Bot is running...")

# bot.infinity_polling()

TEST_MODE = 1

if TEST_MODE:

    start_terminal(
        state,
        projects,
        chat_history,
        client,
        save_chat_history
    )

else:

    print("Bot is running...")
    bot.infinity_polling()