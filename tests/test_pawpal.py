"""Pytest tests for the PawPal+ domain model (pawpal_system.py)."""

from pawpal_system import Owner, Pet, Task


def _make_task(
    pet: Pet,
    *,
    name: str = "Walk",
    priority: int = 3,
    preferred_time_window: tuple[int, int] = (540, 600),
    recurring: bool = True,
) -> Task:
    """Build a simple, fully-specified Task for the given pet."""
    return Task(
        name=name,
        type="walk",
        duration=30,
        priority=priority,
        preferred_time_window=preferred_time_window,
        recurring=recurring,
        pet=pet,
    )


def test_task_completion():
    """mark_done() flips completed from False to True."""
    pet = Pet("Rex", "dog", 3)
    task = _make_task(pet)
    assert task.completed is False  # default before completion

    task.mark_done()

    assert task.completed is True


def test_pet_add_task():
    """add_task() grows the pet's task list by one and sets the back-reference."""
    pet = Pet("Milo", "cat", 5)
    count_before = len(pet.get_tasks())

    task = _make_task(pet)
    pet.add_task(task)

    assert len(pet.get_tasks()) == count_before + 1
    assert task.pet is pet


def test_sort_by_time_orders_by_start_then_priority():
    """sort_by_time() sorts by preferred start ascending, tiebreak priority desc."""
    owner = Owner("Sam", available_time_today=240, preferences={})
    pet = Pet("Rex", "dog", 3)
    owner.add_pet(pet)

    late = _make_task(pet, name="Late", preferred_time_window=(600, 660))
    early_low = _make_task(pet, name="EarlyLow", priority=1, preferred_time_window=(540, 600))
    early_high = _make_task(pet, name="EarlyHigh", priority=5, preferred_time_window=(540, 600))
    for task in (late, early_low, early_high):
        pet.add_task(task)

    ordered = owner.scheduler.sort_by_time()

    # Earliest window first; within the same window, higher priority wins.
    assert [t.name for t in ordered] == ["EarlyHigh", "EarlyLow", "Late"]


def test_tasks_for_pet_filters_by_name():
    """tasks_for_pet() returns only the named pet's tasks, empty for no match."""
    owner = Owner("Sam", available_time_today=240, preferences={})
    rex = Pet("Rex", "dog", 3)
    milo = Pet("Milo", "cat", 5)
    owner.add_pet(rex)
    owner.add_pet(milo)

    rex_task = _make_task(rex, name="RexWalk")
    milo_task = _make_task(milo, name="MiloFeed")
    rex.add_task(rex_task)
    milo.add_task(milo_task)

    assert owner.tasks_for_pet("Rex") == [rex_task]
    assert owner.tasks_for_pet("Milo") == [milo_task]
    assert owner.tasks_for_pet("Nobody") == []


def test_mark_done_recreates_recurring_task():
    """Completing a recurring task spawns a fresh, pending clone on the same pet."""
    pet = Pet("Rex", "dog", 3)
    task = _make_task(pet, recurring=True, preferred_time_window=(540, 600))
    task.scheduled_time = (540, 570)
    pet.add_task(task)

    task.mark_done()

    assert task.completed is True
    # Original stays as history; a new pending clone joins it.
    assert len(pet.get_tasks()) == 2
    assert len(pet.pending_tasks()) == 1

    clone = pet.pending_tasks()[0]
    assert clone is not task
    assert clone.completed is False
    assert clone.scheduled_time is None  # cleared for re-scheduling
    assert clone.pet is pet
    assert clone.name == task.name
    assert clone.preferred_time_window == task.preferred_time_window


def test_mark_done_one_off_does_not_recreate():
    """A non-recurring task just completes — no clone is added."""
    pet = Pet("Rex", "dog", 3)
    task = _make_task(pet, recurring=False)
    pet.add_task(task)

    task.mark_done()

    assert task.completed is True
    assert len(pet.get_tasks()) == 1
    assert pet.pending_tasks() == []
