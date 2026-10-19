# Xian Bai / Alice — Local AI Implementation Plan

**Document status:** Architecture and implementation plan; not yet an instruction to change the laptop  
**Version:** 0.1  
**Date:** 18 October 2026  
**Primary target:** Existing Xian Bai project on Debian 13  
**Planning style:** Build a useful system early, measure before scaling, preserve user control

---

## 0. Executive Summary

The goal is to evolve Xian Bai into a local-first personal assistant that can converse, receive voice commands, understand selected on-screen content when authorised, operate a restricted set of laptop tools, retain task and project memory, accept remote requests from the user's phone, and perform bounded background work overnight.

The recommended approach is **one assistant system with one supervisor and several capabilities**, not a collection of independent agents all running at once.

- **Xian Bai** is the project/product and its personal-assistant experience.
- **Alice** is the assistant identity and orchestration experience: conversation, planning, task handling and memory use.
- **The Python supervisor** is the enforcement and execution layer. It manages tasks, resource budgets, permissions, tool calls, model lifecycle and recovery.
- **LLMs are workers.** A model may interpret a request or complete a specialist task, but it does not decide its own permissions.
- **Markdown** stores readable, portable knowledge and project notes.
- **SQLite** stores durable operational state such as tasks, approvals, retries, events and checkpoints.
- **A local model runtime** serves language models when needed. For initial evaluation, Ollama is a candidate—not a permanent commitment.
- **Remote access** should pass through an authenticated Alice interface over a private network, not through a publicly exposed model API.

### Definition of a useful first version

The initial version is successful when the user can:

1. Chat with a local model through a simple interface.
2. Submit a task that persists across restarts.
3. Ask Alice to perform a narrowly scoped task such as finding a file in an approved folder or opening an approved application.
4. Inspect the task status and result remotely from a phone.
5. Queue a task for later execution without keeping every model loaded.
6. See an audit trail explaining what Alice attempted, which tools ran, and whether the result was verified.

Voice wake-word activation, vision-based screen control, a dashboard, multiple specialist agents and proactive research are later capabilities. They must not delay the first reliable task workflow.

### Core rule

**Alice stays available as a service; individual models are temporary resources; the supervisor remains in charge.**

---

## 1. User Goals, Operating Principles and Non-Goals

### 1.1 Goals

- Local-first operation and transparent data handling.
- Work alongside the existing Xian Bai codebase rather than create a competing project.
- Preserve user final authority: **Assist, not Spy; Guide, not Control; Suggest, not Force.**
- Support normal laptop use, remote/server use, and overnight queued work.
- Keep a conversational model available during interactive use when the measured memory cost is acceptable.
- Load specialist models only when the task needs them.
- Offer voice interaction through push-to-talk and later local wake-word detection.
- Use increasingly sophisticated screen awareness only when simpler, more deterministic methods are insufficient.
- Restrict desktop and filesystem control through explicit tools and allowlists.
- Record useful project state and decisions in human-readable formats.
- Keep engineering work small enough to fit around college and existing commitments.

### 1.2 Principles

1. **Reuse before rewriting.** Audit the existing Xian Bai repository and retain working modules.
2. **One feature at a time.** Finish and test one workflow before adding another.
3. **Deterministic tools before AI.** Use Python or existing operating-system interfaces for file listing, application launch, scheduling, validation and status checks.
4. **One active LLM inference by default.** Multiple loaded models and parallel inference are experimental until benchmarks show they fit.
5. **Model confidence never grants permission.** The policy layer is separate from the model.
6. **Persist before execution.** A task and its intended permissions are recorded before a worker starts.
7. **Checkpoint long tasks.** Background work must be recoverable after a crash or reboot.
8. **Fail closed on uncertainty.** When a tool target is ambiguous or permission cannot be verified, pause and ask.
9. **Observe minimally.** Do not continually capture the desktop or retain audio/screenshots without a clear reason and policy.
10. **Separate interactive responsiveness from background throughput.** Night tasks must not make the active desktop unusable.

### 1.3 Non-goals for the first milestone

- A fully autonomous “AI employee” with unrestricted computer access.
- A large multi-agent framework with every role running persistently.
- A live pixel-art office dashboard.
- Unrestricted command-line execution by a language model.
- Automatic installation of third-party agent skills or plugins.
- Autonomous financial transactions, purchases, publishing or sending messages.
- Building a custom LLM or training models from scratch.
- Replacing every existing Xian Bai feature before inspecting it.

---

## 2. Starting Hardware and Important Constraints

The most recent recorded inventory is:

- Dell Inspiron 15-3567.
- Intel Core i3-7020U, 2 cores / 4 threads.
- 12 GB RAM.
- Approximately 500 GB SSD.
- Debian 13 with GNOME on Wayland.
- No dedicated GPU recorded.

These details are a starting assumption, not a substitute for a current audit. RAM availability, swap setup, free disk space, thermals, current background services and the actual project version must be rechecked before selecting model files.

### 2.1 Consequences

- CPU inference is the likely baseline; do not assume GPU acceleration.
- A model that technically loads may still make the desktop painfully slow.
- Context length, KV cache, runtime overhead and concurrent requests add memory beyond the downloaded model weights.
- Screen automation under Wayland may be more constrained than a simple screenshot-and-click demo suggests. The exact tools must be tested in the user's desktop session.
- Running as a server is different from leaving the laptop suspended. A sleeping or powered-off laptop cannot process requests unless it is configured to wake up.
- Voice recognition, a resident conversational model, the browser and GNOME compete for CPU and RAM.

### 2.2 Initial resource targets (to be measured, not assumed)

| Resource | Initial planning target | Rule |
|---|---:|---|
| Debian, GNOME and daily applications | Measure baseline; allow roughly 3–4 GB for planning | Never treat all system RAM as model RAM |
| Python supervisor and database | Roughly 0.3–0.8 GB planning allowance | Confirm after implementation |
| Resident small chat model | Aim for a quantised model in a roughly 2–3 GB working-memory envelope | Accept only if interactive tests stay responsive |
| Voice pipeline | Start with push-to-talk; measure each component | Do not run all audio components constantly by default |
| Vision or larger reasoning worker | Treat as an additional temporary load | Load only if budget permits; unload resident chat if necessary |
| Safety headroom | Aim to retain at least 1.5–2 GB available during typical use | Tune based on swap and latency, not this number alone |

Memory categories can overlap and real use may differ. The benchmark report is the source of truth; this table is only a starting budget.

### 2.3 Recovery rules

When resource pressure appears:

1. Stop launching new heavy workers.
2. Pause or checkpoint low-priority jobs.
3. Unload idle models through the model manager.
4. Reduce context/concurrency settings before allowing more work.
5. Preserve the task queue and return to a safe state.
6. Notify the user if the task cannot continue within budget.

Do not rely on swap as the normal way to run several models. Swap can help prevent an abrupt failure, but sustained swapping can make the laptop unusably slow.

---

## 3. Target Architecture

```text
Local interface / remote phone / microphone
                    |
                    v
         Alice conversation layer
   (conversation, intent, clarification, plan)
                    |
                    v
      Python supervisor / policy engine
  (permissions, queue, model manager, budgets)
           /                \
          v                  v
   Approved tools        Model runtime
   - files               - general chat
   - applications        - coding/reasoning
   - browser             - vision, on demand
   - desktop             - small classification tasks
   - system status       - speech components separately
           \                /
                    v
          Verification and results
                    |
                    v
       SQLite state + Markdown memory
                    |
                    v
      Local UI / remote notification
```

### 3.1 Components and ownership

| Component | Responsibility | Must not do |
|---|---|---|
| Interface | Accept text/voice, show status, deliver results | Execute privileged actions directly |
| Conversation layer | Understand request, ask clarifying questions, propose structured task | Grant itself permissions or run shell commands directly |
| Supervisor | Own execution lifecycle, route approved tools, enforce budgets, handle retries | Trust model output without validation |
| Policy engine | Decide whether an action is allowed, requires approval or is denied | Infer permission from model confidence |
| Task queue | Persist state, priorities, retries, deadlines, checkpoints and results | Store secrets or entire private files unnecessarily |
| Model manager | Start, stop, warm, unload and measure model workers | Let separate modules independently load models |
| Tool layer | Expose narrowly defined operations | Provide general unrestricted computer access |
| Memory layer | Keep durable knowledge and project state readable | Automatically convert every chat into permanent memory |
| Remote gateway | Authenticate remote clients and limit available operations | Expose an unauthenticated model endpoint to the internet |
| Monitor/audit | Record events and report anomalies | Be the sole security enforcement mechanism |

### 3.2 Candidate technology stack

Choose the smallest stack that works. Do not install everything below at once.

| Need | Initial candidate | Decision rule |
|---|---|---|
| Main language | Python (existing Xian Bai language) | Keep code consistent with the existing project where possible |
| Task persistence | Python `sqlite3` / SQLite | One laptop and one supervisor do not initially need a separate database server |
| Language model runtime | Ollama as first evaluation candidate | Keep behind a thin adapter so it can be replaced later |
| Background lifecycle | systemd service/timer once prototype is stable | First prove the process works from the terminal |
| Remote path | Existing private Tailscale network, if still configured | Restrict which client can access which Alice service; never expose the model runtime publicly |
| Browser automation | Browser DOM/accessibility tooling where practical; Playwright is one candidate | Prefer labelled, semantic locators over raw screen coordinates |
| Linux screen semantics | Accessibility APIs where the application supports them | Test on the actual GNOME Wayland session |
| OCR | Add a local OCR engine only after needed | Test accuracy on the UI types actually used |
| Speech-to-text | Evaluate `whisper.cpp` or another offline option | Measure English accuracy, CPU load and latency on this laptop |
| Wake word | Evaluate `openWakeWord` after push-to-talk works | Confirm CPU use, false activations and microphone permissions |
| Text-to-speech | Select later based on voice quality, licence, offline support and CPU cost | Keep speech synthesis independent from the main LLM |
| Notes interface | Plain Markdown first; Obsidian optional | Files must remain useful without Obsidian installed or open |
| Dashboard | Defer; simple local status page or CLI first | Build a dashboard only when task volume justifies it |

These are candidates to test, not decisions that prohibit alternatives.

---

## 4. Operating Modes and Transition Rules

Alice uses one supervisor with modes that change the priority and loading policy. They are not separate Alice installations.

### 4.1 Interactive mode

**Purpose:** The user is working at the laptop and expects prompt responses.

- Keep the supervisor, queue and local interface active.
- Keep the smallest good conversational model loaded only if measured memory headroom permits.
- Keep wake-word detection off until explicitly enabled; push-to-talk is the first voice mode.
- Prioritise chat, safe interactive tools and explicit user commands.
- Pause or throttle night tasks while the user is active.
- Load vision/coding/reasoning workers only on demand.
- Do not run a full-screen capture loop continuously.

### 4.2 Remote/server mode

**Purpose:** The user is away from the laptop but wants to access Alice remotely and may leave background jobs running.

- Keep the supervisor, task database and authenticated remote gateway available.
- Run only those services that are required for remote requests and queued work.
- A resident chat model is optional. Keep it loaded only if remote-response latency is more important than memory headroom.
- Accept remote tasks, validate the client and enqueue them before execution.
- Allow task results and selected files to be delivered only through configured, explicit operations.
- Run background jobs within their CPU, RAM, network and time limits.
- Do not assume GUI automation is possible merely because the network service is reachable; the required desktop session must exist.
- Keep model APIs bound to localhost unless an independently reviewed network design requires otherwise.

### 4.3 Night-shift mode

**Purpose:** Run user-queued work plus a narrow set of approved proactive tasks.

- Unload the interactive chat model unless remote conversation is expected.
- Prefer one heavy model inference at a time.
- Run only tasks in configured categories and inside the quiet-hour budget.
- Start with a few proactive jobs: project-state summary, selected learning digest, task failure/health report, and backup status report.
- Avoid unrestricted “research anything useful” loops.
- Use deadlines, maximum runtime, maximum retries and maximum network requests.
- Checkpoint long tasks and publish a morning report.
- Do not make changes to security settings or install packages automatically.

### 4.4 Resource-recovery mode

**Trigger:** Low available RAM, high swap pressure, excessive CPU/temperature, worker crash loops or unavailable disk space.

- Reject new heavy model loads temporarily.
- Pause low-priority tasks at a checkpoint.
- Unload idle workers.
- Preserve the supervisor and database if safe.
- Retry a crashed worker only a bounded number of times.
- Emit a clear reason in the logs and status interface.
- Return to the prior mode only after a health check.

### 4.5 Mode transitions

1. Record the requested transition.
2. Stop starting low-priority work.
3. Let short tasks finish and ask long tasks to checkpoint.
4. Stop or unload components not needed in the destination mode.
5. Verify available memory, model status and network/service health.
6. Activate the destination policy.
7. Resume eligible tasks and record the outcome.

A user request can switch from night/server mode back to interactive priority. Do not delete queued work just because a mode changes.

### 4.6 Physical laptop state is separate from Alice's mode

Track at least these host states separately:

