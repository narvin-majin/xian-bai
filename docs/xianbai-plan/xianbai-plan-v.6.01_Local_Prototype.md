# Xian Bai — Local AI Prototype Plan

## Goal

Build a **small, working Xian Bai prototype** around an existing local LLM instead of building every subsystem from scratch.

The first prototype is **not the final Alice/Xian Bai architecture**. It is a laboratory version whose purpose is to prove that the pieces can work together and reveal which components actually need custom development.

### Prototype target

Xian Bai should be able to:

1. Chat normally.
2. Remember basic conversation/session state.
3. Receive a task such as “finish Java assignment tomorrow”.
4. Store and retrieve tasks.
5. Read/write simple notes or idea dumps.
6. Use at least one external tool, such as web search.
7. Explain what tool it wants to use before/while using it.
8. Keep basic logs.
9. Respect a simple permission rule: **never perform an external/destructive action without explicit approval**.
10. Run locally on the current laptop.

---

# 0. Architecture to build toward

```text
                 User
                  │
          Telegram / Terminal
                  │
                  ▼
          Xian Bai Python App
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   Local LLM            Tool Router
   Qwen3 1.7B               │
        │             ┌─────┼─────┐
        │             ▼     ▼     ▼
        │           Tasks  Files  Web
        │             │     │     │
        └─────────────┴─────┴─────┘
                  │
                  ▼
            SQLite / Files
                  │
                  ▼
             Logs / Memory
```

Do **not** implement every box immediately.

---

# Phase 1 — Get the local brain running

## Step 1 — Prepare the environment

On Debian:

- Make a dedicated project directory.
- Create a Python virtual environment.
- Make sure Git is working.
- Record the current Python version.
- Keep the existing Xian Bai repository separate until the local-model experiment works.

Suggested structure:

```text
xianbai-lab/
├── README.md
├── .gitignore
├── venv/
├── models/          # optional; don't commit model files
├── app/
├── tools/
├── data/
├── logs/
└── tests/
```

Do not put model files in GitHub.

## Step 2 — Install Ollama

Use Ollama as the first local model runtime because the goal is experimentation, not building an inference engine.

Verify that Ollama starts correctly.

## Step 3 — Download the small model

Start with:

```text
Qwen3-1.7B
Q4_K_M
```

Expected model storage is roughly 1.3 GB, with additional runtime/cache usage.

Do not download several models yet.

## Step 4 — Test the model directly

Before writing Xian Bai code, test:

- normal conversation
- basic reasoning
- summarization
- following instructions
- structured output
- simple tool-use instructions

Create a small `model_tests.md` containing observations.

### Success condition

You can reliably send a prompt to the local model and receive a response.

---

# Phase 2 — Put Python around the model

## Step 5 — Create the smallest possible Python wrapper

Create something conceptually like:

```text
Python
  ↓
Ollama
  ↓
Qwen3
  ↓
response
```

The Python program should:

1. accept user text,
2. send it to the local model,
3. print the response.

Nothing else.

## Step 6 — Add conversation history

Keep a simple session history.

Do NOT build sophisticated long-term memory yet.

Example:

```python
messages = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
]
```

### Success condition

You can have a multi-turn conversation with Xian Bai from the terminal.

---

# Phase 3 — Create the first Xian Bai identity

## Step 7 — Add a system prompt

Define:

- name: Xian Bai
- purpose
- communication style
- user authority
- privacy/local-first principles
- when it should ask for permission
- what it can/cannot claim to have done

Keep this short.

Do not try to encode the entire personality/philosophy yet.

## Step 8 — Add basic application state

Create a small state object containing things such as:

```text
current_session
user_name
current_project
active_task
last_action
```

Keep state separate from the LLM.

---

# Phase 4 — Give Xian Bai its first tools

This is the important transition.

The LLM should **not directly control the computer**.

Instead:

```text
User request
     ↓
LLM
     ↓
Tool decision
     ↓
Python tool
     ↓
Result
     ↓
LLM
     ↓
User
```

## Step 9 — Build a simple calculator tool

Even though it sounds trivial, this establishes the tool architecture.

Example:

```text
calculate("17 * 24")
```

The model should be able to request the tool, Python executes it, and the result goes back to the model.

## Step 10 — Build a notes tool

Functions:

```text
save_note()
read_note()
list_notes()
```

Store notes as Markdown files initially.

This gives Xian Bai its first persistent capability.

## Step 11 — Build a task tool

Use SQLite.

Minimum task fields:

```text
id
title
description
created_at
due_date
status
priority
```

Functions:

```text
create_task()
list_tasks()
complete_task()
update_task()
```

Don't build the intelligent scheduler yet.

## Step 12 — Add a basic web-search tool

Use an existing search service/API rather than writing search infrastructure yourself.

The model should be able to:

```text
search_web(query)
```

and then summarize the returned information.

Keep API keys outside Git.

---

# Phase 5 — Build the Tool Router

## Step 13 — Define a tool registry

Conceptually:

```text
TOOLS = {
    "calculator": ...,
    "notes": ...,
    "tasks": ...,
    "web_search": ...
}
```

Each tool should have:

- name
- description
- input schema
- Python function
- permission level

## Step 14 — Let the LLM choose tools

The LLM should produce structured tool requests.

Example:

```json
{
  "tool": "create_task",
  "arguments": {
    "title": "Finish Java I/O assignment",
    "due_date": "tomorrow"
  }
}
```

Python validates it.

Then Python executes it.

**Never blindly execute arbitrary Python/code generated by the model.**

## Step 15 — Add a permission layer

Start simple:

```text
SAFE
- read notes
- list tasks
- calculate
- search web

ASK FIRST
- create/update tasks
- send messages
- modify files

NEVER BY DEFAULT
- delete important files
- run arbitrary shell commands
- install software
- expose private information
```

