That's exactly what I would do.

Don't build every feature now. Build a working assistant first and keep future ideas in a **feature_ideas.txt** file.

This is how real software projects grow.

---

# Xian Bai Master Plan v1.0

Save this as:

```text
PROJECT_ROADMAP.md
```

or

```text
XIAN_BAI_MASTER_PLAN.md
```

Whenever you start a new chat, you can paste this file and I'll immediately understand the project.

---

# Project Name

```text
Xian Bai
```

Personal AI Executive Assistant

---

# Main Goal

Build a Telegram-based AI assistant that:

* Chats naturally
* Tracks work
* Tracks projects
* Maintains memory
* Creates plans
* Gives reminders
* Prevents burnout
* Learns habits
* Helps achieve long-term goals

---

# Core Philosophy

```text
Assist
Not Spy

Guide
Not Control

Suggest
Not Force
```

The assistant should help make decisions.

The user always has final authority.

---

# Folder Structure

```text
tiny_assistant/

├── app.py

├── state.json

├── history.json

├── user_profile.json

├── assistant_memory.json

├── projects.json

├── reminders.json

├── feature_ideas.txt

├── logs/

│   ├── 2026-05-22.md
│   ├── 2026-05-23.md

└── backups/
```

---

# File Purpose

## app.py

Main program.

Responsibilities:

* Telegram bot
* Gemini API
* Commands
* Memory loading
* Memory saving

---

## state.json

Current active state.

Example:

```json
{
  "task": "Python",
  "status": "working",
  "start_time": "19:00"
}
```

Purpose:

Current session only.

---

## history.json

Structured event history.

Example:

```json
[
  {
    "event": "start_task",
    "task": "Python",
    "time": "2026-05-22T19:00"
  }
]
```

Purpose:

Permanent timeline.

---

## user_profile.json

Things user explicitly tells assistant.

Example:

```json
{
  "name": "Narvin",
  "preferred_name": "Yang Kai",

  "goals": [
    "Become freelancer",
    "Learn Python"
  ]
}
```

Purpose:

Long-term profile.

---

## assistant_memory.json

Things assistant learns automatically.

Example:

```json
{
  "best_focus_time": "19:00",
  "average_session_length": 55
}
```

Purpose:

Adaptive behavior.

---

## projects.json

Tracks projects.

Example:

```json
{
  "Tiny Assistant": {
    "status": "active",
    "priority": 10
  }
}
```

Purpose:

Project management.

---

## reminders.json

Future events.

Example:

```json
{
  "Python Study": {
    "date": "2026-05-23",
    "time": "19:00"
  }
}
```

Purpose:

Scheduling.

---

## feature_ideas.txt

Future features.

Example:

```text
Voice mode

Calendar sync

Exam planner

Burnout prediction

Freelance tracker

Japanese learning mode
```

Purpose:

Prevent feature overload.

---

# Development Phases

---

# Phase 1

## Foundation

Goal:

Working assistant.

### Step 1

Create Telegram bot.

Result:

Bot receives messages.

---

### Step 2

Connect Gemini.

Result:

Bot can chat.

---

### Step 3

Create state.json.

Result:

Stores active task.

---

### Step 4

Add:

```text
/track
```

Result:

Start task.

---

### Step 5

Add:

```text
/done
```

Result:

Finish task.

---

### Step 6

Save state automatically.

Result:

Survives restart.

---

### Step 7

Basic error handling.

Result:

No crashes when Gemini fails.

---

### Step 8

Daily log creation.

Result:

Creates markdown logs.

---

# Phase 2

## Work Tracking

Goal:

Track real work.

### Step 9

Create history.json.

Result:

Stores events.

---

### Step 10

Add:

```text
/stopwork
```

Result:

End session.

---

### Step 11

Add:

```text
/note
```

Example:

```text
/note fixed decimal bug
```

Result:

Stores observations.

---

### Step 12

Add timestamps.

Result:

Work duration tracking.

---

### Step 13

Calculate session length.

Result:

Hours worked.

---

### Step 14

Generate daily summary.

Example:

```text
Worked:
2h 15m

Notes:
Fixed decimal bug
Added README
```

---

# Phase 3

## Memory System

Goal:

Become personal.

### Step 15

Create user_profile.json.

---

### Step 16

Create assistant_memory.json.

---

### Step 17

Add:

```text
/remember
```

Example:

```text
/remember I prefer studying at night
```

---

### Step 18

Add:

```text
/profile
```

Displays profile.

---

### Step 19

Learn patterns.

Examples:

* best focus time
* average session

---

### Step 20

Track burnout indicators.

Examples:

* consecutive days worked
* session lengths

---

# Phase 4

## Project Management

Goal:

Manage multiple projects.

### Step 21

Create projects.json.

---

### Step 22

Add:

```text
/project add
```

---

### Step 23

Add:

```text
/project switch
```

---

### Step 24

Track project sessions.

---

### Step 25

Project statistics.

Example:

```text
Tiny Assistant:
12h

Python:
15h
```

---

# Phase 5

## Planning Engine

Goal:

Create schedules.

### Step 26

Morning planning.

Command:

```text
/plan
```

---

### Step 27

Task database.

Stores:

* priority
* duration
* difficulty

---

### Step 28

Fixed events.

Examples:

* exams
* classes

Cannot move.

---

### Step 29

Priority scoring.

---

### Step 30

Daily schedule generation.

---

### Step 31

Conflict detection.

---

### Step 32

Adaptive replanning.

---

# Phase 6

## Executive Assistant

Goal:

Think ahead.

### Step 33

Burnout detection.

---

### Step 34

Focus pattern learning.

---

### Step 35

Workload balancing.

---

### Step 36

Smart reminders.

---

### Step 37

Weekly reviews.

---

### Step 38

Project forecasting.

---

### Step 39

Goal alignment.

---

### Step 40

Decision advisor.

---

### Step 41

Opportunity suggestions.

---

# Build Order

Work only in this order:

```text
Phase 1
↓
Phase 2
↓
Phase 3
↓
Phase 4
↓
Phase 5
↓
Phase 6
```

Never skip ahead.

If Phase 1 isn't solid, Phase 5 will be a mess.

---

# Current Status

As of today:

```text
Completed:

✓ Telegram bot
✓ Gemini integration
✓ state.json
✓ /track
✓ /done
✓ Error handling

Next:

→ Daily logs
→ history.json
```

This roadmap is detailed enough that even if we start a completely new chat months from now, you can paste it and I can quickly understand where Xian Bai is, what's already built, and what the next step should be.
