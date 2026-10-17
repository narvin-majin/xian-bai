# Xiao Bai Plan

> **Purpose:** Build Xiao Bai into a practical personal executive assistant first, then grow it into the core of the future Alice Engine.

**Current version:** v0.4 (development)  
**Plan status:** Living roadmap  
**Deadline:** To be decided separately after this plan is reviewed

---

## 1. Vision

Xiao Bai is not meant to be just a chatbot, reminder app, or news reader.

The long-term goal is a system that understands:

- what I need to do
- what matters to me
- what I am working toward
- what I have already told it
- what is happening in the outside world
- what deserves my attention right now

The practical goal is:

> **When I am wasting time, forgetting something, or missing useful information, Xiao Bai should help me notice what matters and decide what to do next.**

Xiao Bai is the practical core of the future **Alice Engine**, which will eventually become the larger intelligence behind Alice.

---

# 2. Immediate Problems Xiao Bai Should Solve

### A. Forgetting and missing things

Xiao Bai should remember:

- tasks
- reminders
- deadlines
- appointments
- commitments
- unfinished work

### B. Too many projects and responsibilities

Xiao Bai should understand the relationship between:

- projects
- tasks
- college work
- freelance/work responsibilities
- personal goals
- priorities

### C. Wasting available time

A major real-world use case:

> I get home, start doomscrolling for an hour, and lose useful time.

Xiao Bai should eventually be able to look at my:

- calendar
- tasks
- projects
- reminders
- deadlines
- Personal Executive System priorities

and tell me something practical such as:

> "You have about one hour before bed. Your highest-priority task is the college record. Start that now."

The goal is **decision support**, not simply displaying a task list.

### D. Being disconnected from current information

I currently do not follow the news consistently.

Xiao Bai should eventually keep me informed about:

- major events
- AI developments
- new tools
- useful technologies
- learning opportunities
- opportunities relevant to work
- important changes that affect my interests or projects

The goal is not "give me the top 10 headlines."

The goal is:

> **"Tell me what happened that I personally should know."**

---

# 3. Product Principles

## 3.1 Usefulness before sophistication

A simple feature that I actually use is more valuable than a sophisticated feature that exists only in code.

Every major milestone should produce a capability I can use in real life.

## 3.2 Build from real workflows

Features should start from situations such as:

- waking up
- commuting
- working
- studying
- coming home
- procrastinating
- preparing for bed
- starting a project
- discovering important information

## 3.3 Keep the architecture simple

Do not build a large AI framework prematurely.

Start with simple:

- Python
- files / lightweight storage
- APIs where useful
- a small local LLM where useful
- clear modules
- testable managers/services

Architecture should grow when the actual requirements demand it.

## 3.4 Personalization is a core feature

Personalization should eventually cover:

- facts about me
- interests
- preferences
- communication style
- projects
- goals
- responsibilities
- priorities
- current situation
- long-term context

## 3.5 Xiao Bai should be proactive

The long-term assistant should not wait for me to ask everything.

It should eventually be able to say:

> "You have time available. Here is what would be useful to do."

or:

> "This happened today and it matters to your project."

Proactivity must remain useful and controlled, not become notification spam.

---

# 4. Current State

## Completed

### Phase 1
- Core project foundation
- Initial interaction flow

### Phase 2
- Command handling / basic assistant flow

### Phase 2.5
- Integration improvements

### Phase 3
- Current assistant functionality

### Phase 4 — Reminder Foundation
- Reminder manager
- Persistent reminder storage
- Add reminder
- List reminders
- Complete reminder
- Terminal support
- Telegram support
- Telegram command menu integration
- Invalid-number and empty-list edge cases

### Current reminder commands

- `/reminder_add`
- `/reminders`
- `/reminder_done`

---

# 5. Immediate Work

Before starting the larger Personal Executive system:

## 5.1 Stabilize the current version

- Commit the stable v0.4 state
- Push the current working version to GitHub
- Keep a known-good baseline

## 5.2 Architecture cleanup

Improve the current code so future modules do not require duplicated command logic.

Priority:

1. Make `command_router.py` the central command dispatcher
2. Reduce duplicate command parsing
3. Simplify `telegram_ui.py`
4. Introduce / prepare an `AppContext`
5. Separate responsibilities clearly between core, managers, services, UI, and data
6. Preserve current working behavior while refactoring

Do not turn the cleanup into an endless rewrite.

---

# 6. Roadmap

## Phase 5 — Personal Executive Foundation

### Goal

Give Xiao Bai a structured view of my responsibilities.

Xiao Bai should understand:

- tasks
- projects
- reminders
- deadlines
- calendar events
- priorities
- goals

### First useful capability

> **"What should I do today?"**

The answer should combine information from the systems above instead of simply printing separate lists.

### Success condition

I can ask Xiao Bai what deserves attention today and receive a useful, understandable answer.

---

# 7. Phase 6 — Personal Memory

### Goal

Make Xiao Bai persistent.

It should remember useful information about:

### Me
- preferences
- interests
- habits
- recurring patterns

