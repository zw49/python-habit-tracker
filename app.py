from datetime import date, timedelta

import pandas as pd
import streamlit as st

from habits import (
    HABITS,
    NTFY_COMPLETION_TOPIC,
    complete,
    load,
    streaks,
    uncomplete,
)


@st.dialog("Complete a habit")
def complete_dialog() -> None:
    today = date.today()
    df = load()
    choice = st.selectbox("Habit", HABITS)
    already = ((df["completed"] == choice) & (df["date"] == today)).any()
    if already:
        st.info(f"{choice} already completed today.")
        if st.button("Mark incomplete", type="secondary"):
            uncomplete(choice, today)
            st.rerun()
    else:
        if st.button("Complete for today", type="primary"):
            complete(choice, today)
            st.rerun()


st.set_page_config(page_title="Habit Tracker", layout="centered")

today = date.today()
df = load()


def metric_card(label: str, value: object, color: str = "inherit") -> str:
    return f"""
    <div style='text-align:center;'>
      <div style='font-size:0.875rem; color:rgba(128,128,128,0.9);'>{label}</div>
      <div style='font-size:2.25rem; font-weight:600; line-height:1.2; color:{color};'>{value}</div>
    </div>
    """


def render_streak(habit: str, habit_days: set[date], current: int) -> None:
    if len(HABITS) > 1:
        st.markdown(
            f"<div style='text-align:center;'><b>{habit}</b></div>",
            unsafe_allow_html=True,
        )
    strip_days = 5
    marks = []
    for i in range(strip_days - 1, -1, -1):
        d = today - timedelta(days=i)
        if d in habit_days:
            in_streak = (today - d).days < current
            marks.append("🔥" if in_streak else "✅")
        else:
            marks.append("<span style='opacity:0.25'>•</span>")
    strip = "&nbsp;".join(marks)
    color = "#ff6a00" if current > 0 else "inherit"
    st.markdown(
        metric_card("Current streak", f"🔥 {current}", color)
        + f"<div style='text-align:center; font-size:16px; letter-spacing:1px; margin-top:4px;'>{strip}</div>",
        unsafe_allow_html=True,
    )


st.title("Habit Tracker")
st.caption(f"Today: {today.isoformat()}")
btn_col, info_col, _ = st.columns([2, 2, 4.7], gap="xxsmall")
with btn_col:
    if st.button("Complete a habit", type="primary"):
        complete_dialog()
with info_col:
    with st.popover("Notification topic"):
        st.markdown(
            "Subscribe to this topic on [ntfy.sh](https://ntfy.sh) to receive "
            "a notification on every completion:"
        )
        st.code(NTFY_COMPLETION_TOPIC, language=None)

with st.expander("Stats"):
    if df.empty:
        st.write("No data yet.")
    else:
        for habit in HABITS:
            habit_days = set(df.loc[df["completed"] == habit, "date"])
            current, longest = streaks(habit_days, today)
            c1, c2, c3 = st.columns(3)
            c1.markdown(metric_card("Total", len(habit_days)), unsafe_allow_html=True)
            with c2:
                render_streak(habit, habit_days, current)
            c3.markdown(metric_card("Longest streak", longest), unsafe_allow_html=True)

        st.divider()

        chart_df = (
            df.assign(count=1)
            .groupby(["date", "completed"])["count"]
            .sum()
            .unstack(fill_value=0)
            .sort_index()
            .cumsum()
        )
        chart_df.index = pd.to_datetime(chart_df.index)
        st.caption("Cumulative completions")
        st.line_chart(chart_df)

st.subheader("History")
if df.empty:
    st.write("No completions yet.")
else:
    full_range = pd.date_range(start=df["date"].min(), end=today, freq="D").date
    pivot = (
        df.assign(done="✅")
        .pivot_table(
            index="date",
            columns="completed",
            values="done",
            aggfunc="first",
            fill_value="",
        )
        .reindex(full_range, fill_value="")
        .sort_index(ascending=False)
    )
    st.dataframe(pivot, use_container_width=True)
