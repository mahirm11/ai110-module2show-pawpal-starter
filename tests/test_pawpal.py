"""Pytest tests for the PawPal+ domain model (pawpal_system.py)."""

from pawpal_system import Owner, Pet, Task


def _make_task(
    pet: Pet,
    *,
    name: str = "Walk",
    priority: int = 3,
    duration: int = 30,
    preferred_time_window: tuple[int, int] = (540, 600),
    recurring: bool = True,
) -> Task:
    """Build a simple, fully-specified Task for the given pet."""
    return Task(
        name=name,
        type="walk",
        duration=duration,
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


# --- edge cases: empty schedule, conflicts, recurring, zero-duration --------


def test_empty_schedule_does_not_crash():
    """No tasks (including a pet with none) → empty schedule, no crash."""
    owner = Owner("Sam", available_time_today=240, preferences={})
    owner.add_pet(Pet("Rex", "dog", 3))  # a pet with no tasks at all

    schedule = owner.scheduler.generate_schedule()

    assert schedule.scheduled == []
    assert schedule.deferred == []
    assert schedule.conflicts == []
    assert owner.scheduler.sort_by_priority() == []
    # explain_reasoning() summarizes zero counts rather than raising.
    assert "0 scheduled" in owner.scheduler.explain_reasoning()


def test_exact_same_slot_conflicts():
    """Two tasks placed at the identical slot are flagged as one conflict."""
    owner = Owner("Sam", available_time_today=240, preferences={})
    pet = Pet("Rex", "dog", 3)
    owner.add_pet(pet)
    a = _make_task(pet, name="A", preferred_time_window=(540, 600))
    b = _make_task(pet, name="B", preferred_time_window=(540, 600))
    pet.add_task(a)
    pet.add_task(b)

    schedule = owner.scheduler.generate_schedule()

    # Both start at their (identical) preferred window start.
    assert a.scheduled_time == (540, 570)
    assert b.scheduled_time == (540, 570)
    assert len(schedule.conflicts) == 1
    assert set(schedule.conflicts[0]) == {a, b}


def test_end_to_start_does_not_conflict():
    """Half-open [start, end) slots that merely touch (600|600) do not conflict."""
    owner = Owner("Sam", available_time_today=240, preferences={})
    pet = Pet("Rex", "dog", 3)
    owner.add_pet(pet)
    first = _make_task(pet, name="First", duration=60, preferred_time_window=(540, 600))
    second = _make_task(pet, name="Second", duration=60, preferred_time_window=(600, 660))
    pet.add_task(first)
    pet.add_task(second)

    schedule = owner.scheduler.generate_schedule()

    assert first.scheduled_time == (540, 600)
    assert second.scheduled_time == (600, 660)
    assert schedule.conflicts == []


def test_recurring_clone_reschedulable_same_day():
    """Documents the mark_done TODO: the clone reappears in today's plan.

    The clone has no due date, so regenerating after completion re-schedules
    it the same day. This asserts current behavior — update it if/when
    due_date/planning_date lands.
    """
    owner = Owner("Sam", available_time_today=240, preferences={})
    pet = Pet("Rex", "dog", 3)
    owner.add_pet(pet)
    task = _make_task(pet, name="Walk", recurring=True, preferred_time_window=(540, 600))
    pet.add_task(task)

    first = owner.scheduler.generate_schedule()
    assert first.scheduled == [task]

    task.mark_done()
    second = owner.scheduler.generate_schedule()

    # The completed original is filtered out; its pending clone is scheduled.
    assert len(second.scheduled) == 1
    clone = second.scheduled[0]
    assert clone is not task
    assert clone.completed is False
    assert clone.name == "Walk"


def test_double_mark_done_creates_duplicate_clones():
    """Documents current behavior: re-completing a recurring task clones again.

    mark_done() is not idempotent — each call on a recurring task spawns a
    clone, so two calls leave two pending clones. Captured to observe, not
    (yet) fix.
    """
    pet = Pet("Rex", "dog", 3)
    task = _make_task(pet, recurring=True)
    pet.add_task(task)

    task.mark_done()
    task.mark_done()  # completing the already-completed original again

    assert task.completed is True
    assert len(pet.get_tasks()) == 3  # original + 2 clones
    assert len(pet.pending_tasks()) == 2


def test_zero_duration_task_always_placed():
    """A 0-min task fits any budget (0 <= remaining) and conflicts with nothing."""
    owner = Owner("Sam", available_time_today=0, preferences={})
    pet = Pet("Rex", "dog", 3)
    owner.add_pet(pet)
    zero = _make_task(pet, name="Zero", duration=0, preferred_time_window=(540, 600))
    normal = _make_task(pet, name="Normal", duration=30, preferred_time_window=(540, 600))
    pet.add_task(zero)
    pet.add_task(normal)

    schedule = owner.scheduler.generate_schedule()

    # Even with a 0-min budget the 0-min task is placed; the 30-min one defers.
    assert zero in schedule.scheduled
    assert zero.scheduled_time == (540, 540)
    assert normal in schedule.deferred
    # A zero-length [t, t) slot overlaps nothing, so no conflict is flagged.
    assert schedule.conflicts == []
