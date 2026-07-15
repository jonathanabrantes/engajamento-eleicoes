import csv
from datetime import datetime, timezone
from pathlib import Path

CSV_PATH = Path(__file__).parent / "data" / "followers.csv"
FIELDS = ("timestamp", "username", "followers", "delta")


def init_csv():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def read_all() -> list[dict]:
    init_csv()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return [
            {
                "timestamp": row["timestamp"],
                "username": row["username"],
                "followers": int(row["followers"]),
                "delta": int(row["delta"]),
            }
            for row in csv.DictReader(f)
            if row.get("timestamp") and row.get("username")
        ]


def get_last_snapshot(username: str) -> dict | None:
    rows = [r for r in read_all() if r["username"] == username]
    return rows[-1] if rows else None


def append_snapshot(username: str, followers: int, delta: int, ts: str | None = None) -> str:
    ts = ts or datetime.now(timezone.utc).isoformat()
    init_csv()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(
            {
                "timestamp": ts,
                "username": username,
                "followers": followers,
                "delta": delta,
            }
        )
    return ts