- Awake with interactive desktop.
- Awake with display off or locked.
- Suspended.
- Powered off/rebooting.

A background service can continue while the display is off, but GUI automation may no longer have a usable display context. Suspended or powered-off states prevent normal task execution. Lid-close, suspend and wake-on-LAN behaviour must be configured and tested separately, not assumed.

---

## 5. Model Roles, Loading Policy and Benchmark Plan

### 5.1 Model roles

Do not create a separate persistent model for every agent role. Define capabilities and route work according to test results.

| Role | Intended tasks | Default loading rule |
|---|---|---|
| Resident conversational model | Dialogue, simple intent understanding, task proposal, clarification | Loaded in interactive mode if budget allows |
| General fallback model | Fallback when specialist task fails or is unavailable | On demand; may be the same model as chat |
| Coding/reasoning worker | Harder code, debugging, complex planning | On demand; unload/replace chat model if needed |
| Vision-language worker | Interpret a screenshot or visual target when simpler methods fail | On demand; never run on every screen refresh by default |
| Small classifier/router | Simple classification, extraction or report triage | Keep resident only if it saves more latency than it costs in RAM/CPU |
| Speech-to-text | Convert recorded command to text | Separate component; push-to-talk first, then benchmark always-ready mode |
| Wake-word detector | Detect the chosen activation phrase | Optional low-load service after voice pipeline works |
| Text-to-speech | Speak an answer | On demand initially |
| Security/report reviewer | Summarise system events for human review | Scheduled or on demand; not trusted to enforce security |

### 5.2 Four-model benchmark set

The user proposed benchmarking four models of different sizes. Keep that experiment, but choose exact model names only after checking current availability, licence, supported quantisation, disk space and runtime compatibility.

Select four candidates that cover:

1. Small general model (approximately 1B–1.5B parameters).
2. Small/medium general model (approximately 2B–3B).
3. Larger general/reasoning candidate (approximately 4B, only if memory budget permits).
4. A coding-oriented candidate, ideally small enough to be a realistic CPU test.

These size bands are experimental buckets, not a guarantee about performance or RAM. A model family with several sizes makes comparisons more controlled; a different-family coding model can test task specialisation.

Do not download all four until disk space is checked and each candidate has been vetted. Avoid spending time on model names just because a video mentioned them. The hardware, model licence, task quality and benchmark results matter more than the brand.

### 5.3 Fair test procedure

For each model:

1. Record exact model tag, quantisation, runtime version, context size, prompt, output cap and date.
2. Record baseline available RAM and CPU load before starting.
3. Measure cold load time.
4. Run a consistent task set and record first-token latency and generation speed where available.
5. Record peak RAM, CPU use, swap changes, temperature trend and whether GNOME stayed responsive.
6. Run the same task three times where possible. Report median and note outliers.
7. Grade correctness against known answers or explicit acceptance checks—not only subjective “sounds good” ratings.
8. Repeat with a typical browser/VS Code workload open.
9. Do not compare one model at 2K context with another at a much larger context without documenting the difference.

### 5.4 Required task set

- Ordinary conversation with simple instructions.
- Return a strict JSON task proposal matching a schema.
- Decide whether to search files, open an app, use the browser or ask a clarifying question.
- Summarise a known text and preserve critical facts.
- Write or debug a small Python function with tests.
- Handle an ambiguous request by asking rather than guessing.
- Refuse a disallowed operation or correctly request approval.
- Recover from a tool error and explain what failed.

### 5.5 Metrics

| Metric | Why it matters |
|---|---|
| Cold load time | How long an on-demand worker delays the task |
| Time to first token / first useful response | Interactive feel |
| Generation speed | Whether longer answers are practical |
| Peak resident memory | Whether the model fits alongside desktop workloads |
| Available RAM and swap movement | Detects pressure and thrashing |
| CPU and temperature trend | Sustained tasks may throttle or disrupt daily work |
| Task correctness | A fast wrong answer is not useful |
| Tool-call schema validity | Supervisor needs predictable structured output |
| Desktop responsiveness | Protects the main laptop use case |
| Recovery behaviour | Shows whether a bad run breaks the workflow |

### 5.6 One-model versus two-model experiment

Run these only after each model's standalone benchmark passes:

- **A. One model loaded, sequential tasks.** Baseline.
- **B. Chat model stays loaded; worker is loaded only when required.** Observe eviction and memory behaviour.
- **C. Two models loaded but only one generates at a time.** Measure model-switching latency against memory cost.
- **D. Two simultaneous inferences.** Experimental only; record peak RAM, swap, throughput and desktop lag.

The starting production policy is **one active LLM inference at a time**, usually with one resident chat model in interactive mode. Change this only if measured benefits justify it. Loading two models in memory is a different question from generating with both at once.

### 5.7 Initial runtime policy

If Ollama is selected, put it behind `ModelRuntimeAdapter`. The adapter should support request, health check, preload if desired, unload and error reporting. Keep its HTTP API local by default. Configure conservative parallelism and a deliberate context size; measure before changing those defaults. The supervisor—not each agent role—owns the load/unload decisions.

---

## 6. Task Queue and Durable Execution

### 6.1 Why SQLite rather than a linked list

The queue must survive reboots, record task history, recover unfinished jobs, track approvals and support retries. SQLite is a better fit than an in-memory linked list for this single-machine use case. A priority queue can be implemented through database queries and indexes; there is no need to introduce a separate queue server initially.

### 6.2 Task record fields

Minimum `tasks` table fields:

- `id` — unique task ID.
- `created_at`, `updated_at`, `started_at`, `finished_at`.
- `source` — local UI, voice, remote client, schedule or internal workflow.
- `requested_by` — local user or authenticated client identity.
- `title` and `user_request` — concise human-readable request; avoid unnecessary sensitive payloads.
- `task_type` — file search, app launch, browser task, coding, report, audit, etc.
- `priority` — P0–P4 band.
- `status` — lifecycle state.
- `required_capabilities` — deterministic tool and model capabilities needed.
- `approval_state` and `approval_details` — approval requirement, requester and expiry.
- `deadline_at`, `not_before`, `max_runtime_seconds`.
- `retry_count`, `max_retries`, `last_error_code`.
- `checkpoint_ref` — location of recoverable progress.
- `result_ref` — stored output location.
- `policy_version` — rules used for execution.

Do not store raw credentials, private keys or large binary screenshots in the task row. Reference a controlled artifact file when a persistent artifact is genuinely needed.

### 6.3 Status lifecycle

```text
created
  -> queued
  -> planning
  -> awaiting_approval   (when needed)
  -> ready
  -> running
  -> verifying
  -> completed

Exceptional states:
  cancelled, deferred, failed, needs_attention
```