This layer belongs to Xian Bai's Python code, not the LLM.

---

# Phase 6 — First useful prototype

## Step 16 — Connect everything

The first meaningful loop should be:

```text
User
 ↓
Xian Bai
 ↓
Understands request
 ↓
Decides whether a tool is needed
 ↓
Chooses tool
 ↓
Python validates request
 ↓
Tool executes
 ↓
Result returned to LLM
 ↓
Xian Bai explains result
```

Test requests such as:

```text
"Remember that I need to finish my Java assignment."

"What tasks do I have?"

"Search for the latest Qwen3 documentation."

"Save this idea: Xian Bai should have an idea parking system."

"What did I ask you to remember?"

"Calculate 17% of 850."
```

---

# Phase 7 — Observe before expanding

For every failed interaction, classify the problem.

```text
MODEL PROBLEM
The LLM misunderstood the request.

TOOL PROBLEM
The tool itself is inadequate.

ROUTER PROBLEM
The correct tool existed but wasn't selected.

STATE/MEMORY PROBLEM
The information wasn't stored/retrieved correctly.

PERMISSION PROBLEM
The system allowed or blocked the wrong thing.

UX PROBLEM
The interaction was technically correct but annoying.
```

This classification is extremely important.

**Do not immediately write a new module when something fails.**

First identify which layer actually failed.

---

# Phase 8 — Replace weak components only when justified

After the prototype works, evaluate each component.

For every component ask:

1. Does it already work well enough?
2. Is it too slow?
3. Is it unreliable?
4. Is it missing a feature Xian Bai genuinely needs?
5. Can it be wrapped instead of replaced?
6. Would replacing it teach us something valuable?
7. Is the maintenance cost worth it?

Only then decide:

```text
KEEP
WRAP
MODIFY
REPLACE
BUILD FROM SCRATCH
```

This is the core engineering philosophy of the project.

---

# Things NOT to build yet

Do not start with:

- custom LLM inference engine
- custom vector database
- complicated knowledge graph
- autonomous computer control
- 24/7 autonomous agent loops
- advanced scheduler
- voice assistant
- multi-agent architecture
- complex RAG system
- custom UI
- elaborate personality engine
- perfect memory system
- 100+ modules

Those may eventually become useful.

They are not required to prove that Xian Bai works.

---

# Initial milestone

The first milestone is intentionally small:

## Xian Bai v0.1

```text
✓ Local LLM
✓ Python wrapper
✓ Conversation
✓ Basic identity
✓ Session state
✓ Notes
✓ Tasks
✓ Web search
✓ Tool router
✓ Permission checks
✓ Logging
```

Everything beyond this is optional until the prototype has been used in real life.

---

# Suggested development workflow

Use this loop for the entire project:

```text
BUILD
  ↓
TEST WITH REAL REQUEST
  ↓
FIND FAILURE
  ↓
IDENTIFY WHICH LAYER FAILED
  ↓
FIX ONLY THAT LAYER
  ↓
TEST AGAIN
  ↓
KEEP / MODIFY / REPLACE
  ↓
NEXT CAPABILITY
```

Avoid:

```text
PLAN EVERYTHING
    ↓
BUILD EVERYTHING
    ↓
HOPE IT WORKS
```

---

# Rough time estimate

For someone at your current experience level, assuming roughly **1–2 focused hours/day**:

| Stage | Rough time |
|---|---:|
| Local model + Ollama | 1–2 hours |
| Python wrapper + conversation | 2–4 hours |
| Identity + state | 1–3 hours |
| Notes | 1–2 hours |
| Tasks + SQLite | 3–6 hours |
| Web search | 2–4 hours |
| Tool router | 4–8 hours |
| Permission layer | 2–4 hours |
| Integration + debugging | 4–8 hours |
| Real-world testing | 3–6 hours |
| **Total** | **~23–47 focused hours** |

### Calendar estimate

At ~1–2 hours/day:

**Fast:** ~2 weeks

**Realistic with college/distractions:** ~3–5 weeks

**Very relaxed:** ~6–8 weeks

The first usable version could appear much earlier — potentially **within the first few days**.

The goal is NOT to spend 5 weeks before seeing Xian Bai work.

You should have something like:

```text
Day 1:
"Hello Xian Bai."
      ↓
Local model replies.

Day 2–3:
Xian Bai remembers the current conversation.

Week 1:
Xian Bai can use notes/tasks.

Week 2:
Xian Bai can use tools.

Weeks 3–5:
Make the system reliable.
```

---

# Long-term direction

Once v0.1 works, the project can evolve toward:

```text
                 XIAN BAI
                    │
       ┌────────────┼────────────┐
       │            │            │
    Reasoning     Memory       Tools
       │            │            │
       │        ┌───┴───┐    ┌───┴────┐
       │        │       │    │        │
    Local LLM  Short  Long  Web     Files
              term   term  Tasks   Computer
                         │
                    Knowledge
                     /Projects
                         │
                         ▼
                  Personal Assistant
```

Later, individual components can be replaced with stronger systems.

For example:

```text
Qwen3 1.7B
     ↓
larger local model on future PC
```

without rebuilding the entire assistant.

---

# Definition of success

Xian Bai v0.1 is successful if:

> You can sit down at the laptop, talk to Xian Bai naturally, ask it to remember something, create/check a task, save an idea, search the web, and have it use those capabilities through controlled Python tools.

It does **not** need to be intelligent enough to run your entire life.

It only needs to prove that the architecture works.

---

# Principle to keep at the top of the project

> **Use existing infrastructure for commodity problems. Build custom code for the things that make Xian Bai uniquely useful.**

And:

> **Do not build a module until a real requirement proves that you need it.**
