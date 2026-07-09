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


@dataclass
class Task:
    """A single care activity for a pet."""

    description: str
    time: str                 # 24-hour "HH:MM", e.g. "08:00"
    frequency: str = "daily"  # "once", "daily", "weekly", ...
    completed: bool = False

    def mark_complete(self):
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self):
        """Mark this task as not done."""
        self.completed = False

    def toggle(self):
        """Flip the completion status."""
        self.completed = not self.completed

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
        return [(pet, task) for pet, task in self.all_tasks() if not task.completed]

    def completed_tasks(self):
        """(pet, task) pairs that are completed."""
        return [(pet, task) for pet, task in self.all_tasks() if task.completed]

    def tasks_for_pet(self, name):
        """All tasks for one pet by name, or an empty list if not found."""
        pet = self.owner.get_pet(name)
        return list(pet.tasks) if pet else []

    def daily_schedule(self):
        """The day's plan: pending (pet, task) pairs ordered by time."""
        return sorted(self.pending_tasks(), key=lambda pair: pair[1].time)

    def next_task(self):
        """The next pending (pet, task) pair by time, or None if all done."""
        schedule = self.daily_schedule()
        return schedule[0] if schedule else None

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
