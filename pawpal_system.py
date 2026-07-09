"""PawPal+ logic layer.

Backend classes for the pet care planning assistant.

Four core classes:
  - Task      : a single care activity (description, time, frequency, done?)
  - Pet       : pet details and its list of tasks
  - Owner     : manages multiple pets and exposes all their tasks
  - Scheduler : the "brain" that retrieves, organizes, and manages tasks
                across all of an owner's pets

Task and Pet are dataclasses to keep the data clean. Mirrors diagrams/uml.mmd.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """A single care activity for a pet."""

    description: str
    time: str                 # 24-hour "HH:MM", e.g. "08:00"
    frequency: str = "daily"  # "once", "daily", "weekly", ...
    completed: bool = False
    due_date: date = field(default_factory=date.today)  # when it's next due
    last_completed: Optional[date] = None                # when last marked done, or None

    def mark_complete(self, today=None):
        """Mark this task done for its current occurrence.

        Recurring tasks (daily/weekly) roll their due_date forward to the
        next occurrence so they reappear on that day; 'once' (and any other)
        tasks simply stay done. `completed` stays True until refresh() reopens
        it on the next due day.

        Args:
            today: reference date used to stamp last_completed and compute the
                next due_date; defaults to the real current date when None.
        """
        if today is None:
            today = date.today()
        self.completed = True
        self.last_completed = today
        if self.frequency == "daily":
            self.due_date = today + timedelta(days=1)
        elif self.frequency == "weekly":
            self.due_date = today + timedelta(days=7)

    def mark_incomplete(self):
        """Mark this task as not done."""
        self.completed = False

    def toggle(self):
        """Flip the completion status."""
        self.completed = not self.completed

    def refresh(self, today=None):
        """Reopen a recurring task once its next due date has arrived.

        Call at the start of a day: a completed daily/weekly task whose
        due_date is today or earlier flips back to pending so it shows up in
        the plan again. One-off tasks are never reopened.

        Args:
            today: reference date compared against due_date; defaults to the
                real current date when None.

        Returns:
            True if the task was reopened, else False.
        """
        if today is None:
            today = date.today()
        if (self.completed
                and self.frequency in ("daily", "weekly")
                and today >= self.due_date):
            self.completed = False
            return True
        return False

    def __str__(self):
        """Render the task as a checkbox line for display."""
        box = "x" if self.completed else " "
        return f"[{box}] {self.time}  {self.description} ({self.frequency})"


@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str = "dog"
    breed: str = ""
    tasks: list = field(default_factory=list)  # list[Task]

    def add_task(self, description, time, frequency="daily"):
        """Create a Task, attach it to this pet, and return it."""
        task = Task(description, time, frequency)
        self.tasks.append(task)
        return task

    def remove_task(self, task):
        """Remove a task from this pet (no error if it isn't there)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def pending_tasks(self):
        """Return this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def completed_tasks(self):
        """Return this pet's tasks that are completed."""
        return [t for t in self.tasks if t.completed]

    def __str__(self):
        """Render the pet's name, breed/species, and task count."""
        label = self.breed or self.species
        return f"{self.name} ({label}) — {len(self.tasks)} task(s)"


@dataclass
class Owner:
    """An owner who manages one or more pets."""

    name: str
    phone: str = ""
    pets: list = field(default_factory=list)  # list[Pet]

    def add_pet(self, name, species="dog", breed=""):
        """Create a Pet, add it to this owner, and return it."""
        pet = Pet(name, species, breed)
        self.pets.append(pet)
        return pet

    def remove_pet(self, pet):
        """Remove a pet from this owner (no error if it isn't there)."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pet(self, name):
        """Find one of this owner's pets by name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def all_tasks(self):
        """Return every (pet, task) pair across all of this owner's pets."""
        pairs = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs


class Scheduler:
    """The brain: retrieves, organizes, and manages tasks across pets.

    Wraps a single Owner and works over all of that owner's pets' tasks.
    """

    def __init__(self, owner):
        """Wrap the owner whose pets' tasks this scheduler manages."""
        self.owner = owner

    def all_tasks(self):
        """All (pet, task) pairs for the owner."""
        return self.owner.all_tasks()

    def pending_tasks(self):
        """(pet, task) pairs that are not yet completed."""
        return self.filter_tasks(completed=False)

    def completed_tasks(self):
        """(pet, task) pairs that are completed."""
        return self.filter_tasks(completed=True)

    def tasks_for_pet(self, name):
        """All tasks for one pet by name, or an empty list if not found."""
        pet = self.owner.get_pet(name)
        return list(pet.tasks) if pet else []

    def refresh_due(self, today=None):
        """Reopen every recurring task whose due date has arrived.

        Call at the start of a day (or before building the agenda) so
        completed daily/weekly tasks reappear.

        Args:
            today: reference date, forwarded to Task.refresh(); defaults to the
                real current date when None.

        Returns:
            The number of tasks that were reopened.
        """
        return sum(task.refresh(today) for _pet, task in self.all_tasks())

    def filter_tasks(self, completed=None, pet_name=None):
        """Return (pet, task) pairs matching the given criteria.

        Both filters are optional and combine with AND. With no arguments,
        returns every (pet, task) pair.

        Args:
            completed: True -> only done tasks, False -> only pending,
                None (default) -> don't filter on status.
            pet_name: case-insensitive pet name to match; None (default) ->
                all pets.

        Returns:
            A list of the matching (pet, task) pairs, in the pets' insertion
            order.
        """
        pairs = self.all_tasks()
        if completed is not None:
            pairs = [(pet, task) for pet, task in pairs
                     if task.completed == completed]
        if pet_name is not None:
            key = pet_name.lower()
            pairs = [(pet, task) for pet, task in pairs
                     if pet.name.lower() == key]
        return pairs

    def sort_by_time(self, tasks):
        """Order Task objects chronologically by their start time.

        Times are stored as zero-padded 24-hour strings ("08:00"), so plain
        string comparison already orders them correctly without any parsing.

        Args:
            tasks: an iterable of Task objects.

        Returns:
            A new list of the tasks sorted earliest-first. The input is not
            modified.
        """
        return sorted(tasks, key=lambda task: task.time)

    def daily_schedule(self):
        """The day's plan: pending (pet, task) pairs ordered by time."""
        return sorted(self.pending_tasks(), key=lambda pair: pair[1].time)

    def next_task(self):
        """Find the single earliest pending task across all pets.

        Uses a one-pass min() rather than sorting the whole plan, since only
        the first item is needed.

        Returns:
            The earliest pending (pet, task) pair by time, or None if every
            task is complete.
        """
        pending = self.pending_tasks()
        return min(pending, key=lambda pair: pair[1].time) if pending else None

    def find_conflicts(self, include_completed=False):
        """Detect time clashes across all of the owner's pets.

        Returns a list of conflict groups, where each group is a list of
        (pet, task) pairs scheduled at the identical time. Only groups with
        two or more pairs are returned (a lone task isn't a clash). Clashes
        between different pets and within a single pet are both reported.

        Tasks with a blank or missing time are ignored (they can't clash on a
        time slot).

        Args:
            include_completed: if False (default) only pending tasks are
                checked, since completed tasks no longer compete for the
                owner's time; if True, every task is checked.

        Returns:
            A list of conflict groups ordered by time, where each group is a
            list of two or more (pet, task) pairs sharing the same time. Empty
            if there are no clashes.
        """
        pairs = self.all_tasks() if include_completed else self.pending_tasks()
        by_time = {}
        for pet, task in pairs:
            time = getattr(task, "time", None)
            if not time:            # a task with no time can't clash on a slot
                continue
            by_time.setdefault(time, []).append((pet, task))
        return [group for _time, group in sorted(by_time.items())
                if len(group) > 1]

    def has_conflicts(self, include_completed=False):
        """Report whether the schedule contains any time clash.

        Args:
            include_completed: passed through to find_conflicts(); see there.

        Returns:
            True if any two tasks share a time, else False.
        """
        return bool(self.find_conflicts(include_completed))

    def conflict_report(self, include_completed=False):
        """Build a multi-line, human-readable summary of time clashes.

        Args:
            include_completed: passed through to find_conflicts(); see there.

        Returns:
            A string with one line per clashing time slot listing the pets and
            tasks involved, or "No scheduling conflicts." when the plan is
            clear.
        """
        conflicts = self.find_conflicts(include_completed)
        if not conflicts:
            return "No scheduling conflicts."
        lines = ["Scheduling conflicts:"]
        for group in conflicts:
            time = group[0][1].time
            who = ", ".join(f"{pet.name}: {task.description}"
                            for pet, task in group)
            lines.append(f"  {time} — {who}")
        return "\n".join(lines)

    def conflict_warning(self, include_completed=False):
        """Lightweight, crash-proof conflict check for display in the UI.

        Formats the groups found by find_conflicts(), wrapped in a guard so
        any unexpected error yields a warning string instead of crashing the
        program (useful for calling directly from UI code).

        Args:
            include_completed: passed through to find_conflicts(); see there.

        Returns:
            A short one-line warning string when two or more tasks share a
            time, or an empty string ("") when the schedule is clear.
        """
        try:
            conflicts = self.find_conflicts(include_completed)
            if not conflicts:
                return ""
            times = ", ".join(group[0][1].time for group in conflicts)
            return (f"⚠️ Scheduling conflict: {len(conflicts)} time slot(s) "
                    f"with overlapping tasks ({times}).")
        except Exception:
            # Never let a conflict check take down the app.
            return "⚠️ Could not check for scheduling conflicts."

    def complete_task(self, task):
        """Mark a given task complete. Returns True if it belonged to the owner."""
        for _pet, owned_task in self.all_tasks():
            if owned_task is task:
                task.mark_complete()
                return True
        return False

    def agenda(self):
        """A human-readable daily agenda, ordered by time and grouped per line."""
        schedule = self.daily_schedule()
        if not schedule:
            return f"{self.owner.name}'s pets are all caught up — no pending tasks."
        lines = [f"Today's plan for {self.owner.name}:"]
        for pet, task in schedule:
            lines.append(f"  {task.time}  {pet.name}: {task.description} ({task.frequency})")
        remaining = len(schedule)
        done = len(self.completed_tasks())
        lines.append(f"({remaining} to do, {done} done)")
        return "\n".join(lines)
