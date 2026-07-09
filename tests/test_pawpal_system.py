"""Automated tests for the PawPal+ logic layer.

Run with:  python3 -m pytest
"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler


# --- Task ------------------------------------------------------------------

def test_task_defaults():
    task = Task("Morning walk", "08:00")
    assert task.frequency == "daily"
    assert task.completed is False


def test_task_mark_complete_and_toggle():
    task = Task("Meds", "08:30")
    task.mark_complete()
    assert task.completed is True
    task.mark_incomplete()
    assert task.completed is False
    task.toggle()
    assert task.completed is True


# --- Pet -------------------------------------------------------------------

def test_pet_add_task_returns_and_attaches():
    pet = Pet("Mochi", "dog", "Corgi")
    task = pet.add_task("Walk", "18:00")
    assert task in pet.tasks
    assert len(pet.tasks) == 1


def test_pet_pending_and_completed_split():
    pet = Pet("Luna", "cat")
    t1 = pet.add_task("Feed", "07:30")
    t2 = pet.add_task("Litter", "19:00")
    t1.mark_complete()
    assert pet.completed_tasks() == [t1]
    assert pet.pending_tasks() == [t2]


def test_pet_remove_task():
    pet = Pet("Mochi")
    task = pet.add_task("Walk", "18:00")
    pet.remove_task(task)
    assert pet.tasks == []
    # removing again is a no-op, not an error
    pet.remove_task(task)


# --- Owner -----------------------------------------------------------------

def test_owner_add_pet():
    owner = Owner("Jordan")
    pet = owner.add_pet("Mochi", "dog", "Corgi")
    assert pet in owner.pets
    assert pet.name == "Mochi"


def test_owner_get_pet_case_insensitive():
    owner = Owner("Jordan")
    owner.add_pet("Mochi")
    assert owner.get_pet("mochi").name == "Mochi"
    assert owner.get_pet("MOCHI").name == "Mochi"
    assert owner.get_pet("nope") is None


def test_owner_all_tasks_returns_pet_task_pairs():
    owner = Owner("Jordan")
    mochi = owner.add_pet("Mochi")
    luna = owner.add_pet("Luna", "cat")
    mochi.add_task("Walk", "18:00")
    luna.add_task("Feed", "07:30")
    pairs = owner.all_tasks()
    assert len(pairs) == 2
    # each pair is (pet, task) and links back to the right pet
    for pet, task in pairs:
        assert task in pet.tasks


# --- Scheduler -------------------------------------------------------------

@pytest.fixture
def owner_with_tasks():
    """An owner with two pets and tasks added out of time order."""
    owner = Owner("Jordan")
    mochi = owner.add_pet("Mochi", "dog", "Corgi")
    luna = owner.add_pet("Luna", "cat")
    mochi.add_task("Evening walk", "18:00")
    mochi.add_task("Morning feeding", "08:00")
    luna.add_task("Feed Luna", "07:30")
    return owner


def test_daily_schedule_is_time_ordered_across_pets(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    times = [task.time for _pet, task in scheduler.daily_schedule()]
    assert times == ["07:30", "08:00", "18:00"]


def test_daily_schedule_excludes_completed(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    # complete the earliest task
    _pet, task = scheduler.daily_schedule()[0]
    task.mark_complete()
    times = [t.time for _p, t in scheduler.daily_schedule()]
    assert "07:30" not in times
    assert times == ["08:00", "18:00"]


def test_next_task_is_soonest(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    pet, task = scheduler.next_task()
    assert task.time == "07:30"
    assert pet.name == "Luna"


def test_next_task_none_when_all_done(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    for _pet, task in scheduler.all_tasks():
        task.mark_complete()
    assert scheduler.next_task() is None


def test_complete_task_returns_true_for_owned_task(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    _pet, task = scheduler.all_tasks()[0]
    assert scheduler.complete_task(task) is True
    assert task.completed is True


def test_complete_task_returns_false_for_foreign_task(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    stranger = Task("Not ours", "09:00")
    assert scheduler.complete_task(stranger) is False


def test_tasks_for_pet(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    assert len(scheduler.tasks_for_pet("Mochi")) == 2
    assert scheduler.tasks_for_pet("Ghost") == []


def test_agenda_mentions_owner_and_tasks(owner_with_tasks):
    scheduler = Scheduler(owner_with_tasks)
    text = scheduler.agenda()
    assert "Jordan" in text
    assert "Feed Luna" in text
    assert "3 to do" in text


def test_agenda_when_all_caught_up():
    owner = Owner("Jordan")
    scheduler = Scheduler(owner)
    assert "caught up" in scheduler.agenda()


# --- Sorting correctness ---------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks added out of order come back earliest-first."""
    tasks = [
        Task("Evening walk", "18:00"),
        Task("Morning feeding", "08:00"),
        Task("Midday check", "12:30"),
    ]
    scheduler = Scheduler(Owner("Jordan"))
    ordered = scheduler.sort_by_time(tasks)
    assert [t.time for t in ordered] == ["08:00", "12:30", "18:00"]


