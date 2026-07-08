"""PawPal+ core domain model.

Skeleton only — see diagrams/uml.mmd. Scheduling logic is built incrementally.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(eq=False)
class Pet:
    """A pet that needs care and holds the tasks it needs.

    eq=False keeps identity-based equality (``is``): two distinct pets with the
    same name/species/age are different pets, so ``pet not in owner.pets`` and
    ``task.pet is pet`` behave by identity rather than by field values.
    """

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)  # Pet "1" --> "*" Task : needs

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, keeping the task's back-reference in sync.

        Reassigns task.pet to self so the Task "*" --> "1" Pet relationship
        always agrees with the Pet "1" --> "*" Task list, even if the task was
        built pointing at a different pet.
        """
        task.pet = self
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's own task list."""
        return self.tasks

    def pending_tasks(self) -> list[Task]:
        """Return this pet's not-yet-completed tasks."""
        return [task for task in self.tasks if not task.completed]

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's list if present; no-op otherwise."""
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass(eq=False)
class Task:
    """A single care task (walk, feed, meds, groom, enrichment).

    Holds a back-reference to the Pet it is for so the schedule can say
    which pet each task belongs to.

    eq=False keeps identity-based equality (``is``): two distinct tasks with the
    same field values (e.g. a "walk" for Rex and a "walk" for Milo) stay
    distinct, so collecting/deduping tasks in the scheduler never silently
    merges them. conflicts_with() is unaffected — it compares scheduled_time
    values directly, not task identity.
    """

    name: str
    type: str
    duration: int  # minutes
    priority: int
    preferred_time_window: tuple[int, int]  # (start_minute, end_minute)
    recurring: bool  # frequency: True = every day, False = one-off
    pet: Pet  # Task "*" --> "1" Pet : for
    completed: bool = False  # completion status
    # Where the scheduler actually placed this task, set by generate_schedule().
    # None until scheduled; preferred_time_window is only the input preference.
    scheduled_time: tuple[int, int] | None = None

    def conflicts_with(self, other: Task) -> bool:
        """Return True if this task's *scheduled* slot overlaps `other`'s.

        Compares scheduled_time (where each task actually lands), not
        preferred_time_window (a mere preference). Returns False if either task
        is still unscheduled — an unplaced task cannot conflict with anything.

        Slots are half-open intervals [start, end), so tasks that merely touch
        end-to-start (e.g. 540-600 and 600-660) do not conflict.
        """
        if self.scheduled_time is None or other.scheduled_time is None:
            return False
        start, end = self.scheduled_time
        other_start, other_end = other.scheduled_time
        return start < other_end and other_start < end

    def mark_done(self) -> None:
        """Mark this task completed; if recurring, queue its next occurrence.

        A recurring task represents a daily need, so completing today's instance
        spawns a fresh, un-completed copy on the same pet (scheduled_time cleared)
        ready for the next generate_schedule() run. One-off tasks just complete.
        Delegates to pet.add_task() so the new task's back-reference stays in sync.

        The completed original is kept as history — the UI is expected to filter
        with pending_tasks() so completed clones don't clutter the display.
        """
        self.completed = True
        if self.recurring and self.pet is not None:
            # TODO(recurring): due_date + planning_date. preferred_time_window is
            # time-of-day only, so the clone is due "some day" with no notion of
            # tomorrow. Because Scheduler.tasks filters on pending (not date), the
            # clone is immediately re-schedulable *today* — so once a "mark
            # complete" UI button exists and the schedule is regenerated, a
            # finished daily task would reappear in the same day's plan. Harmless
            # now (no such button wired up yet). Minimal fix when it is: add an
            # optional Task.due_date (None = any day), advance it by
            # timedelta(days=1) here, and filter Scheduler.tasks on a
            # Scheduler.planning_date (None = ignore dates, preserving today's
            # behavior).
            self.pet.add_task(replace(self, completed=False, scheduled_time=None))