Every state change should have an event record with timestamp, task ID, source module, old/new state and a short reason. Approval must be tied to the exact proposed action and relevant parameters. A changed target or materially different action invalidates the old approval.

### 6.4 Priority policy

| Priority | Examples | Behaviour |
|---|---|---|
| P0 — safety | Stop unsafe tool activity, protect data | Interrupt if safe and necessary |
| P1 — interactive | Answer user, simple permitted app action | Highest normal priority |
| P2 — explicitly requested work | Find files, summarise notes, run tests | Normal queue |
| P3 — scheduled maintenance | Backup check, daily project summary | When capacity permits |
| P4 — proactive work | Optional learning digest, low-urgency research | First to defer when busy |

Use priority aging so a long-waiting task can eventually rise within its class. Include deadlines and mode eligibility. Do not make priority the security system: a P0 label must not be assigned by an untrusted model to bypass controls.

### 6.5 Queue scheduling rules

- One heavy model job at a time initially.
- Small deterministic tools may run while the LLM is idle, but do not oversubscribe the CPU.
- Interactive tasks can pause or pre-empt low-priority work at a safe checkpoint.
- Jobs waiting for approval consume no model resources.
- Every task has bounded runtime and retry count.
- Tool calls must be idempotent where possible. For non-idempotent actions, the supervisor must check whether the action already happened before retrying.
- Repeated failures move the task to `needs_attention` or `failed`; do not loop forever.
- Persist a checkpoint before lengthy work or risky file modifications.
- At restart, identify orphaned `running` tasks and resume only when a safe checkpoint exists; otherwise mark for review.

### 6.6 Initial task types

Start with only a few types:

1. `file_search` — search named/approved directories and return paths plus limited snippets.
2. `open_application` — launch an allowlisted application using a fixed application ID or desktop entry.
3. `summarise_file` — read a user-selected or approved text file and produce a summary.
4. `run_test_command` — run a configured test command for a known project; no arbitrary model-generated shell string.
5. `scheduled_report` — produce a summary from approved task/project data.

Browser automation, visual clicking, arbitrary code editing and general desktop control should be added later as separate task types with their own tests.

---

## 7. Tool Registry and Permission Model

### 7.1 Structured tool calls

The LLM should return a constrained proposal, for example:

```json
{
  "intent": "file_search",
  "target_scope": "approved_project_files",
  "query": "Java Unit 4 notes",
  "needs_screen": false,
  "requires_approval": false
}
```

This is only a proposal. The supervisor validates it against a schema, normalises parameters, checks the allowlist and makes the actual permission decision. Model-supplied `requires_approval` is informational and never authoritative.

### 7.2 Initial permission categories

| Action | Default | Notes |
|---|---|---|
| Read configured application/window title | Allow | Avoid collecting unrelated windows |
| Search approved directories | Allow | Enforce path scope and size limits |
| Read a user-selected text file | Allow | Record file path; avoid copying sensitive full content into logs |
| Open an allowlisted application | Allow | Use fixed app IDs/desktop entries |
| Open a URL in an approved browser | Allow for permitted schemes/domains | Reject dangerous schemes and suspicious parameters |
| Use browser DOM to read a page | Allow only within defined browser scope | Webpage text is untrusted data |
| Click a verified, ordinary UI control | Allow only for a tested workflow | Target must be identified and checked immediately before action |
| Type into an arbitrary text field | Ask or restrict by app/context | Could send messages or overwrite content |
| Read credentials, tokens, private keys or authentication codes | Deny by default | Do not make these files part of the general search scope |
| Delete, overwrite or move important files | Require explicit approval | Show exact path and proposed change |
| Send a message, publish, submit a form or purchase | Require explicit approval | Show destination/content before confirmation |
| Install software or change system/security settings | Require explicit approval | Prefer manual user execution for early versions |
| Run arbitrary shell command supplied by model | Deny | Expose fixed command tools for defined jobs instead |
| Run as root / use `sudo` | Deny to the agent | User performs privileged actions manually during early development |

### 7.3 Filesystem containment

- Configure an explicit list of readable roots and separate writable roots.
- Resolve and validate paths before use; handle `..`, symlinks and special files deliberately.
- Start with read-only project folders. Write only to an Alice-owned workspace or explicit output directory.
- Enforce file-size, file-type and traversal limits.
- Exclude `.ssh`, browser profiles, credential stores, password managers, `.env` files and other secret-bearing paths unless a specific reviewed workflow requires them.
- Keep Alice's runtime unprivileged.
- Make file modification a separate tool from file reading, with its own approval policy and diff/checkpoint mechanism.

### 7.4 Prompt-injection boundary

Screenshots, web pages, documents, code comments and tool output may contain instructions such as “ignore your rules.” Treat all such content as untrusted data. It may inform the task result but cannot alter system policy or grant additional permissions.

The supervisor should:

1. Maintain policy outside the model's editable context.
2. Pass only the minimum required information to each worker.
3. Treat tool results as data, not as trusted control messages.
4. Validate every proposed tool call and its arguments.
5. Ask for approval when the proposed action exceeds the allowlist.
6. Verify the result independently where possible.

### 7.5 Approval workflow

An approval prompt must state:

- What action will happen.
- The exact target (path, URL, application, recipient or field).
- What data will be changed or sent.
- Whether the action can be undone.
- Why the action is being proposed.

Approval should expire after a configured interval and be invalidated if the action changes. “Allow safe actions automatically” means allowlisted operations under stated conditions—not blanket permission for any action the model describes as safe.

---

## 8. Screen Awareness and Desktop Control

The screen pipeline should be tiered. Capturing the whole screen and asking a vision model to reason about every action should be the fallback, not the default.

### 8.1 Tier 1 — deterministic tools

Prefer existing system and application interfaces:

- File APIs for file searches.
- Known desktop entry/app IDs for application launching.
- Browser DOM/accessibility semantics for supported web workflows.
- Active-window metadata where safely available.
- Application-specific interfaces for known tasks.

These are typically easier to verify than visual clicking.

### 8.2 Tier 2 — accessibility information and OCR

If the target is visible in an application, try exposed accessibility labels/roles or OCR before loading a VLM. This can handle many text-based buttons, titles and labels without requiring visual reasoning. Test support in the actual application and GNOME Wayland session.

### 8.3 Tier 3 — vision-language model

Use only when the previous tiers are insufficient:

