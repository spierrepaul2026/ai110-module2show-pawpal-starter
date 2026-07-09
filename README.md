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

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The tests live in [`tests/test_pawpal_system.py`](tests/test_pawpal_system.py) and exercise
the logic layer in [`pawpal_system.py`](pawpal_system.py):

- **`Task`** — default values, and `mark_complete` / `mark_incomplete` / `toggle` state changes.
- **`Pet`** — adding, removing, and looking up tasks, plus splitting them into pending vs. completed.
- **`Owner`** — adding pets, case-insensitive pet lookup, and collecting every `(pet, task)` pair.
- **`Scheduler`** — time-ordered daily schedules across pets, `next_task`, completing tasks,
  per-pet task lists, and the human-readable agenda.
- **Sorting** — `sort_by_time` returns a chronological copy without mutating the caller's list.
- **Recurrence** — daily/weekly tasks roll their due date forward and reopen once the day arrives,
  while one-off tasks stay done.
- **Conflict detection** — tasks booked at the same time are flagged, across different pets and
  within a single pet, with no false positives when times differ.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/stephenpierre-paul/Desktop/A110 project/ai110-module2show-pawpal-starter
collected 25 items

tests/test_pawpal_system.py .........................                    [100%]

============================== 25 passed in 0.01s ==============================
```

## 📐 Smarter Scheduling

The scheduling "brain" lives in the `Scheduler` class in [`pawpal_system.py`](pawpal_system.py),
which wraps an `Owner` and works across all of that owner's pets' tasks. Each task
stores a description, a 24-hour `time` string (`"08:00"`), a `frequency`
(`once` / `daily` / `weekly`), and its completion state. The features below build on
that data.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.daily_schedule()`, `Scheduler.next_task()` | Chronological ordering by task time |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.pending_tasks()`, `Scheduler.completed_tasks()` | By pet name and/or completion status |
| Conflict handling | `Scheduler.find_conflicts()`, `Scheduler.has_conflicts()`, `Scheduler.conflict_report()`, `Scheduler.conflict_warning()` | Detects tasks booked at the same time |
| Recurring tasks | `Task.mark_complete()`, `Task.refresh()`, `Scheduler.refresh_due()` | Daily/weekly tasks roll forward and reappear |

### Sorting behavior

- **`Scheduler.sort_by_time(tasks)`** returns a new list of `Task` objects ordered
  earliest-first. Because times are stored as zero-padded 24-hour strings
  (`"08:00"`), plain string comparison already sorts chronologically — no date
  parsing needed. The original list is left unchanged.
- **`Scheduler.daily_schedule()`** applies the same ordering to the day's *pending*
  `(pet, task)` pairs to produce the plan.
- **`Scheduler.next_task()`** returns just the earliest pending task using a single
  `min()` pass (O(n)) instead of sorting the whole list, or `None` when everything
  is done.

### Filtering behavior

- **`Scheduler.filter_tasks(completed=None, pet_name=None)`** is the single filtering
  entry point. Both arguments are optional and combine with AND:
  - `completed=True` → only done tasks, `completed=False` → only pending,
    `None` → don't filter on status.
  - `pet_name` → case-insensitive match on a pet's name, `None` → all pets.
- **`Scheduler.pending_tasks()`** and **`Scheduler.completed_tasks()`** are thin
  shortcuts that delegate to `filter_tasks()`, so there is one source of truth for
  status filtering.

### Conflict detection logic

- **`Scheduler.find_conflicts(include_completed=False)`** buckets tasks by their
  `time` and returns groups of two or more `(pet, task)` pairs that share the same
  slot. It catches clashes **between different pets** and **within a single pet**,
  and ignores tasks with a blank/missing time. Only pending tasks are checked by
  default (completed tasks no longer compete for the owner's time).
- **`Scheduler.has_conflicts()`** returns a simple boolean for quick checks.
- **`Scheduler.conflict_report()`** produces a multi-line, human-readable summary
  (one line per clashing time slot).
- **`Scheduler.conflict_warning()`** is a crash-proof helper for UI code: it returns
  a short one-line warning string (or `""` when clear) and is guarded so an
  unexpected error yields a message instead of taking down the app.

### Recurring task logic

- **`Task.mark_complete(today=None)`** marks a task done for its current occurrence.
  For **daily** tasks it rolls `due_date` forward one day; for **weekly** tasks,
  seven days; **once** tasks simply stay done. `completed` stays `True` until the
  next due day.
- **`Task.refresh(today=None)`** reopens a completed daily/weekly task once its
  `due_date` has arrived, so it reappears in the plan. One-off tasks are never
  reopened.
- **`Scheduler.refresh_due(today=None)`** applies `refresh()` across every task and
  returns how many were reopened — call it at the start of a day (or before building
  the agenda). The optional `today` argument on all three methods makes the recurring
  logic deterministic and easy to test across simulated dates.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