### Work
- projects
- clients
- ongoing work
- important context

### College
- subjects
- assignments
- records
- deadlines
- recurring responsibilities

### Xiao Bai itself
- previous decisions
- useful context from earlier conversations
- important system state

### Success condition

I should not need to repeatedly explain the same context to Xiao Bai.

Memory should be useful, editable, and inspectable.

---

# 8. Phase 7 — Context and Personal Executive Assistant

### Goal

Combine Personal Executive data + Memory + current time/context.

This is the first major "Xiao Bai feels useful" milestone.

Xiao Bai should eventually answer:

> **"What should I do right now?"**

It should consider:

- current time
- available time
- calendar
- unfinished tasks
- deadlines
- project importance
- Personal Executive priorities
- reminders
- current goals
- relevant personal context

### Example

If I come home with one free hour and start doomscrolling, Xiao Bai should be able to suggest a concrete use of that hour.

The goal is not to control me.

The goal is to **reduce decision friction and make the useful action obvious.**

### Success condition

Xiao Bai can turn a messy set of tasks and responsibilities into a practical next action.

---

# 9. Phase 8 — News and Information Engine

## Goal

Build a system that keeps me informed without requiring me to actively follow the news.

### Core pipeline

```text
Internet
   ↓
Gather sources
   ↓
Extract candidate stories
   ↓
Deduplicate
   ↓
Classify / understand
   ↓
Check relevance to me
   ↓
Estimate importance
   ↓
Summarize
   ↓
Store useful information
   ↓
Notify / brief me
```

### News categories

The system should be able to detect:

- major news
- AI developments
- model releases
- important product updates
- useful tools
- technical developments
- learning opportunities
- work opportunities
- developments related to my projects
- things that could be useful long-term

### Personalization

A story should become more important when it connects to:

- my interests
- my current projects
- my goals
- my work
- technologies I am learning
- things Xiao Bai knows are relevant to me

### Example

Not:

> "New AI model released."

But:

> "A new AI model was released today. This may matter to Xiao Bai because it could run locally on your hardware and may improve one of the tasks you want Xiao Bai to handle."

### Commute use case

During a commute, Xiao Bai should eventually provide a compact personalized briefing.

---

# 10. Phase 9 — Continuous Information + Memory

The News Engine should eventually feed the Personal Memory system.

```text
World
  ↓
News / Web
  ↓
Information processing
  ↓
Relevant knowledge
  ↓
Memory / Knowledge
  ↓
User context
  ↓
Better decisions
```

This allows Xiao Bai to remember not just facts about me, but useful facts about the world.

---

# 11. Phase 10 — Proactive Xiao Bai

Xiao Bai should eventually become able to act proactively when there is a strong reason.

Examples:

### Time awareness

> "You have 90 minutes free."

### Deadline awareness

> "Your college work is due tomorrow."

### News awareness

> "Something important happened in AI today."

### Opportunity awareness

> "A new tool appeared that could help your current project."

### Learning awareness

> "This technology is becoming useful enough that learning it now may be worthwhile."

The system should prioritize relevance and avoid excessive notifications.

---

# 12. Phase 11 — Alice Engine

Long-term direction.

Xiao Bai becomes the practical assistant/interface around a larger intelligence system.

Conceptually:

```text
                 ALICE
                   │
             Alice Engine
                   │
        ┌──────────┴──────────┐
        │                     │
    USER MODEL            WORLD MODEL
        │                     │
    Memory                 News
    Goals                  Web
    Projects               Knowledge
    Preferences            Events
        │                     │
        └──────────┬──────────┘
                   │
             EXECUTIVE LOGIC
                   │
          "What matters now?"
                   │
                XIAO BAI
```

This is a long-term direction, not something to build immediately.

---

# 13. Technical Direction

The project should remain practical for the available hardware.

### Local AI

Use a small local model when it is good enough for:

- simple classification
- extraction
- lightweight reasoning
- formatting
- summarization
- routine assistant tasks

Use external services when the local model is not sufficient or when web access is required.

Do not make "everything must run locally" a goal by itself.

### Interfaces

Continue supporting:

- Terminal
- Telegram

Keep the assistant logic independent from either UI.

### Data

Prefer simple, inspectable storage at first.

Do not introduce heavy infrastructure before the project actually needs it.

---

# 14. Development Rules

## Rule 1 — Every milestone must produce a usable capability

Bad milestone:

> "Build memory architecture."

Good milestone:

> "Xiao Bai remembers my project and can use it when answering what I should work on."

## Rule 2 — Avoid endless refactoring

Refactor enough to support the next capability.

Then build.

## Rule 3 — Keep a working baseline

Every meaningful milestone should end with:

- tested behavior
- Git commit
- documentation update
- known-good version

## Rule 4 — Build the smallest useful version first

For example:

> Simple reminders → notifications later

> Simple memory → advanced retrieval later

> Simple news gathering → intelligent ranking later

## Rule 5 — Build for actual behavior

The system should solve real problems in my life, not just demonstrate technical features.

---

# 15. Main Success Milestones

The roadmap should be judged by what Xiao Bai can actually do.

