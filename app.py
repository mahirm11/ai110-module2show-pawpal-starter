import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ app.

This UI is wired to the real project logic: it uses the **`Owner`, `Pet`, `Task`, and
`Scheduler` classes** from `pawpal_system.py` to add tasks, build a daily schedule, and
explain the plan.

Use it as your interactive demo of the scheduling system.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Map the UI's priority labels onto the integer priorities Task expects.
PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}


def _fmt_time(minutes: int) -> str:
    """Render minutes-since-midnight as a 12-hour clock string (e.g. 9:00am)."""
    hour24, minute = divmod(minutes, 60)
    suffix = "am" if hour24 % 24 < 12 else "pm"
    return f"{hour24 % 12 or 12}:{minute:02d}{suffix}"


st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
available_time = st.number_input(
    "Available time today (minutes)", min_value=1, max_value=1440, value=120
)

# Create the Owner exactly once, with no pets. Pets are added explicitly via the
# "Add pet" form below, then reused across reruns from session state.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        owner_name, available_time_today=int(available_time), preferences={}
    )

owner = st.session_state.owner
# The owner is only built once, but keep the time-budget control live each rerun
# so changing it actually affects the next schedule.
owner.available_time_today = int(available_time)

st.markdown("### Pets")
st.caption("Add one or more pets. Tasks are assigned to a specific pet.")

pcol1, pcol2 = st.columns(2)
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    owner.add_pet(Pet(pet_name, species, age=0))

if owner.pets:
    st.write("Current pets:")
    for i, pet in enumerate(owner.pets):
        info_col, del_col = st.columns([4, 1])
        info_col.write(f"{pet.name} ({pet.species})")
        if del_col.button("Delete", key=f"del_pet_{i}"):
            owner.remove_pet(pet)
            owner.scheduler.last_schedule = None  # invalidate stale snapshot
            st.rerun()
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add a few tasks. These feed directly into your scheduler.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    category = st.selectbox("Category", ["walk", "feed", "meds", "groom", "enrichment"])
with col3:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

start_time = st.time_input("Preferred start time", value=datetime.time(9, 0))

if owner.pets:
    selected_index = st.selectbox(
        "For pet",
        options=range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    if st.button("Add task"):
        selected_pet = owner.pets[selected_index]  # look up fresh at construction time
        start_minutes = start_time.hour * 60 + start_time.minute
        window = (start_minutes, start_minutes + int(duration))
        task = Task(
            name=task_title,
            type=category,
            duration=int(duration),
            priority=PRIORITY_MAP[priority],
            preferred_time_window=window,
            recurring=False,
            pet=selected_pet,
        )
        owner.add_task(task)  # routes through the owner to the right pet
else:
    st.info("Add a pet before creating tasks.")

pending = [task for pet in owner.pets for task in pet.pending_tasks()]
if pending:
    st.write("Current tasks:")

    view_col, filter_col = st.columns(2)
    with view_col:
        view_mode = st.radio(
            "View",
            options=["By priority", "By time"],
            horizontal=True,
            help="By priority = most urgent first. By time = earliest preferred start first.",
        )
    with filter_col:
        # dict.fromkeys dedupes repeated pet names while keeping display order.
        pet_names = list(dict.fromkeys(pet.name for pet in owner.pets))
        pet_filter = st.selectbox("Filter by pet", options=["All pets"] + pet_names)

    # Order via the scheduler's own sort methods so the UI showcases them.
    if view_mode == "By time":
        ordered = owner.scheduler.sort_by_time()
    else:
        ordered = owner.scheduler.sort_by_priority()

    # Filter by pet using owner.tasks_for_pet(); keep the scheduler's ordering.
    if pet_filter != "All pets":
        pet_tasks = set(owner.tasks_for_pet(pet_filter))
        ordered = [task for task in ordered if task in pet_tasks]

    if ordered:
        for i, task in enumerate(ordered):
            info_col, del_col = st.columns([4, 1])
            window = (
                f"{_fmt_time(task.preferred_time_window[0])}"
                f"–{_fmt_time(task.preferred_time_window[1])}"
            )
            info_col.write(
                f"{task.name} ({task.pet.name}) · {task.duration} min · "
                f"priority {task.priority} · {window}"
            )
            if del_col.button("Delete", key=f"del_task_{i}"):
                owner.remove_task(task)
                owner.scheduler.last_schedule = None  # invalidate stale snapshot
                st.rerun()
    else:
        st.info(f"No tasks for {pet_filter}.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs your scheduler and explains the resulting plan.")

if st.button("Generate schedule"):
    schedule = owner.scheduler.generate_schedule()

    if schedule.conflicts:
        lines = [f"⚠️ **{len(schedule.conflicts)} scheduling conflict(s) detected:**", ""]
        for first, second in schedule.conflicts:
            first_slot = f"{_fmt_time(first.scheduled_time[0])}–{_fmt_time(first.scheduled_time[1])}"
            second_slot = f"{_fmt_time(second.scheduled_time[0])}–{_fmt_time(second.scheduled_time[1])}"
            lines.append(
                f"- **{first.name}** ({first_slot}) overlaps "
                f"**{second.name}** ({second_slot})"
            )
        st.warning("\n".join(lines))
    else:
        st.success("✅ Clean schedule — no conflicting time slots.")

    # Full reasoning underneath either way.
    st.text(owner.scheduler.explain_reasoning())
