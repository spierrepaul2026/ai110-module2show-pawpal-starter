# 🐾 PawPal+

A pet care planner for busy owners. Add your pets and their care tasks, and PawPal+ builds a time-ordered daily plan across every pet, flags tasks booked at the same time, and brings daily and weekly tasks back once they're due again.

Built in Python with a Streamlit interface and a 25-test pytest suite. I designed the classes in UML first, then built the logic layer, then connected it to the UI.

**Built by Stephen Pierre-Paul** for CodePath AI110: Foundations of AI Engineering.

## Features

- **Daily plan across pets:** every pending task for every pet, sorted by time
- **Conflict detection:** flags two tasks booked in the same slot, for the same pet or different pets
- **Recurring tasks:** daily and weekly tasks roll forward when completed and reopen on their next due day
- **Filtering:** by pet and by done or pending
- **Tested:** 25 pytest tests cover tasks, pets, owners, scheduling, recurrence, and conflicts

## Tech stack

Python · Streamlit · pytest · Mermaid (UML diagrams in [`diagrams/`](diagrams/))

## Run it

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py   # web app
python main.py         # terminal demo
python -m pytest       # tests
```

## 🖥️ Sample Output

Output of `python main.py`, with two pets and a deliberate 08:00 clash:

```
Today's plan for Jordan:
  08:00  Mochi: Morning feeding (daily)
  08:00  Luna: Feed Luna (daily)
  08:30  Mochi: Heart meds (daily)
  18:00  Mochi: Evening walk (daily)
  19:00  Luna: Litter box (daily)
(5 to do, 0 done)

⚠️ Scheduling conflict: 1 time slot(s) with overlapping tasks (08:00).
Clashing tasks:
  08:00  Mochi: Morning feeding
  08:00  Luna: Feed Luna
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

1. Run `streamlit run app.py` and enter the owner's name and phone number.
2. Add one or more pets with a name, species, and breed.
3. Pick a pet and add care tasks, each with a time (HH:MM) and a frequency of once, daily, or weekly.
4. Click **Generate schedule** to see the day's plan sorted by time.
5. If two tasks share a time slot, PawPal+ shows a conflict warning; otherwise it confirms the day is clear.
6. Check off tasks as they're done. Daily and weekly tasks come back on their next due day.
