import streamlit as st

st.set_page_config(page_title="Habit Tracker", layout="centered")

pages = [
    st.Page(
        "sections/habits.py",
        title="Habits",
        icon=":material/local_fire_department:",
        default=True,
    ),
    st.Page(
        "sections/tasks.py",
        title="Tasks",
        icon=":material/checklist:",
    ),
]
st.navigation(pages, position="top").run()
