# Xiao Bai Unified Development Plan

**Plan version:** 1.0  
**Status:** Working roadmap  
**Purpose:** The single plan to follow for building Xiao Bai, integrating the local AI prototype, and gradually growing toward the Alice Engine.

> **Source of truth:** Follow this document instead of managing `xianbai-plan.md` and `Xian_Bai_Local_Prototype_Plan.md` as two independent development roadmaps. Keep the original files as historical references until this unified plan has been reviewed and adopted.

---

## 1. The goal

Build Xiao Bai into a useful personal executive assistant first, then gradually develop it toward the future Alice Engine.

Xiao Bai should eventually help me:
- manage reminders, tasks, projects, deadlines, and priorities;
- remember useful personal and project context;
- decide what deserves attention today or right now;
- find and summarize current information that matters to me;
- connect relevant information about the world with my goals and projects;
- take actions through controlled tools, with clear permission boundaries.

The local language model is one component of Xiao Bai, not a separate assistant and not the whole system.

**Practical principle:** Build the smallest useful capability, test it in real use, and only then expand it.

---

## 2. How the two previous plans fit together

The previous plans had different roles:

- **The main Xiao Bai roadmap** described the user-facing capabilities and their development order: reminders, Personal Executive features, memory, news, proactivity, and the long-term Alice Engine direction.
- **The local AI prototype plan** described how to test a small local model, connect it to Python, and provide controlled tools such as notes, tasks, calculations, and web search.

This unified plan combines them into one sequence.

### One application, one source of truth

- The existing Xiao Bai repository is the main application.
- The local AI laboratory is temporary and isolated while the model and integration approach are tested.
- Do not build two independent assistants.
- Do not maintain two production versions of tasks, reminders, notes, or memory.
- When a prototype component is useful and tested, integrate or adapt it into the main application.
- The main application's data and managers remain authoritative after integration.
- A local model may be used where it works well; use external services where useful or necessary. Do not make “everything must run locally” a requirement.

---

## 3. Working constraints

Plan around the following assumptions:

- Approximately **one hour per development session**.
- Aim for one small-to-medium function or one meaningful implementation step per session.
- Beginner learning, debugging, and testing count as development work.
- A development day means a day I actually work, not a calendar day.
- Use phase-level working-session estimates, not fixed calendar deadlines.
- The planned CIE 3 break is **October 6–13, 2026**. Treat it as a no-development block.
- Re-estimate a phase if real testing shows that the scope or effort is different from expected.

Do not measure success by lines of code or hours alone. Measure it by what Xiao Bai can reliably do.

---

## 4. Architecture direction

The architecture should evolve gradually toward this conceptual shape:

```text
User
  |
Terminal / Telegram
  |
Xiao Bai Application
  |
Command Router / Application Context
  |
Assistant and AI Layer
  |-------------------------------|
  |                               |
Existing Managers             Local LLM
  |                               |
  |                         Structured request
  |                               |
  +---------- Tool Router --------+
                  |
          Validation / Permissions
                  |
       +----------+----------+
       |          |          |
     Tasks       Files       Web
       |          |          |
       +----------+----------+
                  |
            Persistent Data
          (SQLite / Markdown)
                  |
          Logs / Test Results
```

This is a target, not a demand to build every box now. Preserve the working architecture and introduce boundaries only when needed for the next capability.

### Responsibility boundaries

- **UI (Terminal / Telegram):** receive input and display results.
- **Command router:** dispatch supported commands without duplicating parsing logic.
- **Application context:** provide shared dependencies where it simplifies integration.
- **Managers/services:** own domain rules and persistent operations for reminders, tasks, projects, notes, and similar features.
- **AI layer:** interpret natural-language requests and generate responses or structured tool requests.
- **Tool router:** select and call registered tools.
- **Permission layer:** enforce what can happen and when approval is required.
- **Storage:** keep persistent data outside the model's conversation context.
- **Logging/tests:** make failures understandable and behavior repeatable.

Do not rewrite the whole architecture up front. Refactor only enough to support the next capability safely.

---

## 5. Development workflow

Use this loop for every phase:

