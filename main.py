"""Manual test / demo for the PawPal+ logic layer.

Run with:  python3 main.py

Builds an owner with two pets and several care tasks, then prints the
day's schedule to the terminal using the Scheduler.
"""

from pawpal_system import Owner, Scheduler


def main():
    # 1. Create an owner
    owner = Owner(name="Jordan", phone="555-1234")

    # 2. Create two pets
    mochi = owner.add_pet("Mochi", species="dog", breed="Corgi")
    luna = owner.add_pet("Luna", species="cat")

    # 3. Add tasks with different times (added out of order on purpose,
    #    so we can see the Scheduler sort them)
    mochi.add_task("Evening walk", "18:00", "daily")
    mochi.add_task("Morning feeding", "08:00", "daily")
    mochi.add_task("Heart meds", "08:30", "daily")
    luna.add_task("Feed Luna", "07:30", "daily")
    luna.add_task("Litter box", "19:00", "daily")

    # 4. Print today's schedule
    scheduler = Scheduler(owner)

    print("=" * 40)
    print("TODAY'S SCHEDULE")
    print("=" * 40)
    print(scheduler.agenda())

    # Show what happens after completing the first task
    print()
    nxt = scheduler.next_task()
    if nxt:
        pet, task = nxt
        task.mark_complete()
        print(f"Marked done: {task.description} for {pet.name}")
        print()
        print("Updated schedule:")
        print(scheduler.agenda())


if __name__ == "__main__":
    main()
