import csv
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "users.csv"
DB_PATH = BASE_DIR / "users.db"
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}")


def read_users(path):
    users, skipped = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip().lower()
            if not name:
                skipped.append(f"line {reader.line_num}: missing name")
            elif not EMAIL_RE.fullmatch(email):
                skipped.append(f"line {reader.line_num}: invalid email '{email}'")
            else:
                users.append((name, email))
    return users, skipped


def main():
    try:
        users, skipped = read_users(CSV_PATH)
    except OSError as exc:
        sys.exit(f"Could not read {CSV_PATH.name}: {exc}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)"
    )
    with conn:
        inserted = conn.executemany("INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)", users).rowcount
    rows = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
    conn.close()

    print(f"inserted: {inserted}  duplicates: {len(users) - inserted}  skipped: {len(skipped)}")
    for reason in skipped:
        print(f"  {reason}")

    print(f"\n{'ID':<4}{'Name':<20}Email")
    for user_id, name, email in rows:
        print(f"{user_id:<4}{name:<20}{email}")


if __name__ == "__main__":
    main()