1. Read the relevant code and current documentation.
2. Choose one small user-facing behavior.
3. Agree on the exact success condition before coding.
4. Implement the smallest change that can satisfy it.
5. Test normal cases and important edge cases.
6. Fix the actual failing layer instead of adding unrelated features.
7. Commit a working checkpoint.
8. Update this plan and the relevant project documentation.
9. Choose the next small step.

When something fails, classify it before changing code:

- **Model problem:** the model misunderstood or generated an invalid response.
- **Router problem:** the correct tool existed but was not selected or dispatched.
- **Tool/manager problem:** the operation itself is incorrect.
- **State/storage problem:** data was not saved or retrieved properly.
- **Permission problem:** an operation was allowed or blocked incorrectly.
- **UI problem:** input/output handling is confusing or duplicated.
- **Integration problem:** components work alone but fail together.

Avoid building large features before testing the smaller loop.

---

## 6. Phase 0 — Protect the current working version

**Estimated effort:** 1–2 working sessions

### Tasks
- Inspect the actual repository and current Git status.
- Confirm the project starts and current reminder behavior still works.
- Commit the stable state and push it if the configured remote is correct.
- Keep secrets, local model files, virtual environments, and private data out of Git.
- Record the Python version and current run/test instructions.
- Keep the local AI experiment in a separate directory/repository for now.

### Completion criteria
- There is a known-good Git checkpoint.
- The project can be started using documented instructions.
- The current reminder behavior has a short, repeatable test checklist.

**Do not assume that a documented feature works until it has been checked in the actual repository.**

---

## 7. Phase 1 — Finish and stabilize reminders

**Estimated effort:** 3–5 working sessions

The existing roadmap records a reminder foundation that includes a reminder manager, persistent storage, add/list/complete operations, terminal and Telegram support, command-menu integration, and several input edge cases. Verify the real code before treating each item as complete.

### Tasks
- Check the existing `/reminder_add`, `/reminders`, and `/reminder_done` flows.
- Test valid input, invalid input, empty lists, and completing an existing reminder.
- Fix remaining useful reminder issues without expanding into a full scheduling system.
- Verify behavior from both Terminal and Telegram where supported.
- Add or update tests and documentation.

### Completion criteria
- Reminder operations behave predictably.
- Invalid input is handled without crashing.
- The feature has been committed and can be used reliably.

---

## 8. Phase 2 — Minimal architecture cleanup

**Estimated effort:** 3–5 working sessions

### Tasks, in this order
1. Make `command_router.py` the central dispatcher if the current code supports that design.
2. Remove duplicated command parsing where practical.
3. Simplify `telegram_ui.py` so UI code is not responsible for assistant/domain logic.
4. Introduce or prepare an `AppContext` only if it reduces dependency duplication.
5. Clarify the boundaries between core, managers, services, UI, and data.
6. Preserve current working behavior with regression tests.

### Completion criteria
- Terminal and Telegram reach the same underlying capabilities where appropriate.
- New commands have one clear place for dispatch.
- Existing reminders still work.
- The refactor has not turned into a full rewrite.

**Do not build a generic framework for hypothetical future modules.**

---

## 9. Phase 3 — Local AI feasibility test

**Estimated effort:** 3–6 working sessions; laptop performance may change the estimate.

Do this in a separate `xianbai-lab/` directory or separate Git repository. The lab is temporary and should not duplicate the full application.

### Step 1: Prepare the environment
- Use a dedicated project directory.
- Create a Python virtual environment.
- Confirm Git is working.
- Keep model files out of Git.
- Record the Python version.

### Step 2: Run a local model
- Install and verify Ollama on the current Debian/Linux setup, if it is not already installed.
- Start with the planned **Qwen3 1.7B, Q4_K_M** variant if it is available and compatible with the installed runtime.
- Download one model only to start.
- Check actual memory use, speed, and stability on the laptop.

### Step 3: Test before building application code
Test:
- normal conversation;
- instruction following;
- short summarization;
- basic reasoning;
- structured output;
- whether responses are fast and reliable enough for intended tasks.

Record observations in `model_tests.md`. Do not assume a model's capability or speed from its parameter count alone.

