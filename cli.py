"""PawPal+ interactive terminal app (no Streamlit required).

Run with:  python3 cli.py

A menu-driven front-end to the PawPal+ logic layer. Uses only the Python
standard library, so it runs anywhere without extra installs.
"""

from pawpal_system import Owner, Scheduler


def prompt(label, default=""):
    """Ask for input, falling back to a default on blank entry."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def add_pet(owner):
    name = prompt("Pet name")
    if not name:
        print("  ! Name is required.\n")
        return
    species = prompt("Species", "dog")
    breed = prompt("Breed", "")
    owner.add_pet(name, species, breed)
    print(f"  + Added {name}.\n")


def add_task(owner):
    if not owner.pets:
        print("  ! Add a pet first.\n")
        return
    print("  Pets: " + ", ".join(p.name for p in owner.pets))
    pet = owner.get_pet(prompt("Which pet"))
    if pet is None:
        print("  ! No pet by that name.\n")
        return
    description = prompt("Task description")
    if not description:
        print("  ! Description is required.\n")
        return
    time = prompt("Time (HH:MM)", "08:00")
    frequency = prompt("Frequency (once/daily/weekly)", "daily")
    pet.add_task(description, time, frequency)
    print(f"  + Added '{description}' for {pet.name} at {time}.\n")


def show_schedule(scheduler):
    print()
    print(scheduler.agenda())
    print()


def mark_done(scheduler):
    schedule = scheduler.daily_schedule()
    if not schedule:
        print("  Nothing pending.\n")
        return
    for i, (pet, task) in enumerate(schedule, start=1):
        print(f"  {i}. {task.time}  {pet.name}: {task.description}")
    choice = prompt("Number to mark done")
    if choice.isdigit() and 1 <= int(choice) <= len(schedule):
        _pet, task = schedule[int(choice) - 1]
        task.mark_complete()
        print(f"  * Completed '{task.description}'.\n")
    else:
        print("  ! Invalid choice.\n")


MENU = """\
==============================
        PawPal+ Menu
==============================
1. Add a pet
2. Add a task
3. Show today's schedule
4. Mark a task done
5. Quit
"""


def main():
    owner = Owner(name=prompt("Owner name", "Jordan"))
    scheduler = Scheduler(owner)
    print(f"\nWelcome, {owner.name}! Let's plan your pets' day.\n")

    while True:
        print(MENU)
        choice = prompt("Choose an option")
        if choice == "1":
            add_pet(owner)
        elif choice == "2":
            add_task(owner)
        elif choice == "3":
            show_schedule(scheduler)
        elif choice == "4":
            mark_done(scheduler)
        elif choice == "5":
            print("Goodbye! 🐾")
            break
        else:
            print("  ! Pick 1-5.\n")


if __name__ == "__main__":
    main()
