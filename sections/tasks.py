import uuid
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from habits import send_notification

TASKS_CSV = Path(__file__).parent.parent / "tasks.csv"
COLUMNS = ["id", "task", "assigned_by", "due_date", "date_added", "done"]
NTFY_TASK_ADDED_TOPIC = "z_got_assigned_a_new_task"
NTFY_TASK_COMPLETED_TOPIC = "z_completed_a_task"


def load() -> pd.DataFrame:
    if not TASKS_CSV.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(TASKS_CSV)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = False if col == "done" else ""
    df["done"] = df["done"].fillna(False).astype(bool)
    df["assigned_by"] = df["assigned_by"].fillna("").astype(str)
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce").dt.date
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce").dt.date
    return df[COLUMNS]


def save(df: pd.DataFrame) -> None:
    df.to_csv(TASKS_CSV, index=False)


def add_task(name: str, assigned_by: str, due_date: date | None) -> None:
    df = load()
    new = pd.DataFrame(
        [
            {
                "id": str(uuid.uuid4()),
                "task": name,
                "assigned_by": assigned_by,
                "due_date": due_date,
                "date_added": date.today(),
                "done": False,
            }
        ]
    )
    save(pd.concat([df, new], ignore_index=True))
    msg = f"New task: {name}"
    if assigned_by:
        msg += f" (from {assigned_by})"
    if due_date:
        msg += f" — due {due_date.isoformat()}"
    send_notification(msg, topic=NTFY_TASK_ADDED_TOPIC)


def set_done(task_id: str, done: bool) -> None:
    df = load()
    df.loc[df["id"] == task_id, "done"] = done
    save(df)


def remove_task(task_id: str) -> None:
    df = load()
    save(df[df["id"] != task_id].reset_index(drop=True))


def clear_completed() -> None:
    df = load()
    save(df[~df["done"]].reset_index(drop=True))


st.title("Tasks")

with st.popover("Notification topics"):
    st.markdown("Subscribe to these topics on [ntfy.sh](https://ntfy.sh):")
    st.markdown("**New task assigned**")
    st.code(NTFY_TASK_ADDED_TOPIC, language=None)
    st.markdown("**Task completed**")
    st.code(NTFY_TASK_COMPLETED_TOPIC, language=None)

with st.expander("Add a task"):
    with st.form("add_task", clear_on_submit=True, border=False):
        new_task = st.text_input("Task")
        assigned_by = st.text_input("Assigned by")
        due_date = st.date_input("Due date (optional)", value=None)
        if st.form_submit_button("Add") and new_task.strip():
            add_task(new_task.strip(), assigned_by.strip(), due_date)
            st.rerun()

df = load()

if df.empty:
    st.caption("No tasks yet.")
else:
    display_df = df[["done", "task", "assigned_by", "due_date", "date_added"]].copy()
    edited = st.data_editor(
        display_df,
        column_config={
            "done": st.column_config.CheckboxColumn("Done", width=10),
            "task": st.column_config.TextColumn("Task"),
            "assigned_by": st.column_config.TextColumn("Assigned by"),
            "due_date": st.column_config.DateColumn("Due date"),
            "date_added": st.column_config.DateColumn("Added"),
        },
        disabled=["task", "assigned_by", "due_date", "date_added"],
        num_rows="fixed",
        hide_index=True,
        use_container_width=True,
        key="task_editor",
    )

    if not display_df["done"].equals(edited["done"]):
        changed = display_df["done"] != edited["done"]
        for i in display_df.index[changed]:
            new_done = bool(edited.loc[i, "done"])
            set_done(df.loc[i, "id"], new_done)
            if new_done:
                send_notification(
                    f"Z completed task: {df.loc[i, 'task']}",
                    topic=NTFY_TASK_COMPLETED_TOPIC,
                )
        st.rerun()

    if df["done"].any():
        if st.button("Clear completed"):
            clear_completed()
            st.rerun()