1. Request an explicitly authorised screenshot of a selected window or limited region.
2. Avoid collecting unrelated windows, notifications, passwords or private chats.
3. Ask the vision model to return a small structured result: candidate label, visual description, approximate location and uncertainty.
4. Validate that the target is inside the approved window and matches the task.
5. Perform one action, not a long chain of blind clicks.
6. Capture a new state and verify the result before continuing.
7. Discard the screenshot unless the user has asked to keep it or a bounded debugging policy allows retention.

### 8.4 Browser example: “Play that AI video on the first row”

1. Speech-to-text or the text UI provides the request.
2. Alice identifies that a visible YouTube result must be selected.
3. The supervisor checks that the browser is an approved target.
4. Prefer browser DOM/accessibility data to identify the first-row video and its title.
5. If the target is ambiguous, ask the user which video they mean.
6. Use visual interpretation only if semantic browser information is insufficient.
7. Validate the selected target immediately before clicking.
8. Click through an approved browser-control method.
9. Confirm playback began; if not, stop and report the actual failure.

Do not make claims like “video is playing” merely because the click tool returned without an error.

### 8.5 Wayland note

Do not assume traditional global mouse/keyboard injection or unattended screenshots will work under GNOME Wayland. Test each required capability on the actual laptop. If a GUI technique requires relaxing desktop security or switching session type, document the trade-off and get the user's decision before changing it.

### 8.6 GUI-control acceptance tests

- Correctly identifies the selected browser/window.
- Never clicks when the candidate target is ambiguous.
- Does not interact with a different window than the approved one.
- Detects layout changes or missing targets and stops.
- Confirms action outcome.
- Requires approval for sending, submitting, deleting, purchasing or system changes.
- Works with screen capture disabled for tasks that do not need it.
- Does not store screenshots by default.

---

## 9. Voice Architecture

Voice is a separate interface pipeline. The main LLM does not need to listen continuously.

```text
Microphone
   |
   +--> Push-to-talk (first milestone)
   |
   +--> Local wake-word detector (later, explicit toggle)
                 |
                 v
           Speech-to-text
                 |
                 v
         Alice conversation
                 |
                 v
         Supervisor + tools
                 |
                 v
         Response text
                 |
                 v
          Text-to-speech
```

### 9.1 Stage 1 — push-to-talk

- Bind a clear keyboard shortcut/button to begin and end recording.
- Show microphone state visibly.
- Convert the recording to text offline if an appropriate local model passes tests.
- Display the transcript before execution for debugging and optionally require confirmation for a first command.
- Route the resulting text through the exact same conversation and supervisor path as typed text.
- Keep audio only for the duration needed for transcription; do not archive raw audio by default.

### 9.2 Stage 2 — wake-word detection

- Evaluate a local wake-word detector after push-to-talk is reliable.
- Keep the detector lightweight and distinct from speech-to-text and the LLM.
- Require an explicit enable/disable control and a clear indicator when activation is armed.
- Measure false activations, missed activations, CPU use and response latency.
- After activation, record only the command window needed for transcription.
- Do not allow background wake-word activation to bypass task permissions.

### 9.3 Stage 3 — speech output

- Add a local text-to-speech engine only after the task loop is stable.
- Speak short status messages by default; allow long results to remain text unless requested.
- Ensure speech generation can be interrupted or muted.
- Avoid overlapping speech when background tasks complete.

### 9.4 Remote voice

The phone can send an authenticated audio clip to Alice, which uses the same STT/conversation/policy flow. Test it separately from local microphone input. Do not stream raw audio continuously by default. Remote access must not create a second tool pathway with broader permissions.

### 9.5 Voice acceptance tests

- Correct transcript for a small fixed set of everyday English commands.
- Handles common transcription errors by asking for confirmation when task or target is ambiguous.
- Push-to-talk always stops recording when released/cancelled.
- Voice can be globally disabled.
- Wake-word false-positive rate is measured before enabling it for regular use.
- CPU load does not make normal desktop usage unacceptable.
- Spoken output can be muted without disabling text answers.

---

## 10. Memory and Knowledge Management

Use SQLite for operational truth and Markdown for human-readable knowledge. Do not force all memory into one format.

### 10.1 SQLite operational state

Store:

- Tasks, lifecycle state, priority, approvals and checkpoints.
- Tool execution events and error codes.
- Model benchmark results and measured resource use.
- Schedule definitions and last-run status.
- Minimal preferences that must be queried programmatically, if any.

### 10.2 Markdown durable memory

Suggested starting layout:

```text
alice_data/
├── README.md
├── profile/
│   └── preferences.md
├── projects/
│   └── xian-bai/
│       ├── overview.md
│       ├── architecture-decisions.md
│       ├── current-state.md
│       ├── backlog.md
│       └── changelog.md
├── daily/
│   └── YYYY-MM-DD.md
├── learning/
│   └── YYYY-MM-DD-topic.md
├── reports/
├── procedures/
└── logs/
```

Keep this separate from the code repository's source files unless the user explicitly chooses to version some notes. Sensitive personal data, logs, tokens, screenshots and machine-specific paths should not be committed by default.

### 10.3 Memory write policy

After a significant session or task, Alice may propose a concise memory update containing:

- Decisions made and why.
- What changed in the project.
- Verified outcomes and test results.
- Open issues and next step.
- User corrections that change future behaviour.

Do not automatically store every conversation, speculation, credential or transient error. Durable memory should be selective and periodically reviewed.

### 10.4 Memory consolidation

A scheduled summarisation job may propose daily or weekly summaries. The output must retain links/references to the original tasks or files where practical. The summariser may propose preference changes but must not silently rewrite the authoritative profile without approval.

### 10.5 Obsidian

Obsidian can be used as an optional viewer/editor for the same Markdown files. It is not the database, supervisor or memory engine. The system remains usable if Obsidian is closed or uninstalled. Decide synchronisation and remote access separately; never put secrets in a public vault or repository.

---

## 11. Server Mode, Remote Access and Lifecycle

### 11.1 Network design

- Bind development and model APIs to `127.0.0.1` by default.
- Provide a small authenticated Alice gateway for phone access.
- Reuse the existing private network/VPN if it is still configured and working.
- Use least-privilege access rules so only designated devices/users can reach the Alice gateway.
- Do not expose raw model-runtime ports directly to the public internet.
- Authenticate remote requests at the application layer as well as relying on network reachability.
- Validate every remote task using the same task schema and policy engine as local requests.
- Limit request size, rate and concurrent jobs.
- Log source identity and action results without keeping unnecessary sensitive content.

### 11.2 Service separation

Eventually separate two lifecycles:

