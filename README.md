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
Daily schedule for Mahir — 55/90 min committed, 2 scheduled, 1 deferred:
  Feed cat scheduled at 7:00am — highest priority (5).
  Morning walk scheduled at 9:00am — priority 4.
  Grooming deferred — needs 40 min but only 35 min left in today's 90-min budget.
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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
