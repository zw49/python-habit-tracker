from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

DATA = Path(__file__).parent / "data.csv"
HABITS = ["4runner"]
NTFY_COMPLETION_TOPIC = "4runner_completion_notification"
NTFY_INCOMPLETION_TOPIC = "4runner_incompletion_notification"


def send_notification(message: str, topic: str) -> None:
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode(encoding="utf-8"),
    )


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def save(df: pd.DataFrame) -> None:
    df.to_csv(DATA, index=False)


def complete(habit: str, day: date) -> bool:
    df = load()
    mask = (df["completed"] == habit) & (df["date"] == day)
    if mask.any():
        return False
    new_row = pd.DataFrame([{"completed": habit, "date": day}])
    save(pd.concat([df, new_row], ignore_index=True))
    send_notification(
        f"Z completed {habit} on {day.isoformat()}",
        topic=NTFY_COMPLETION_TOPIC,
    )
    return True


def uncomplete(habit: str, day: date) -> bool:
    df = load()
    mask = (df["completed"] == habit) & (df["date"] == day)
    if not mask.any():
        return False
    save(df[~mask].reset_index(drop=True))
    send_notification(
        f"Z marked {habit} as incomplete on {day.isoformat()}",
        topic=NTFY_INCOMPLETION_TOPIC,
    )
    return True


def streaks(days: set[date], today: date) -> tuple[int, int]:
    current = 0
    d = today
    while d in days:
        current += 1
        d -= timedelta(days=1)
    longest = 0
    run = 0
    prev = None
    for dd in sorted(days):
        run = run + 1 if prev is not None and (dd - prev).days == 1 else 1
        longest = max(longest, run)
        prev = dd
    return current, longest