1. **Alice core service:** task database, queue, scheduler, model manager and remote gateway. It may be usable without an active graphical session.
2. **Desktop bridge:** optional user-session component for authorised screenshot/accessibility/browser/keyboard interaction. It should only be available when the appropriate session exists and should not run with more privilege than needed.

This separation prevents a remote request from assuming that a logged-in desktop and a working display bridge are always available.

### 11.3 systemd deployment

Do not turn the prototype into an auto-starting service until it runs reliably from the terminal. When ready:

- Use a service unit with an unprivileged account/user context.
- Add restart throttling so a crash loop does not continuously consume CPU.
- Use separate timer units for predictable scheduled jobs where appropriate.
- Configure logs/retention and controlled shutdown.
- Make startup idempotent; a second start must not create duplicate scheduler loops.
- Verify reboot recovery and manual stop/start behaviour.
- Treat user-session GUI tools separately from core background services.

### 11.4 Server mode host behaviour

Document the expected behaviour in each state:

| Host state | Core service | Remote requests | GUI actions |
|---|---|---|---|
| Awake, desktop active | Expected to run | Available if network/auth works | Available only through enabled bridge |
| Awake, screen locked/off | Can run | Available if system/network remain up | Must be tested; do not assume |
| Suspended | Usually paused/unavailable | Normally unavailable | Unavailable |
| Powered off/rebooting | Unavailable until startup completes | Unavailable | Unavailable |

Configure lid-close and sleep policy deliberately. Keep power settings conservative; do not disable suspension until the user has agreed to the battery, heat and security implications.

---

## 12. Overnight Tasks and Proactive Work

### 12.1 Allowed early proactive jobs

Limit the first version to a small set:

1. **Xian Bai project review:** summarise open tasks, recent changes and the next small action.
2. **Learning digest:** summarise user-selected materials or notes and prepare a short retrieval/review prompt.
3. **Health report:** list failed tasks, resource usage, model loading results and relevant service errors.
4. **Backup check:** report whether the configured backup ran and whether expected files exist; do not delete or overwrite backups automatically.

Do not allow unbounded web exploration, bulk downloading or automatic project rewrites at night.

### 12.2 Per-job limits

Every unattended job must have:

- Approved task category.
- Explicit input scope.
- Maximum runtime.
- Maximum retries.
- Maximum model/context budget where possible.
- Maximum network request/download limit if network access is allowed.
- Output directory and retention rule.
- Whether the job can write files.
- Whether any approval is required before an external side effect.
- A checkpoint/recovery policy.

### 12.3 Night-shift control loop

1. At the start of the night window, inspect host state, queue and resource health.
2. Pick the highest eligible task within the available budget.
3. Load the smallest adequate model/capability.
4. Run a bounded step and validate its output.
5. Save output/checkpoint and release unused resources.
6. Re-check the system before starting another heavy task.
7. At the end of the window or on a recovery trigger, stop starting work, checkpoint and produce a report.

### 12.4 Example schedule (illustrative, not yet enabled)

- At the configured night start: run queued requested tasks first.
- If capacity remains: run one project-state report.
- On selected nights: run the learning digest.
- Once or twice a day: deterministic service/log checks.
- Weekly: prepare a read-only audit summary for human review.

Exact times should be chosen after reviewing the user's schedule and laptop power use. Scheduled tasks must respect the system timezone and clock changes.

---

## 13. Security Monitoring and Recovery

### 13.1 Deterministic checks always come first

Use normal scripts/system tools for:

- Process/service health and crash loops.
- Available RAM, swap and disk space.
- Repeated task failures.
- Unexpected changes to Alice configuration or allowlists.
- Invalid authentication or repeated rejected remote requests.
- Backup status.
- Model manager actions and tool calls outside policy.

A small local model may group or summarise events, but it is advisory. It is not a security boundary and may miss attacks or produce false alarms.

### 13.2 Read-only audit roles

A security reviewer should initially receive only a sanitised report, not unrestricted filesystem access. It can flag suspicious activity and recommend investigation. It cannot grant itself tools, disable policy checks or approve its own changes.

### 13.3 Audit trail

Log at least:

- Timestamp, task ID and source interface.
- Policy decision and policy version.
- Tool name and parameters after sensitive values have been redacted.
- Model ID and runtime status when relevant.
- Start/end time, status and error code.
- Approval record ID for actions requiring confirmation.
- Verification result.

Do not log API tokens, passwords, private key data, raw microphone audio or full screenshots by default. Define log retention and provide a way to inspect/delete user-facing artifacts.

### 13.4 Backups and restore

- Back up SQLite safely using the SQLite backup mechanism or a consistent stopped/locked backup procedure.
- Back up Markdown memory and configuration separately.
- Exclude model downloads from frequent backups unless there is a specific reason; models can usually be downloaded again, while task and memory state are more valuable.
- Keep a restore procedure and test it periodically.
- Never assume a Git repository is a backup for secrets or local operational data.

### 13.5 Third-party tools/skills

Follow the principle taken from the source material: do not blindly trust a community skill because it appears useful. Read its source, inspect external network access and shell calls, pin versions where appropriate, and test it with restricted permissions. For early milestones, prefer a small tool written and understood locally over importing a large agent bundle.

---

## 14. Dashboard and Communication Interface

### 14.1 Start without a dashboard

The first status surface can be a CLI command or simple local page showing:

- Current mode.
- Current task and queued count.
- Model loaded/unloaded status.
- Available RAM and resource recovery state.
- Tasks awaiting approval.
- Recent successes/failures.
- Last scheduled job and next scheduled job.

This is enough to operate and debug the first version.

### 14.2 Remote notifications

Use the existing working interface if available. Telegram already belongs to the earlier Xian Bai project history, so first inspect that implementation before creating a Discord bot. Discord may be useful later if multiple workflows make channel-based routing valuable, but it is not required for the supervisor or memory architecture.

Remote messages should have a concise structure:

- Task title and ID.
- Status.
- One-line result or blocker.
- Link/path to a controlled output when appropriate.
- Approval request with exact action details if needed.

### 14.3 Mission Control dashboard later

Only build a fuller dashboard when actual task volume warrants it. Proposed tabs can be:

- Tasks.
- Projects.
- Memory/docs.
- Schedules.
- Models/resources.
- Approvals.
- Security/health.

A pixel-art agent office is a visualisation of task state, not an operational requirement. It should render real statuses from the system and never become the source of truth.

---

## 15. Phased Roadmap and Definition of Done

Effort estimates are for focused work, not guaranteed calendar deadlines. Existing code, network configuration and desktop constraints can change the timeline. Work around college by finishing a small testable vertical slice each time.

### Phase 0 — Repository and machine audit

