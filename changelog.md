# CHANGELOG

All notable changes to Xian Bai are documented in this file.

---

# v0.4.0-dev (2026-08-01)

## Added

- Reminder System
- reminder_manager.py
- reminders.json
- /reminder_add
- /reminders
- /reminder_done
- Telegram reminder commands
- Telegram command menu entries for reminders

## Improved

- Shared business logic between Terminal and Telegram
- Cleaner Telegram UI architecture
- Command routing
- Reminder storage structure

## Fixed

- Reminder commands incorrectly handled by Gemini
- Reminder loading bug
- Reminder JSON structure
- Telegram command routing order

---

# v0.3.0 (2026-07-12)

## Added

- Session Tracking
- sessions.json
- /session_start
- /session_stop
- /session_status
- /project_stats

## Improved

- Core Architecture Refactor
- assistant_core.py
- command_router.py
- telegram_ui.py
- terminal_ui.py

## Fixed

- State saving bug
- focus_level KeyError
- Duplicate Telegram command logic
- Command router parsing issues

---

# v0.2.0

## Added

- Project Management System
- Project Switching
- Project Tasks
- Project Creation
- Project Task Completion

---

# v0.1.0

## Initial Release

### Added

- Gemini Integration
- Telegram Bot
- Terminal Mode
- State Management
- Chat History
- Task Tracking