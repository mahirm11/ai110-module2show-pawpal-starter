"""Manual test script for the PawPal+ domain model.

Builds a small owner/pets/tasks scenario, generates a schedule, and prints the
scheduler's reasoning. Run with: python main.py
"""

import sys

from pawpal_system import Owner, Pet, Task


def main() -> None:
    # Ensure em dashes etc. render on any console (e.g. legacy Windows code pages).
    sys.stdout.reconfigure(encoding="utf-8")

    # One owner with a 90-minute care budget for today.
    owner = Owner("Mahir", available_time_today=90, preferences={})

    # Two pets.
    rex = Pet("Rex", "dog", 3)
    milo = Pet("Milo", "cat", 5)

    # Tasks with different preferred windows and mixed priorities, deliberately
    # added out of chronological order and split across the pets.
    # (windows are minutes-since-midnight: 540 = 9:00am, 600 = 10:00am, ...)
    tasks = [
        Task("Morning walk", "walk", 45, 4, (540, 600), True, rex),   # Rex, 9:00am
        Task("Feed cat", "feed", 10, 5, (420, 480), True, milo),      # Milo, 7:00am
        Task("Grooming", "groom", 40, 2, (660, 720), False, rex),     # Rex, 11:00am
        Task("Evening play", "play", 20, 3, (480, 540), True, milo),  # Milo, 8:00am
    ]
    for task in tasks:
        owner.add_task(task)

    owner.scheduler.generate_schedule()

    print("Today's Schedule")
    print(owner.scheduler.explain_reasoning())

    # Verify sort_by_time(): tasks should come out earliest-window first.
    print("\nTasks by time (sort_by_time):")
    for task in owner.scheduler.sort_by_time():
        print(f"  - {task.name}")

    # Verify tasks_for_pet(): only the named pet's tasks should appear.
    print("\nTasks for Milo (tasks_for_pet):")
    for task in owner.tasks_for_pet("Milo"):
        print(f"  - {task.name}")


if __name__ == "__main__":
    main()