### Completion criteria
- The model runs locally.
- A small test script or direct Ollama interaction can send a prompt and receive a response.
- There is a written record of limitations and performance.

### Decision gate
If the model is too slow or unreliable, test a smaller/alternative configuration or use an API for selected tasks. Do not force the whole assistant to depend on a poor fit.

---

## 10. Phase 4 — Connect the local model to Python

**Estimated effort:** 2–4 working sessions

Continue in the lab first.

### Tasks
- Write the smallest Python wrapper that accepts text, calls the model, and returns the response.
- Add multi-turn session history.
- Add a short system prompt defining Xiao Bai's role, communication behavior, privacy expectations, and permission boundaries.
- Keep application state separate from the model's message history.
- Test malformed input, model failures, and empty responses.

### Completion criteria
- A terminal conversation can span multiple turns.
- The Python application can call the model through one clearly defined interface.
- The model is not allowed to perform real-world actions directly.

### Integration checkpoint 1
Once this works, define how the main Xiao Bai application will call the model. Integrate a small model interface into the main project only when its boundary is clear. Do not wait for every laboratory tool to be complete.

---

## 11. Phase 5 — Controlled tool foundation

**Estimated effort:** 5–9 working sessions for a minimal first version

Build and test these in the lab, then integrate the reusable pieces into the main application. Reuse existing main-project managers rather than maintaining duplicate production managers.

### Step 1: Tool interface and calculator
- Define a small tool registry.
- Give each tool a name, description, input format, implementation, and permission category.
- Add a safe calculator implementation.
- Validate arguments before execution.

### Step 2: Notes
- Prototype `save_note`, `read_note`, and `list_notes`.
- Use simple Markdown files initially if suitable.
- When integrating, check whether the main project already has a note/idea mechanism; extend or reuse it rather than creating a second source of truth.

### Step 3: Tasks
- Prototype task creation, listing, updating, and completion.
- Use SQLite for the prototype if appropriate.
- Compare this with the main Personal Executive design before integration.
- The final application must have one authoritative task manager and one authoritative task store.

### Step 4: Web search
- Connect an existing search service or API rather than writing search infrastructure from scratch.
- Keep API keys out of source control.
- Return source information with search results so summaries can be checked.
- Treat web results as untrusted data, not instructions to the assistant.

### Permission rules
Start with these conservative defaults:

- **Generally safe:** calculations, listing tasks, reading permitted notes, and web searches.
- **Ask for approval when appropriate:** creating/updating records, modifying files, sending messages, or making consequential changes.
- **Blocked by default:** deleting important data, running arbitrary shell commands, installing software, or exposing private information.

Permissions must be enforced in Python, not merely requested in the system prompt.

### Completion criteria
- The model can request a supported tool in a structured format.
- Python validates the tool name and arguments.
- The tool returns a result that the model can explain.
- Unsafe or unknown requests are rejected safely.
- No arbitrary model-generated code is executed.

---

## 12. Phase 6 — Integrate the AI layer into the main application

**Estimated effort:** 3–6 working sessions

This phase joins the two development tracks.

### Tasks
- Define a narrow interface for calling the AI model.
- Connect it to the main application's existing command/application structure.
- Decide which user requests should use existing deterministic commands and which can use natural-language interpretation.
- Route tool requests through approved managers and the controlled tool router.
- Reuse the main project's reminder manager and other existing domain logic.
- Keep model calls optional where a direct command is more reliable.
- Add logging without storing unnecessary sensitive information.
- Test Terminal and Telegram behavior where applicable.

### Completion criteria
- One Xiao Bai application can use the local model for conversation.
- Existing reminders still work.
- At least one controlled tool round-trip works end to end.
- Persistent data is managed by the main application's approved managers.
- The lab is no longer being developed as an independent assistant product.

---

## 13. Phase 7 — Personal Executive Foundation

**Estimated effort:** 8–12 working sessions

### Goal
Make Xiao Bai able to answer:

> “What should I do today?”