class Owner:
    """The person using PawPal+. Owns pets and drives the scheduler."""

    def __init__(self, name: str, available_time_today: int, preferences: dict) -> None:
        """Create an owner with a daily time budget, preferences, and a scheduler."""
        self.name: str = name
        self.available_time_today: int = available_time_today  # minutes
        self.preferences: dict = preferences
        self.pets: list[Pet] = []  # Owner "1" --> "*" Pet : owns
        # Owner "1" --> "1" Scheduler : uses. The scheduler reads this owner's
        # pets and preferences directly, so there is one source of truth.
        self.scheduler: Scheduler = Scheduler(self)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner (idempotent)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Un-register a pet; its tasks leave with it (they live only in pet.tasks)."""
        if pet in self.pets:
            self.pets.remove(pet)

    def add_task(self, task: Task) -> None:
        """Route a task onto its pet, ensuring that pet is owned.

        The task carries its own pet reference (Task "*" --> "1" Pet), so we
        delegate storage to that pet. We also register the pet if it is not
        already owned — otherwise the task would be invisible to the scheduler,
        which only sees tasks reachable through owner.pets.
        """
        self.add_pet(task.pet)
        task.pet.add_task(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task without removing its pet, by delegating to the pet."""
        task.pet.remove_task(task)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def tasks_for_pet(self, name: str) -> list[Task]:
        """Return every task belonging to the pet(s) with this name.

        Matches on name rather than identity so callers (e.g. a Streamlit
        dropdown) can filter by the label the owner sees. Returns tasks across
        all matching pets, empty if none match.
        """
        return [task for pet in self.pets if pet.name == name for task in pet.tasks]

    def set_constraint(self, key: str, value: object) -> None:
        """Update a scheduling constraint.

        The dedicated time budget lives on its own attribute; everything else
        goes into preferences, which the scheduler reads as its constraints
        (the same dict object, so no separate copy to keep in sync).
        """
        if key == "available_time_today":
            self.available_time_today = int(value)
        else:
            self.preferences[key] = value


@dataclass
class Schedule:
    """Result of Scheduler.generate_schedule().

    scheduled: tasks that were placed, in placement (priority) order — each has
               scheduled_time set.
    deferred:  tasks that did not fit the time budget — scheduled_time is None.
    conflicts: pairs of scheduled tasks whose slots overlap. Flagged, not
               resolved — conflict resolution is a separate concern for now.
    """

    scheduled: list[Task]
    deferred: list[Task]
    conflicts: list[tuple[Task, Task]]


