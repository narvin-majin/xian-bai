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