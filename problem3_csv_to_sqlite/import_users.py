import csv
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "users.csv"
DB_PATH = BASE_DIR / "users.db"

EMAIL_RE = re.compile(r"[a-z0-9][a-z0-9._%+-]*@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}")
FORMULA_PREFIXES = ("=", "+", "-", "@")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
)
"""


def validate(name: str, email: str) -> str | None:
    if not name:
        return "missing name"
    if name.startswith(FORMULA_PREFIXES):
        return "name starts with a formula character"
    if not EMAIL_RE.fullmatch(email):
        return "invalid email"
    return None


def read_users(path: Path) -> tuple[list[tuple[str, str]], list[tuple[int, str]]]:
    valid, rejected = [], []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = {"name", "email"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} is missing column(s): {', '.join(sorted(missing))}")

        for row in reader:
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip().lower()
            reason = validate(name, email)
            if reason:
                rejected.append((reader.line_num, reason))
            else:
                valid.append((name, email))
    return valid, rejected


def main():
    try:
        users, rejected = read_users(CSV_PATH)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"Failed to read {CSV_PATH.name}: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with conn:
                conn.execute(SCHEMA)
                inserted = conn.executemany(
                    "INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)", users
                ).rowcount
            rows = conn.execute("SELECT id, name, email FROM users ORDER BY id").fetchall()
    except sqlite3.Error as exc:
        print(f"SQLite error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"inserted: {inserted}  duplicates: {len(users) - inserted}  skipped_invalid: {len(rejected)}")
    for line, reason in rejected:
        print(f"  line {line}: {reason}")

    print(f"\n{len(rows)} users in {DB_PATH.name}\n")
    print(f"{'ID':>3}  {'Name':<20}  Email")
    print(f"{'-' * 3}  {'-' * 20}  {'-' * 32}")
    for user_id, name, email in rows:
        print(f"{user_id:>3}  {name[:20]:<20}  {email}")


if __name__ == "__main__":
    main()
