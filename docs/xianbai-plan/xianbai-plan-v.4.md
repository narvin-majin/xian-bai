# Xian Bai Plan (Version 4)

Last Updated:
2026-07-06

Completion:
30 / 46 Steps
≈ 65%

Current Status:
Terminal-first development.

Telegram support has been modularized but cannot be fully tested because Telegram is temporarily unavailable in India.

Repository is under Git version control.

---

# Phase 1 — Core Assistant

✅ COMPLETE

- Telegram Bot
- Gemini Integration
- Basic Chat
- State System
- Track Commands
- History
- Daily Logs

---

# Phase 2 — Project Management

✅ COMPLETE

- projects.json
- /project_create
- /projects
- /project_switch
- /project_task_add
- /project_tasks
- /project_task_done

Project logic moved into project_manager.py

---

# Phase 2.5 — Core Architecture Refactor

✅ COMPLETE

Goal:
One assistant core.
Multiple user interfaces.

Completed:

✅ state_manager.py

✅ project_manager.py

✅ history_manager.py

✅ chat_manager.py

✅ assistant_core.py

✅ command_router.py

✅ terminal_ui.py

✅ telegram_ui.py

✅ app-0.3.py simplified

Result:

app.py only starts the application.

Business logic is separated from UI.

Terminal and Telegram share the same core.

---

# Phase 3 — Session Tracking

⬜ NEXT

Goal:

Measure productive work sessions.

Steps:

⬜ session_manager.py

⬜ sessions.json

⬜ /session_start

⬜ /session_stop

⬜ /project_stats

⬜ Daily session summaries

---
then 
file organization
tiny_assistant/
│
├── app.py              ← rename app-0.3.py after next stable commit
├── assistant_core.py
├── terminal_ui.py
├── telegram_ui.py
│
├── managers/
│   ├── state_manager.py
│   ├── project_manager.py
│   ├── history_manager.py
│   ├── chat_manager.py
│   └── session_manager.py   (next)
│
├── data/
│   ├── state.json
│   ├── projects.json
│   ├── chat_history.json
│   ├── history.json
│   └── sessions.json
│
└── docs/
    ├── xianbai-plan.md
    └── feature_idea.md



This is a good question because it affects the future architecture of Xian Bai.

Option 1 — Pass all parameters (Do this now) ✅
register_handlers(
    bot,
    client,
    state,
    projects,
    chat_history,
    save_chat_history
)
Pros
Very simple.
Easy to understand.
No new concepts.
Perfect for your current project size.
Cons
As the project grows, you'll keep adding parameters.

For example, after a few months you might have:

register_handlers(
    bot,
    client,
    state,
    projects,
    chat_history,
    save_chat_history,
    session_manager,
    reminder_manager,
    memory_manager,
    analytics_manager,
    ...
)

That's not ideal.

Option 2 — Keyword arguments
register_handlers(
    bot=bot,
    client=client,
    state=state,
    projects=projects,
    chat_history=chat_history,
    save_chat_history=save_chat_history
)

This is not a different architecture.

It is exactly the same as Option 1, except each argument has a name.

Pros
Easier to read.
Harder to accidentally swap arguments.
Cons
Still has six parameters.

I would use keyword arguments if the function has many parameters because it makes the call much clearer.

Option 3 — AppContext (Best, but later)

Instead of six separate objects:

state
projects
chat_history
client
save_chat_history
...

you create one object:

context = AppContext(...)

Then:

register_handlers(
    bot,
    context
)

Inside telegram_ui.py:

context.client
context.state
context.projects
context.chat_history

This scales much better.

When should we use AppContext?

Not now.

Here's why:

Right now you're still:

Moving code into modules.
Making Terminal and Telegram share the same logic.
Finishing the refactor.

If we introduce AppContext today, you'll be learning two things at once:

Finishing the refactor.
Understanding a new architectural pattern.

I'd rather keep the current refactor straightforward.

My recommendation

Use Option 2 for now because it's slightly clearer:

register_handlers(
    bot=bot,
    client=client,
    state=state,
    projects=projects,
    chat_history=chat_history,
    save_chat_history=save_chat_history,
)

Then, after Phase 3 (Session Tracking) is complete, we can do a dedicated architecture improvement where we introduce an AppContext class. By then you'll have more modules (sessions, reminders, memory), and the benefit will be obvious.

That way each change has a clear purpose:

Now: finish the refactor.
Later: improve the architecture without mixing it into feature development.



Even better for the future

Later, when you have 20–30 commands, you can define them once:

COMMANDS = [
    ("start", "Start Xian Bai"),
    ("status", "Show status"),
    ("track", "Track task"),
    ...
]

Then:

from telebot.types import BotCommand

def register_commands(bot):
    bot.set_my_commands(
        [BotCommand(cmd, desc) for cmd, desc in COMMANDS]
    )

Now every command exists in one place.

# Phase 4 — Reminder System

⬜

Goal:

Personal reminder assistant.

Steps:

⬜ reminders.json

⬜ reminder_manager.py

⬜ /reminder_add

⬜ /reminders

⬜ /reminder_done

⬜ Reminder notifications

---

# Phase 5 — Personal Memory

⬜

Goal:

Long-term assistant memory.

Files:

⬜ assistant_memory.json

⬜ user_profile.json

Manager:

⬜ memory_manager.py

Commands:

⬜ /remember

⬜ /forget

⬜ /profile

Capabilities:

⬜ Long-term facts

⬜ User preferences

⬜ Important notes

⬜ AI context injection

---

# Phase 6 — Analytics

⬜

Goal:

Personal productivity insights.

Commands:

⬜ /review_day

⬜ /review_week

⬜ /review_month

Features:

⬜ Focus trends

⬜ Burnout detection

⬜ Streak analysis

⬜ Project statistics

---

# Phase 7 — Deployment

⬜

Goal:

Run Xian Bai continuously.

Tasks:

⬜ Git backup workflow

⬜ Oracle Cloud deployment

⬜ Persistent storage

⬜ Automatic restart

⬜ Environment configuration

---

# Phase 8 — Multi-Platform

⬜

Goal:

One assistant.

Multiple frontends.

Platforms:

⬜ Telegram

⬜ Terminal

⬜ Discord

⬜ Web UI (future)

Architecture:

assistant_core.py

↓

Managers

↓

Platform UI

---

# Current Architecture

app.py

├── assistant_core.py

├── terminal_ui.py

├── telegram_ui.py

├── command_router.py

├── project_manager.py

├── state_manager.py

├── history_manager.py

└── chat_manager.py

---

# Next Task

Phase 3

Session Tracking

Create:

session_manager.py

Then implement:

- /session_start
- /session_stop
- sessions.json
- /project_stats