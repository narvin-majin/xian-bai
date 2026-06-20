import os
import json
from pathlib import Path
from datetime import datetime

from terminal_ui import start_terminal
from telegram_ui import register_handlers

from dotenv import load_dotenv
import telebot
from google import genai
from assistant_core import process_message

from state_manager import (
    load_state,
)
state = load_state()

from chat_manager import (
    load_chat_history,
    save_chat_history
)
chat_history = load_chat_history()

from project_manager import (
    load_projects,
)
projects = load_projects()


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
register_handlers(bot)

    
# ==================================================
# CHAT
# ==================================================

@bot.message_handler(func=lambda message: True)
def chat(message):

    reply = process_message(
        message.text.strip(),
        state,
        projects,
        chat_history,
        client
    )

    save_chat_history(chat_history)

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