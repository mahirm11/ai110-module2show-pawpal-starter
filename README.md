# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

What PawPal+ actually implements today:

**Scheduling & sorting**
- **Priority-based scheduling** — `generate_schedule()` greedily places tasks highest-priority-first within the owner's daily time budget. Tasks that don't fit are *deferred*, never truncated.
- **Priority sort** (`sort_by_priority()`) — most-urgent first, tie-broken by earlier preferred start time.
- **Time sort** (`sort_by_time()`) — chronological by preferred start, tie-broken by higher priority (the mirror of the priority sort).
- **Explainable plans** — `explain_reasoning()` narrates why each task was scheduled or deferred, including how ties were resolved.

**Filtering**
- **By pet** — `Owner.tasks_for_pet(name)` returns just the named pet's tasks.
- **By completion status** — `Pet.pending_tasks()` hides already-completed tasks so they're never re-scheduled.

**Conflict detection**
- **Exact-overlap detection** — `detect_conflicts()` flags every pair of scheduled tasks whose time slots overlap. Slots are half-open intervals `[start, end)`, so tasks that merely touch end-to-start (e.g. 9:00–9:30 and 9:30–10:00) do **not** conflict.
- Conflicts are **flagged, not auto-resolved** — surfaced as pairs for the user to decide on.

**Recurring tasks**
- **Automatic recreation** — completing a recurring task via `Task.mark_done()` spawns a fresh, un-completed clone on the same pet, ready for the next schedule. One-off tasks simply complete.

**Domain model**
- `Owner`, `Pet`, `Task`, `Scheduler`, and a `Schedule` result object (`scheduled` / `deferred` / `conflicts`). The scheduler derives its task list directly from the owner's pets, so there's a single source of truth.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

My output after running `python main.py`:

```
Today's Schedule
Daily schedule for Mahir — 75/90 min committed, 3 scheduled, 1 deferred, 0 conflict(s):
  Feed cat scheduled at 7:00am — highest priority (5).
  Morning walk scheduled at 9:00am — priority 4.
  Evening play scheduled at 8:00am — priority 3.
  Grooming deferred — needs 40 min but only 15 min left in today's 90-min budget.
```

## Testing PawPal+

Run the test suite with:

```bash
python -m pytest
```

The suite covers task completion and addition, priority/time sorting, 
pet-based filtering, recurring task recreation, conflict detection 
(including exact-overlap and touching-boundary edge cases), and 
degenerate inputs (empty schedules, zero-duration tasks). Two tests 
intentionally pin current limitations rather than ideal behavior — 
same-day recurring task reappearance and non-idempotent `mark_done()` 
— both documented as known tradeoffs.

**Confidence level:** 4/5 stars — solid coverage across sorting, 
recurring tasks, and conflict detection, including boundary cases 
like touching (non-overlapping) time slots. The remaining gap is two 
known, documented limitations (recurring tasks can reappear same-day, 
`mark_done()` isn't idempotent) rather than untested code.

Sample output:
```
========================================================================== test session starts ==========================================================================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\mahir\OneDrive\Documents\CS\CodePath\AI_110\Projects\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 12 items                                                                                                                                                       

tests\test_pawpal.py ............                                                                                                                                  [100%]

========================================================================== 12 passed in 0.06s ===========================================================================

```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method |
|---|---|
| Sorting by priority | `Scheduler.sort_by_priority()` |
| Sorting by time | `Scheduler.sort_by_time()` |
| Filtering by pet | `Owner.tasks_for_pet(name)` |
| Filtering by completion status | `Pet.pending_tasks()` |
| Conflict detection | `Scheduler.detect_conflicts()` |
| Recurring tasks | `Task.mark_done()` (auto-recreates recurring tasks when completed) |

## 📸 Demo Walkthrough

Launch the app with:

```bash
streamlit run app.py
```

### What the UI lets you do

- **Set the owner + daily budget** — enter an owner name and the minutes available today; the budget stays live, so changing it affects the next schedule.
- **Manage pets** — add pets (name + species) and delete any you no longer need.
- **Manage tasks** — add a task (title, category, duration, priority, preferred start time) for a specific pet, and delete tasks individually.
- **Choose how tasks are listed** — a **View** toggle switches between **By priority** and **By time**, driven by `sort_by_priority()` / `sort_by_time()`.
- **Filter the list by pet** — a dropdown (**All pets** + one entry per pet) filters via `tasks_for_pet()` while keeping the chosen sort order.
- **Generate and read the plan** — a **Generate schedule** button builds the day and explains it.

### Example workflow

1. Set the owner to *Jordan* and the daily budget to *120* minutes.
2. **Add a pet** — enter `Mochi`, species `dog`, and click **Add pet**.
3. **Add a task** — `Morning walk`, category `walk`, 20 min, priority `high`, preferred start `9:00am`, for `Mochi`; click **Add task**.
4. Add a second task at the same 9:00am start (e.g. `Feeding`) to see how conflicts surface.
5. Flip the **View** toggle between *By priority* and *By time* and watch the list reorder.
6. Optionally set **Filter by pet** to `Mochi` to narrow the list.
7. Click **Generate schedule** to see today's plan and reasoning.

### Scheduler behaviors visible in the UI

- **Sorting toggle** — the task list reorders instantly between priority order and chronological order.
- **Conflict warnings** — when two scheduled tasks overlap, the result is shown as a prominent `st.warning()` block listing each conflicting pair by name and time. A clean plan instead shows an `st.success()` banner. Either way, the full natural-language reasoning appears underneath.

### Sample CLI output

Running the scenario in `main.py` (one owner, two pets, four mixed-priority tasks, 90-min budget):

```
Today's Schedule
Daily schedule for Mahir — 75/90 min committed, 3 scheduled, 1 deferred, 0 conflict(s):
  Feed cat scheduled at 7:00am — highest priority (5).
  Morning walk scheduled at 9:00am — priority 4.
  Evening play scheduled at 8:00am — priority 3.
  Grooming deferred — needs 40 min but only 15 min left in today's 90-min budget.

Tasks by time (sort_by_time):
  - Feed cat
  - Evening play
  - Morning walk
  - Grooming

Tasks for Milo (tasks_for_pet):
  - Feed cat
  - Evening play
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