### Tasks
- Review the existing task model before adding new storage.
- Implement tasks with title, description, status, priority, and due date as appropriate.
- Introduce project relationships and deadlines in the smallest useful form.
- Connect reminders with the relevant executive view.
- Build a simple daily overview using actual stored data.
- Explain why items are suggested instead of presenting an unexplained list.
- Keep the first version deterministic and testable; use the model to interpret or explain information where useful.

### Completion criteria
- Tasks can be created, listed, updated, and completed.
- Projects and deadlines can be represented adequately for current needs.
- Xiao Bai can provide a useful daily overview based on real data.
- No duplicate task/reminder databases have been introduced.

---

## 14. Phase 8 — Personal Memory

**Estimated effort:** 7–10 working sessions

### Goal
Store useful context so I do not have to repeatedly explain the same things.

### Start small
- Store selected facts and project context in an inspectable format.
- Separate persistent memory from temporary conversation history.
- Support adding, viewing, correcting, and deleting memory entries.
- Record where a memory came from when useful.
- Retrieve only relevant context for a request.
- Avoid saving every conversation automatically.

### Completion criteria
- Xiao Bai can save a user-approved fact or project detail.
- It can retrieve that detail in a later session.
- The stored memory can be inspected and corrected.
- Memory failures can be distinguished from model and routing failures.

---

## 15. Phase 9 — Context-aware Personal Executive Assistant

**Estimated effort:** 8–12 working sessions

### Goal
Make Xiao Bai able to answer:

> “What should I do right now?”

### Tasks
Combine, incrementally:
- current time;
- available time, when supplied or reliably known;
- tasks and deadlines;
- projects and priorities;
- reminders;
- relevant personal memory.

Start with clear rules and understandable recommendations. Use the model to interpret requests and explain suggestions, not as the sole authority over priorities or dates.

### Completion criteria
- Xiao Bai can suggest a practical next action based on actual task/context data.
- It can explain the main reason for its recommendation.
- It handles missing information honestly rather than inventing a schedule.

---

## 16. Phase 10 — News and Information Engine

**Estimated effort:** 10–15 working sessions for a useful first version

### Goal
Keep me informed about developments that matter to my interests, projects, learning, and work.

### Build the pipeline in stages
1. Retrieve articles from a small set of reliable sources or a search provider.
2. Extract titles, URLs, publication times, and available summaries.
3. Deduplicate repeated stories.
4. Categorize candidate items.
5. Estimate relevance to my known interests and projects.
6. Summarize using source-grounded information.
7. Store selected stories with source links and timestamps.
8. Provide a compact briefing before attempting complex automated notifications.

### Categories to consider
- major news;
- AI and model releases;
- useful products and tools;
- technical developments;
- learning and work opportunities;
- changes relevant to current Xiao Bai projects.

### Important safeguards
- Keep source URLs and timestamps.
- Distinguish publication time from the time an event occurred.
- Do not treat a model-generated summary as a verified fact.
- Avoid duplicate stories and notification spam.
- Keep the first version user-triggered or scheduled in a simple, controlled way; do not build a 24/7 autonomous agent first.

### Completion criteria
- Xiao Bai can retrieve, deduplicate, summarize, and show a small set of relevant stories with sources.
- The summaries preserve important qualifications and do not invent details.
- The user can inspect the original source.

---

## 17. Phase 11 — Connect news to memory and decisions

**Estimated effort:** 4–8 working sessions initially; revise after Phase 10

### Goal
Connect useful world information with personal context.

### Tasks
- Save selected, useful information rather than every article.
- Link relevant developments to existing projects or interests.
- Preserve source and date information.
- Retrieve relevant world information when answering project-related questions.
- Make it possible to correct or remove stored information.

### Completion criteria
- Xiao Bai can explain why a particular development may matter to a project or interest.
- The connection is based on stored context and sourced information, not invented personalization.

---

## 18. Phase 12 — Proactive assistant

**Estimated effort:** 7–10 working sessions for an initial version

### Goal
Provide timely suggestions without becoming noisy or intrusive.

### Begin with limited, user-controlled behavior
- Reminders and deadlines that are already stored.
- A simple daily or scheduled briefing.
- Important news that passes a relevance threshold.
- Clear controls to disable or adjust notifications.