class Scheduler:
    """Builds and explains a daily schedule from all pets' tasks."""

    def __init__(self, owner: Owner) -> None:
        """Bind the scheduler to its owner, sharing the owner's preferences as constraints."""
        # Owner "1" --> "1" Scheduler : uses (back-reference).
        self.owner: Owner = owner
        # One constraints bag, shared with the owner: set_constraint() writes
        # to owner.preferences and the scheduler reads the same object.
        self.constraints: dict = owner.preferences
        # Populated by generate_schedule(); read by explain_reasoning().
        self.last_schedule: Schedule | None = None
        self._reasoning: list[str] = []

    @property
    def tasks(self) -> list[Task]:
        """Pending tasks across all of the owner's pets (single source of truth)."""
        # Scheduler "1" o-- "*" Task : schedules. Derived from the owner's pets
        # so there is a single source of truth (no separately-populated list).
        # Uses pending_tasks() so already-completed tasks are not re-scheduled.
        return [task for pet in self.owner.pets for task in pet.pending_tasks()]

    def generate_schedule(self) -> Schedule:
        """Build today's schedule greedily, highest priority first.

        Walks sort_by_priority() and, for each task, tries to place it at the
        start of its preferred_time_window. A task is placed only if its full
        duration still fits within owner.available_time_today (cumulative work
        minutes) — otherwise it is deferred with scheduled_time left as None. We
        never truncate a task to make it fit.

        Because start times come from preferred windows while the budget tracks
        cumulative duration, two placed tasks can share a wall-clock slot; those
        overlaps are surfaced via detect_conflicts() and reported on the result,
        not silently un-scheduled.
        """
        budget = self.owner.available_time_today
        ordered = self.sort_by_priority()
        top_priority = ordered[0].priority if ordered else None

        scheduled: list[Task] = []
        deferred: list[Task] = []
        reasoning: list[str] = []
        used = 0  # cumulative minutes committed so far

        for task in ordered:
            # Fresh placement each run: clear any slot from a previous call.
            task.scheduled_time = None
            remaining = budget - used
            if task.duration <= remaining:
                start = task.preferred_time_window[0]
                task.scheduled_time = (start, start + task.duration)
                used += task.duration
                scheduled.append(task)
                reasoning.append(self._why_scheduled(task, ordered, top_priority))
            else:
                deferred.append(task)
                reasoning.append(self._why_deferred(task, remaining))

        conflicts = self.detect_conflicts()

        self._reasoning = reasoning
        self.last_schedule = Schedule(scheduled, deferred, conflicts)
        return self.last_schedule

    def explain_reasoning(self) -> str:
        """Return a natural-language explanation of the last schedule.

        Reads the most recent generate_schedule() result without recomputing —
        it's a pure read. Narrates each task's fate (scheduled or deferred) and
        the reason, followed by any flagged conflicts. Returns a clear notice if
        no schedule has been generated yet.
        """
        if self.last_schedule is None:
            return "No schedule generated yet — call generate_schedule() first."

        schedule = self.last_schedule
        budget = self.owner.available_time_today
        used = sum(task.duration for task in schedule.scheduled)

        lines = [
            f"Daily schedule for {self.owner.name} "
            f"— {used}/{budget} min committed, "
            f"{len(schedule.scheduled)} scheduled, {len(schedule.deferred)} deferred, "
            f"{len(schedule.conflicts)} conflict(s):"
        ]
        lines.extend(f"  {note}" for note in self._reasoning)

        if schedule.conflicts:
            lines.append("")
            lines.append("Conflicts flagged (overlapping slots — not resolved):")
            for first, second in schedule.conflicts:
                first_slot = self._format_slot(first)
                second_slot = self._format_slot(second)
                lines.append(
                    f"  - {first.name} ({first_slot}) overlaps "
                    f"{second.name} ({second_slot})"
                )

        return "\n".join(lines)

    def sort_by_priority(self) -> list[Task]:
        """Return pending tasks ordered most-urgent first.

        Primary key: priority, descending (higher value = more urgent).
        Tiebreak: earlier preferred_time_window start goes first, so tasks of
        equal priority are ordered by when the owner would like them to happen
        — something explain_reasoning() can point to concretely.
        """
        return sorted(
            self.tasks,
            key=lambda task: (-task.priority, task.preferred_time_window[0]),
        )

    def sort_by_time(self) -> list[Task]:
        """Return pending tasks ordered by preferred start time, earliest first.

        Primary key: preferred_time_window start, ascending (chronological view
        of the day). Tiebreak: higher priority first, so tasks that want the same
        slot are ordered by urgency — the mirror image of sort_by_priority()'s keys.
        """
        return sorted(
            self.tasks,
            key=lambda task: (task.preferred_time_window[0], -task.priority),
        )

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Return every pair of tasks whose scheduled slots overlap.

        Delegates the overlap test to Task.conflicts_with(), which compares
        scheduled_time. Tasks with no scheduled_time never conflict, so this is
        empty until generate_schedule() has placed tasks. Each unordered pair is
        reported once, as an (earlier-in-list, later-in-list) tuple.
        """
        tasks = self.tasks
        conflicts: list[tuple[Task, Task]] = []
        for i, task in enumerate(tasks):
            for other in tasks[i + 1:]:
                if task.conflicts_with(other):
                    conflicts.append((task, other))
        return conflicts

    # --- reasoning / formatting helpers -----------------------------------

    def _why_scheduled(
        self, task: Task, ordered: list[Task], top_priority: int | None
    ) -> str:
        """One-line justification for a task that got placed."""
        start_str = self._format_time(task.scheduled_time[0])
        base = (
            f"highest priority ({task.priority})"
            if task.priority == top_priority
            else f"priority {task.priority}"
        )
        clause = ""
        peers = [t for t in ordered if t is not task and t.priority == task.priority]
        if peers:
            my_start = task.preferred_time_window[0]
            later = [t for t in peers if t.preferred_time_window[0] > my_start]
            earlier = [t for t in peers if t.preferred_time_window[0] < my_start]
            if later:
                clause = f", tied with {self._names(later)} but earlier preferred window"
            elif earlier:
                clause = (
                    f", tied with {self._names(earlier)} "
                    "but placed after (later preferred window)"
                )
            else:
                clause = (
                    f", tied with {self._names(peers)} "
                    "(same window; kept insertion order)"
                )
        return f"{task.name} scheduled at {start_str} — {base}{clause}."

    def _why_deferred(self, task: Task, remaining: int) -> str:
        """One-line justification for a task that did not fit the budget."""
        return (
            f"{task.name} deferred — needs {task.duration} min but only "
            f"{remaining} min left in today's {self.owner.available_time_today}-min budget."
        )

    def _format_slot(self, task: Task) -> str:
        """Render a scheduled task's slot as e.g. '9:00am-9:30am'."""
        start, end = task.scheduled_time
        return f"{self._format_time(start)}-{self._format_time(end)}"

    @staticmethod
    def _names(tasks: list[Task]) -> str:
        """Join task names into a comma-separated string."""
        return ", ".join(task.name for task in tasks)

    @staticmethod
    def _format_time(minutes: int) -> str:
        """Convert minutes-since-midnight to a 12-hour clock string."""
        hour24, minute = divmod(minutes, 60)
        suffix = "am" if hour24 % 24 < 12 else "pm"
        hour12 = hour24 % 12 or 12
        return f"{hour12}:{minute:02d}{suffix}"
