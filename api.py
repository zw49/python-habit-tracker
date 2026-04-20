import json
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from habits import HABITS, complete, load, streaks, uncomplete


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, body: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/habits":
            self._json(200, {"habits": HABITS})
            return
        if path == "/status":
            today = date.today()
            df = load()
            result = {}
            for h in HABITS:
                days = set(df.loc[df["completed"] == h, "date"])
                current, longest = streaks(days, today)
                result[h] = {
                    "completed_today": today in days,
                    "current_streak": current,
                    "longest_streak": longest,
                    "total": len(days),
                }
            self._json(200, result)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        parts = [p for p in path.split("/") if p]
        if len(parts) == 2 and parts[0] in ("complete", "uncomplete"):
            action, habit = parts
            if habit not in HABITS:
                self._json(400, {"error": f"unknown habit: {habit}"})
                return
            today = date.today()
            fn = complete if action == "complete" else uncomplete
            changed = fn(habit, today)
            self._json(
                200,
                {
                    "habit": habit,
                    "date": today.isoformat(),
                    "action": action,
                    "changed": changed,
                },
            )
            return
        self._json(404, {"error": "not found"})


def serve(port: int = 8000) -> None:
    print(f"API listening on 0.0.0.0:{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    serve()