**Estimated effort:** 30–60 minutes for initial inspection; longer if repository state is unclear.

Tasks:

- Find the exact Xian Bai project location and current branch.
- Check `git status`, recent commits and existing backup before modifying files.
- Map current bot, router, state/history, configuration and command modules.
- Record Python environment/dependencies without changing them.
- Check current RAM/swap/CPU/load/disk and current model runtime state if installed.
- Confirm whether Telegram and Tailscale still work.
- Identify secrets and ensure they are not in the repository.
- Make a small “reuse / repair / defer” map for existing modules.

**Done when:** a written inventory exists; the project is backed up; no code has been rewritten; the next implementation step is obvious.

### Phase 1 — Baseline and four-model benchmark

**Estimated effort:** 1–3 focused sessions, depending on download speed and testing issues.

Tasks:

- Establish baseline resource measurements.
- Choose four candidate models only after checking licence, quantisation, compatibility and disk capacity.
- Run the standard prompt/task set.
- Measure cold load, warm latency, memory, CPU, swap and task quality.
- Repeat tests with the typical browser/development workload open.
- Select a resident model and an on-demand fallback, or record that no model is yet suitable for resident use.

**Done when:** a table records exact model tags and measured results; the resident/fallback decision is evidence-based.

### Phase 2 — Queue and supervisor with fake workers

**Estimated effort:** 2–4 focused sessions.

Tasks:

- Create SQLite schema and migrations.
- Implement task lifecycle, priority selection, bounded retry and events.
- Implement a fake worker that returns predictable success/failure results.
- Add a policy interface and tool registry.
- Add safe startup/shutdown and recovery for orphaned tasks.
- Add tests for queue state transitions.

**Done when:** enqueue, run, fail, retry, cancel and recover workflows work without using an LLM.

### Phase 3 — Model manager and local chat

**Estimated effort:** 2–4 focused sessions.

Tasks:

- Implement a runtime adapter for the selected local model server.
- Add health check, request timeout, model load/unload, context limit and error handling.
- Connect Alice conversation to the model.
- Enforce structured-output validation for task proposals.
- Compare resident versus on-demand policy.
- Ensure the manager is the only module that manages model lifecycle.

**Done when:** Alice can converse, propose a task, receive a validated model response and return a useful failure message when the runtime is unavailable.

### Phase 4 — First safe tools

**Estimated effort:** 2–5 focused sessions.

Tasks:

- Implement approved-directory file search.
- Implement allowlisted application launch.
- Implement reading/summarising a selected text file.
- Implement a known test command for a known repository, not arbitrary shell text.
- Add path containment, output limits, logging and result verification.
- Add explicit approval flow for any write or sensitive action.

**Done when:** at least two real tasks complete end-to-end, and disallowed paths/actions are blocked in tests.

### Phase 5 — Remote access and notifications

**Estimated effort:** 1–4 focused sessions; depends on existing connectivity.

Tasks:

- Inspect existing Telegram/Tailscale integration before adding a new transport.
- Add authenticated remote task submission and status lookup.
- Apply request-size and rate limits.
- Verify remote clients can only reach the intended service.
- Test reconnect, duplicate command submission and remote errors.

**Done when:** an authenticated phone request creates one task, can be tracked, and returns a result without exposing the raw model endpoint.

### Phase 6 — Server/night modes and timers

**Estimated effort:** 2–4 focused sessions.

Tasks:

- Implement mode policy and transition events.
- Add one bounded scheduled job.
- Add per-task CPU/RAM/time/network limits to the extent supported by the implementation.
- Add checkpoint and restart recovery tests.
- Add systemd service/timer only after manual operation is stable.
- Define awake, display-off, suspend and reboot behaviour.

**Done when:** queued jobs can run overnight under limits, mode transitions do not corrupt tasks, and reboot recovery is tested.

### Phase 7 — Memory and learning reports

**Estimated effort:** 1–3 focused sessions.

Tasks:

- Add Markdown structure for project state and summaries.
- Implement explicit memory update proposals rather than automatic full-chat capture.
- Add a project-state report using current queue/Git data.
- Add a short user-selected learning digest.
- Decide whether Obsidian helps navigation.

**Done when:** summaries are readable, traceable to source tasks/files and do not overwrite authoritative preferences without approval.

### Phase 8 — Voice

**Estimated effort:** 2–5 focused sessions for push-to-talk; wake word later.

Tasks:

- Implement push-to-talk recording state and local transcription.
- Route transcript through the existing task pathway.
- Measure recognition quality/latency/CPU.
- Add local TTS if worthwhile.
- Evaluate wake-word detector and false activations.

**Done when:** voice requests use the same permissions, can be cancelled/muted, and do not destabilise interactive mode.

### Phase 9 — Screen awareness and controlled desktop use

**Estimated effort:** several focused sessions to multiple weeks depending on Wayland/application compatibility.

Tasks:

- Test active-window and accessibility information.
- Add OCR for supported screen types.
- Add screenshot capture scoped to a window/region.
- Test a single browser workflow before general desktop control.
- Add vision worker on demand.
- Validate target, perform one action, re-observe and verify.
- Add approval gates for sensitive actions.

**Done when:** a defined browser task is reliably handled or fails safely; the system does not blindly chain clicks.

### Phase 10 — Dashboard and specialist roles

**Estimated effort:** optional; scope depends on actual use.

Tasks:

- Add a dashboard only after the CLI/status page is insufficient.
- Add role-based workflows (researcher, coder, reviewer) as task templates first.
- Separate models only when tests show meaningful quality or latency gains.
- Add scheduled read-only audits and a morning report.

**Done when:** each new role has a clear job, measurable benefit, permissions, tests and a resource budget.

---

## 16. Acceptance Criteria for a Stable Prototype

Do not call the system “workable” merely because a demo succeeds once. The prototype should meet these criteria:

### Reliability

- A queued task survives supervisor restart.
- A task cannot remain “running” forever without a timeout/recovery decision.
- Worker crashes produce bounded retries and useful errors.
- Duplicate requests do not accidentally repeat non-idempotent actions.
- A mode transition does not corrupt current task state.

### Performance

- Interactive use remains acceptably responsive under the selected resident model.
- Model loading/unloading follows the budget.
- Swap growth and desktop latency are recorded in tests.
- Two-model concurrency remains off unless its tests pass.

### Safety

- The model cannot bypass the tool registry or policy engine.
- Arbitrary model-generated shell commands are denied.
- Sensitive operations need specific approval.
- Remote access is authenticated and limited to the intended gateway.
- Untrusted page/document instructions cannot change the policy.
- Logs avoid secrets and unnecessary private content.

### Usability