Do not introduce autonomous computer control or unrestricted action loops.

### Completion criteria
- Notifications are useful, limited, and controllable.
- Xiao Bai explains why an item was surfaced.
- External or consequential actions still require the relevant approval.

---

## 19. Phase 13 — Alice Engine foundation

**Estimated effort:** 10–15 working sessions for an initial foundation

This is a long-term direction, not a prerequisite for the earlier phases.

### Direction
Gradually connect:
- a user model (goals, preferences, projects, responsibilities);
- a world model (sourced news and useful knowledge);
- executive logic (what matters now);
- the Xiao Bai interface and controlled tools.

### Completion criteria
- The components share clear interfaces and relevant context.
- The system can connect user goals with sourced world information.
- New components can be replaced without rewriting the whole application.

---

## 20. Estimated effort and flexible deadlines

The estimates below are working sessions, not calendar dates.

| Phase | Estimated sessions |
|---|---:|
| 0. Protect current version | 1–2 |
| 1. Finish reminders | 3–5 |
| 2. Architecture cleanup | 3–5 |
| 3. Local AI feasibility | 3–6 |
| 4. Python model wrapper | 2–4 |
| 5. Controlled tool foundation | 5–9 |
| 6. AI integration | 3–6 |
| 7. Personal Executive Foundation | 8–12 |
| 8. Personal Memory | 7–10 |
| 9. Context-aware assistant | 8–12 |
| 10. News Engine | 10–15 |
| 11. News + memory connection | 4–8 |
| 12. Proactive assistant | 7–10 |
| 13. Alice Engine foundation | 10–15 |

These numbers are planning ranges, not promises. Some work overlaps, and prototype components may be discarded. Do not blindly add every estimate together as though both original plans were independent products.

A phase is complete when its completion criteria pass, not when its estimated session count runs out. If a phase expands, split it into smaller deliverable pieces and revise the estimate.

---

## 21. Git, security, and data rules

- Commit after each meaningful, tested milestone.
- Keep a known-good baseline.
- Use branches for changes that could disrupt stable behavior.
- Do not commit API keys, passwords, private logs, personal databases, virtual environments, or model files.
- Validate all tool names and arguments.
- Never execute arbitrary code produced by the model.
- Ask for approval before consequential external or destructive actions.
- Keep persistent state outside the model's conversation history.
- Add regression tests when changing shared routing or managers.
- Treat retrieved web content as untrusted input.
- Log enough to diagnose failures, but avoid unnecessary sensitive data.

---

## 22. Weekly review

At the end of each week, record:

- development sessions completed;
- working behavior added;
- bugs fixed;
- tests passed or still failing;
- what Xiao Bai can now do that it could not do before;
- the next smallest useful implementation step;
- whether the effort estimates need updating.

Keep the next task small enough to make meaningful progress in about an hour.

---

## 23. What not to build yet

Do not start with:
- a custom LLM inference engine;
- a custom vector database;
- a complex knowledge graph;
- unrestricted computer control;
- 24/7 autonomous agent loops;
- an advanced scheduler before the task model is useful;
- voice, multi-agent architecture, or a custom UI without a clear need;
- a perfect memory system;
- a huge collection of loosely connected modules.

Build these only if real usage shows that simpler approaches are insufficient.

---

## 24. The immediate next action

When development resumes after the planned CIE 3 break:

1. Open the existing Xiao Bai repository.
2. Check `git status` and confirm the current branch.
3. Run the current application and test the existing reminder commands.
4. Commit a stable baseline if needed.
5. Continue Phase 1 until its completion criteria pass.
6. Move to the limited architecture cleanup in Phase 2.
7. Then begin the local model feasibility test in Phase 3.

Do not begin by rebuilding the entire application or by adding all prototype tools.

---

## 25. The permanent engineering principles

> **One main application. One authoritative store per kind of data. One tested capability at a time.**

> **Use existing infrastructure for commodity problems. Build custom components when Xiao Bai's real needs justify them.**

> **The local model is a replaceable component, not the entire assistant.**

> **The goal is not to write the most code. The goal is to make Xiao Bai reliably improve daily life, support decisions, and surface useful information.**
