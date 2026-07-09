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
    #    so we can see the Scheduler sort them). Two tasks share 08:00 on
    #    purpose (Mochi's feeding + Luna's breakfast) to trigger a conflict.
    mochi.add_task("Evening walk", "18:00", "daily")
    mochi.add_task("Morning feeding", "08:00", "daily")
    mochi.add_task("Heart meds", "08:30", "daily")
    luna.add_task("Feed Luna", "08:00", "daily")   # clashes with Mochi at 08:00
    luna.add_task("Litter box", "19:00", "daily")

    # 4. Print today's schedule
    scheduler = Scheduler(owner)

    print("=" * 40)
    print("TODAY'S SCHEDULE")
    print("=" * 40)
    print(scheduler.agenda())

    # 4b. Conflict detection: two tasks are booked at 08:00, so the Scheduler
    #     should flag it here rather than letting the clash slip by unnoticed.
    print()
    warning = scheduler.conflict_warning()
    if warning:
        print(warning)
        print("Clashing tasks:")
        for group in scheduler.find_conflicts():
            time = group[0][1].time
            for pet, task in group:
                print(f"  {time}  {pet.name}: {task.description}")
    else:
        print("No scheduling conflicts.")

    # 5. sort_by_time(): tasks were added out of order above; sort them.
    print()
    print("All tasks sorted by time:")
    all_tasks = [task for _pet, task in scheduler.all_tasks()]
    for task in scheduler.sort_by_time(all_tasks):
        print(f"  {task}")

    # 6. filter_tasks(): narrow down by pet name.
    print()
    print("Just Mochi's tasks (sorted):")
    mochi_tasks = [task for _pet, task in scheduler.filter_tasks(pet_name="Mochi")]
    for task in scheduler.sort_by_time(mochi_tasks):
        print(f"  {task}")

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

    # 7. filter_tasks(): split by completion status.
    print()
    print("Completed so far:")
    for pet, task in scheduler.filter_tasks(completed=True):
        print(f"  {pet.name}: {task}")
    print("Still pending:")
    for pet, task in scheduler.filter_tasks(completed=False):
        print(f"  {pet.name}: {task}")


if __name__ == "__main__":
    main()