### Milestone 1
> **"Xiao Bai can manage my reminders."**

Status: ✅ Mostly complete

### Milestone 2
> **"Xiao Bai can tell me what I should do today."**

Target: Personal Executive foundation

### Milestone 3
> **"Xiao Bai remembers my important context."**

Target: Personal Memory

### Milestone 4
> **"Xiao Bai can tell me what I should do with the next hour."**

Target: Context-aware Personal Executive Assistant

### Milestone 5
> **"Xiao Bai keeps me informed about things happening in the world that matter to me."**

Target: News Engine

### Milestone 6
> **"Xiao Bai connects world information with my goals, projects, and opportunities."**

Target: Personalized information intelligence

### Milestone 7
> **"Xiao Bai behaves like the early core of Alice."**

Target: Alice Engine

---

# 16. Current Priority

At the beginning of this plan, the priority is:

```text
1. Stabilize current Xiao Bai
2. Architecture cleanup
3. Personal Executive foundation
4. Personal Memory
5. Context-aware daily assistant
6. News / Information Engine
7. Proactive intelligence
8. Alice Engine
```

The order can change when real-world use reveals a better path.

The permanent rule is:

> **Build the next thing that makes Xiao Bai materially more useful to me.**

---


# 17. Time Budget and Phase Deadlines

## Working Assumption

For now, plan development around this capacity:

- **~1 hour per day**
- **~1 small-to-medium function or meaningful implementation step per day**
- I am still a beginner, so learning, debugging, testing, and ChatGPT-assisted development are part of the one-hour session.
- A "development day" means a day I actually work on Xiao Bai, not a calendar day.

This means the roadmap should use **phase-level effort budgets**, not exact calendar dates.

## CIE 3 Break

From **October 6–13, 2026**, I have CIE 3 exams.

Treat this period as a planned **no-Xiao-Bai-development block**.

The phase estimates below therefore describe **working days**, and I will decide the actual calendar dates myself.

## Phase Estimates

These are estimates, not rigid deadlines.

| Phase / Module | Estimated working days | Practical completion target |
|---|---:|---|
| Current Reminder completion | **3–5 days** | Finish the remaining useful reminder functionality and leave the module stable |
| Architecture Cleanup | **3–5 days** | Clean command routing/UI boundaries and prepare the codebase for new modules |
| Personal Executive Foundation | **8–12 days** | Tasks, projects, priorities, deadlines and a useful "What should I do today?" capability |
| Personal Memory | **7–10 days** | Store and retrieve useful personal/project context |
| Context-Aware Executive Assistant | **8–12 days** | Combine time, tasks, projects, reminders, priorities and memory to answer "What should I do right now?" |
| News / Information Engine | **10–15 days** | Gather, filter, deduplicate and summarize personalized news/information |
| Proactive Assistant | **7–10 days** | Useful proactive suggestions/notifications without becoming noisy |
| Alice Engine Foundation | **10–15 days** | Begin connecting user model, world information, memory and executive logic |

### Total Estimated Work

The full roadmap is roughly **56–84 working days** at the current pace.

This is intentionally a broad range.

It does **not** mean Xiao Bai must take 56–84 calendar days, because:

- exams and other life commitments create breaks
- some days will be debugging rather than adding functions
- some functions will be easier than expected
- some functions will require learning
- some phases may be changed or split after real usage

## How to Use the Estimate

At the beginning of a phase:

1. Start the phase timer from **Day 1**.
2. Work for about one hour per session.
3. Aim for one small/medium function or meaningful piece of functionality.
4. Test what was built before moving on.
5. Keep going until the phase's **completion criteria** are actually met.
6. Use the estimated day range as a **guardrail**, not a punishment.

Example:

> Personal Executive Foundation = 8–12 working days.

That means:

> "I expect this phase to take around 8–12 actual development sessions."

It does **not** mean:

> "It must be finished on a specific date."

## Flexible Deadline Rule

A phase is complete when its intended user-facing capability works, **not** when the estimated number of days runs out.

If a phase finishes early, move forward.

If a phase takes longer because I am learning or debugging, continue until the phase is genuinely useful, then review the estimate.

If the scope grows too large, split the phase rather than letting it become an endless project.

## Weekly Check-in

At the end of each week, record:

- working days completed
- functions/features completed
- bugs fixed
- what Xiao Bai can now do that it could not do before
- what the next working session should build

The main measure of progress is **usable capability**, not hours logged or lines of code.

---

# 18. Deadline

A concrete calendar deadline is not required for every phase. Each phase uses the working-day estimate above as its deadline budget.

When I decide to set a calendar target for a phase, break the roadmap into:

- weekly targets
- session-level tasks
- measurable completion criteria

The deadline should be realistic but firm enough to prevent indefinite postponement.

---

# 19. Definition of Success

Xiao Bai succeeds when it becomes something I naturally use because it reduces the mental effort required to manage my life and stay informed.

The ultimate test is not:

> "How much code did I write?"

It is:

> **"Did Xiao Bai make my day easier, more informed, and more intentional?"**
