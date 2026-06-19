import os
from dotenv import load_dotenv
import telebot
from google import genai
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "state.json"

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

STATE_FILE = BASE_DIR / "state.json"
HISTORY_FILE = BASE_DIR / "history.json"

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("Missing TELEGRAM_TOKEN or GEMINI_API_KEY in .env")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# def save_state():
#     with open("state.json", "w") as f:
#         json.dump(state, f)
def save_state():
    # print("SAVE_STATE CALLED")
    print("Saving to:", os.path.abspath("state.json"))
    # with open("state.json", "w") as f:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

    print("Saved:", state)

def load_state():
    try:
        # with open("state.json", "r") as f:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "task": "none",
            "status": "idle",
            "streak": 0
        }

# state = {
#     # "task": "none",
#     # "status": "idle",
#     # "streak": 0

# }

def log_history(task, status):
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    history.append({
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "status": status
    })

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

state = load_state()

def write_daily_log(message):
    today = datetime.now().strftime("%Y-%m-%d")

    log_file = LOGS_DIR / f"{today}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")

    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Assistant is ready. Use /track Python, /done, or just chat."
    )

@bot.message_handler(commands=["track"])
def track(message):
    task = message.text.replace("/track", "").strip()
    if not task:
        bot.reply_to(message, "Use: /track Python")
        return
    state["task"] = task
    state["status"] = "working"
    save_state()

    bot.reply_to(message, f"Tracking: {task}")

    write_daily_log(f"TRACKED: {task}")

@bot.message_handler(commands=["done"])
def done(message):
    state["status"] = "done"
    state["streak"] += 1
    save_state()

    bot.reply_to(message, "Nice. Marked as done.")

    log_history(
        state["task"],
        "done"
    )

    write_daily_log(
        f"DONE: {state['task']}"
    )

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_text = message.text.strip()

    prompt = (
        "You are a direct, kind personal productivity coach. "
        f"Current state: {state}. "
        "Keep answers short, clear, and practical."
    )

    try:
        response = client.models.generate_content(
            # model="gemini-2.5-flash-lite",
            model="gemini-2.5-flash",
            contents=[prompt, user_text],
        )
        reply = response.text or "Gemini did not return text."
    # except Exception as e:
    #     reply = f"AI error: {e}"
    except Exception:
        reply = (
            "Gemini is busy right now. "
            "Please try again in a minute."
        )

    bot.reply_to(message, reply)



print("Bot is running...")
bot.infinity_polling()