import streamlit as st

from pawpal_system import Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant — add pets, give them care tasks, and build a daily plan.")

# --- State: one Owner persists in the session; everything hangs off it ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Owner ---
st.subheader("Owner")
c1, c2 = st.columns(2)
with c1:
    owner.name = st.text_input("Owner name", value=owner.name)
with c2:
    owner.phone = st.text_input("Phone", value=owner.phone)

st.divider()

# --- Pets ---
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    p1, p2, p3 = st.columns(3)
    with p1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with p2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with p3:
        breed = st.text_input("Breed", value="Corgi")
    if st.form_submit_button("Add pet") and pet_name.strip():
        owner.add_pet(pet_name.strip(), species, breed.strip())

if not owner.pets:
    st.info("No pets yet. Add one above.")

# --- Tasks (per pet) ---
if owner.pets:
    st.subheader("Care Tasks")
    selected_name = st.selectbox("Add a task for", [p.name for p in owner.pets])
    selected_pet = owner.get_pet(selected_name)

    with st.form("add_task", clear_on_submit=True):
        t1, t2, t3 = st.columns(3)
        with t1:
            description = st.text_input("Task", value="Morning walk")
        with t2:
            time = st.text_input("Time (HH:MM)", value="08:00")
        with t3:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1)
        if st.form_submit_button("Add task") and description.strip() and selected_pet:
            selected_pet.add_task(description.strip(), time.strip(), frequency)

    # Each pet's tasks, ordered by time via the Scheduler, with a checkbox
    # that drives completion status.
    for pet in owner.pets:
        st.markdown(f"**{pet}**")
        if not pet.tasks:
            st.caption("No tasks yet.")
        for task in scheduler.sort_by_time(pet.tasks):
            task.completed = st.checkbox(
                f"{task.time} — {task.description} ({task.frequency})",
                value=task.completed,
                key=f"{pet.name}-{id(task)}",
            )

    # Surface any time clashes the Scheduler detects across all pets.
    warning = scheduler.conflict_warning()
    if warning:
        st.warning(warning)

st.divider()

# --- Schedule (the Scheduler brain) ---
st.subheader("Daily Plan")
st.caption("The Scheduler gathers every pet's pending tasks and orders them by time.")

if st.button("Generate schedule", type="primary"):
    schedule = scheduler.daily_schedule()
    if not schedule:
        st.success("All caught up — no pending tasks! 🎉")
    else:
        # Conflict warnings first, so clashes are obvious before reading the plan.
        if scheduler.has_conflicts():
            st.warning(scheduler.conflict_warning())
            with st.expander("See conflicting tasks"):
                st.text(scheduler.conflict_report())
        else:
            st.success("No scheduling conflicts — the day is clear. ✅")

        # Quick counts of pending vs. completed, using the Scheduler filters.
        pending = scheduler.pending_tasks()
        done = scheduler.completed_tasks()
        m1, m2 = st.columns(2)
        m1.metric("Pending", len(pending))
        m2.metric("Completed", len(done))

        st.markdown("### Ordered plan")
        st.table(
            [
                {"Time": task.time, "Pet": pet.name, "Task": task.description, "Frequency": task.frequency}
                for pet, task in schedule
            ]
        )
        nxt = scheduler.next_task()
        if nxt:
            pet, task = nxt
            st.info(f"⏭️ Next up: **{task.description}** for **{pet.name}** at **{task.time}**")