def test_sort_by_time_does_not_mutate_input():
    """Sorting returns a new list; the caller's list is left untouched."""
    tasks = [Task("Later", "18:00"), Task("Earlier", "08:00")]
    scheduler = Scheduler(Owner("Jordan"))
    scheduler.sort_by_time(tasks)
    assert [t.time for t in tasks] == ["18:00", "08:00"]


# --- Recurrence logic ------------------------------------------------------

def test_daily_task_reopens_for_the_following_day():
    """Completing a daily task schedules its next occurrence one day later,
    and refresh() reopens it once that day arrives.

    Note: this code rolls the SAME task's due_date forward rather than
    creating a new Task object; the recurrence is the task reappearing.
    """
    today = date(2026, 7, 9)
    task = Task("Morning walk", "08:00", frequency="daily")

    task.mark_complete(today=today)
    assert task.completed is True
    # next occurrence is scheduled for the following day
    assert task.due_date == today + timedelta(days=1)

    # same day: still done, does not reappear yet
    assert task.refresh(today=today) is False
    assert task.completed is True

    # the following day: it reopens for its new occurrence
    tomorrow = today + timedelta(days=1)
    assert task.refresh(today=tomorrow) is True
    assert task.completed is False


def test_once_task_never_reopens():
    """A one-off task stays done and is never rescheduled."""
    today = date(2026, 7, 9)
    task = Task("Vet appointment", "14:00", frequency="once")
    task.mark_complete(today=today)
    # due_date is not rolled forward for one-off tasks
    later = today + timedelta(days=30)
    assert task.refresh(today=later) is False
    assert task.completed is True


def test_scheduler_refresh_due_reopens_recurring_tasks():
    """refresh_due reopens every recurring task whose due date has arrived
    and reports how many were reopened."""
    today = date(2026, 7, 9)
    owner = Owner("Jordan")
    pet = owner.add_pet("Mochi")
    daily = pet.add_task("Feed", "08:00", frequency="daily")
    scheduler = Scheduler(owner)

    daily.mark_complete(today=today)
    reopened = scheduler.refresh_due(today=today + timedelta(days=1))
    assert reopened == 1
    assert daily.completed is False


# --- Conflict detection ----------------------------------------------------

def test_find_conflicts_flags_duplicate_times():
    """Two tasks scheduled at the same time are reported as one clash group."""
    owner = Owner("Jordan")
    mochi = owner.add_pet("Mochi")
    luna = owner.add_pet("Luna", "cat")
    mochi.add_task("Walk", "08:00")
    luna.add_task("Feed", "08:00")
    scheduler = Scheduler(owner)

    conflicts = scheduler.find_conflicts()
    assert len(conflicts) == 1
    assert len(conflicts[0]) == 2           # both tasks in the clash group
    assert scheduler.has_conflicts() is True


def test_no_conflict_when_times_differ():
    """Distinct times produce no clash."""
    owner = Owner("Jordan")
    pet = owner.add_pet("Mochi")
    pet.add_task("Walk", "08:00")
    pet.add_task("Dinner", "18:00")
    scheduler = Scheduler(owner)

    assert scheduler.find_conflicts() == []
    assert scheduler.has_conflicts() is False


def test_same_pet_tasks_at_same_time_conflict():
    """A clash within a single pet's own schedule is still reported."""
    owner = Owner("Jordan")
    pet = owner.add_pet("Mochi")
    pet.add_task("Walk", "08:00")
    pet.add_task("Meds", "08:00")
    scheduler = Scheduler(owner)

    conflicts = scheduler.find_conflicts()
    assert len(conflicts) == 1
    assert len(conflicts[0]) == 2