- The task queue/status is inspectable.
- Failures explain what happened and what is needed next.
- Results link back to their input task/files.
- Memory updates are readable and selective.
- The system still has a useful fallback when no LLM is loaded.

---

## 17. Initial Audit Commands

Run these first from a terminal; they only inspect the machine and do not change system state:

```bash
# Current memory and swap
free -h
swapon --show

# CPU and load
nproc
uptime
lscpu | sed -n '1,24p'

# Largest current processes
ps -eo pid,comm,%cpu,%mem --sort=-%mem | head -15

# Filesystem capacity
 df -h

# Python and Git versions
python3 --version
git --version

# If currently in the Xian Bai repository, inspect state without changing it:
git status --short --branch
git log -5 --oneline
```

If run outside the repository, `git status` will report that it is not a repository; this is harmless. First `cd` into the confirmed Xian Bai project directory before collecting project-specific Git data. Do not paste tokens, bot secrets, private keys or `.env` contents into chat.

### Machine inventory to collect

- Current project path and repo branch.
- Whether the working tree has changes that need preserving.
- Existing module/file tree (exclude secrets and large data folders).
- Whether the current Telegram bot/router/state modules work.
- Available disk space for model files.
- Current model runtime installation/status, if any.
- Current Tailscale state, without sharing auth keys.
- Current desktop session type (Wayland/X11) and whether remote desktop sharing works.

### Initial command output to keep

Save the baseline to a local file such as `docs/baseline-2026-10-18.md` in the project only after verifying that the file contains no private identifiers or secrets. Otherwise, keep it in a private local data directory outside Git.

---

## 18. First Work Session Checklist

Do these in order. Do not install new models or rewrite code before finishing the audit.

- [ ] Locate the existing Xian Bai project.
- [ ] Check and preserve current Git changes.
- [ ] Record current machine health and disk space.
- [ ] Read the current command router, state/history modules and existing bot entry point.
- [ ] Identify existing remote access and model runtime instead of duplicating them.
- [ ] List which functions already work and which are broken or unfinished.
- [ ] Create a short reuse/repair/defer map.
- [ ] Select model candidates for benchmark only after the resource check.
- [ ] Agree on the first vertical slice: persistent queue + one safe tool + result notification.

**First vertical slice recommendation:** “Submit a task → store it → search an approved folder → return the matching path → record and report the result.” This demonstrates the queue, permissions, tools and reporting with less risk than GUI control or overnight autonomy.

---

## 19. Decisions That Must Remain Explicit

The following are not to be guessed by implementation code:

- Which folder paths Alice may read or write.
- Which remote devices can submit tasks.
- Whether the chat model stays resident during server mode.
- Whether voice activation is enabled.
- Which proactive night jobs are permitted.
- How long logs, audio, screenshots and generated artifacts are retained.
- Which applications and websites may be controlled.
- What counts as a sensitive/destructive action requiring approval.
- Whether an external/cloud model is ever allowed and which data may leave the machine.
- Whether laptop sleep/suspend policy changes for server operation.

Store configuration in a human-readable file with conservative defaults. Secrets should be provided through an appropriate local secret/environment mechanism, not committed to Git or written into Markdown logs.

---

## 20. Inspiration from the Extracted Local-Agent Setup

The extracted file `Tina Huang's Local AI Setup.md` describes several ideas worth adapting:

| Idea from the source | Alice adaptation | What not to copy blindly |
|---|---|---|
| Agents have defined roles | Define task templates and capabilities | Do not start with many independently running agents |
| Markdown-based memory | Keep readable project notes and daily summaries | Do not record every conversation or make memory an unreviewed truth source |
| Scheduled “heartbeat” jobs | Use bounded scheduled tasks and explicit timers | Avoid endless polling loops and unrestricted autonomous work |
| Mission Control dashboard | Start with a simple status view, then build a dashboard if useful | Avoid spending time on visual polish before the queue is reliable |
| Discord channels for workflows | Reuse working Telegram or another transport first; add Discord only if needed | Do not create a new communication platform without a use case |
| Separate small/strong models by workload | Benchmark models and load specialists on demand | Do not assume the named models or their reported capabilities fit this laptop |
| Dedicated machine for agent safety | Use unprivileged accounts, isolated directories and strict tool permissions on the existing laptop | A separate machine may eventually improve isolation, but it is not required for the first safe prototype |
| Scheduled security review | Combine deterministic checks with read-only model summaries | Never rely on an LLM as the only security control |
| One feature at a time | Ship one tested vertical slice per milestone | Do not implement several new features at once |

The screenshots and extracted notes are treated as inspiration supplied for this plan, not as an independent audit of that setup. Details such as model versions, costs and exact internals should be verified before being used as implementation requirements.

---

## 21. Reference Links

Use these official or primary project references when implementation reaches the relevant phase. Check the documentation again before installation because APIs and versions change.

- **Ollama FAQ — model residency, unload behaviour, context size and concurrency:** <https://github.com/ollama/ollama/blob/main/docs/faq.mdx>
- **Python `sqlite3` documentation — transactions and database interface:** <https://docs.python.org/3/library/sqlite3.html>
- **systemd service units:** <https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html>
- **systemd timer units:** <https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html>
- **Tailscale access control:** <https://tailscale.com/docs/features/access-control>
- **Tailscale grants:** <https://tailscale.com/docs/features/access-control/grants>
- **Playwright locators — semantic browser selectors and auto-waiting:** <https://playwright.dev/docs/locators>
- **whisper.cpp — local CPU-capable speech-to-text implementation:** <https://github.com/ggml-org/whisper.cpp>
- **openWakeWord — local wake-word detection project:** <https://github.com/tslapp/openwakeword>

These links help with later implementation; this document does not claim that all components have been installed or that any performance level has been proven on the target laptop.

---

## 22. Final Recommendation

Build Alice in this order:

1. **Audit and measure** the existing project and laptop.
2. **Benchmark four models** and choose a measured resident/fallback policy.
3. **Implement durable queue and supervisor with fake workers.**
4. **Connect one local model and a few safe tools.**
5. **Reuse the existing remote interface and add bounded scheduled work.**
6. **Add memory consolidation, push-to-talk, wake word and screen awareness incrementally.**
7. **Only then consider more agent roles and Mission Control.**

The system should improve your daily work early, not become another project that demands constant upkeep. Xian Bai remains the main project; Alice's supervisor, memory, models and interfaces are components that make it more capable.

**Next action:** complete Section 17 and Section 18, then use the observed machine and repository state to create the benchmark candidate list and implementation tasks. No large model download, broad permission grant or desktop-control installation is needed before that audit.
