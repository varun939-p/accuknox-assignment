import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import requests

API_URL = "https://openlibrary.org/search.json"
DB_PATH = Path(__file__).resolve().parent / "books.db"
HEADERS = {"User-Agent": "accuknox-assignment-books/1.0"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publication_year INTEGER,
    UNIQUE(title, author)
)
"""


def fetch_docs(query: str = "computer security", limit: int = 15) -> list:
    params = {"q": query, "limit": limit, "fields": "title,author_name,first_publish_year"}
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=20)
    response.raise_for_status()
    payload = response.json()
    docs = payload.get("docs") if isinstance(payload, dict) else None
    return docs if isinstance(docs, list) else []


def parse_book(doc: dict) -> tuple[str, str, int | None] | None:
    title = doc.get("title")
    if not isinstance(title, str) or not title.strip():
        return None

    raw_authors = doc.get("author_name")
    if not isinstance(raw_authors, list):
        raw_authors = []
    authors = [a.strip() for a in raw_authors if isinstance(a, str) and a.strip()]
    author = ", ".join(authors[:2]) or "Unknown"

    year = doc.get("first_publish_year")
    if not isinstance(year, int):
        year = None

    return title.strip(), author, year


def truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 3] + "..."


def print_table(rows: list[tuple]) -> None:
    print(f"{'ID':>3}  {'Title':<45}  {'Author':<30}  {'Year':>4}")
    print(f"{'-' * 3}  {'-' * 45}  {'-' * 30}  {'-' * 4}")
    for book_id, title, author, year in rows:
        print(f"{book_id:>3}  {truncate(title, 45):<45}  {truncate(author, 30):<30}  {year or '-':>4}")


def main() -> int:
    try:
        docs = fetch_docs()
    except requests.RequestException as exc:
        print(f"error: could not fetch books from Open Library: {exc}", file=sys.stderr)
        return 1

    parsed = [parse_book(doc) for doc in docs if isinstance(doc, dict)]
    books = [book for book in parsed if book is not None]
    skipped = len(docs) - len(books)

    try:
        with closing(sqlite3.connect(DB_PATH)) as conn:
            with conn:
                conn.execute(SCHEMA)
                inserted = conn.executemany(
                    "INSERT OR IGNORE INTO books (title, author, publication_year) VALUES (?, ?, ?)",
                    books,
                ).rowcount
            rows = conn.execute(
                "SELECT id, title, author, publication_year FROM books "
                "ORDER BY publication_year DESC, title ASC"
            ).fetchall()
    except sqlite3.Error as exc:
        print(f"error: database operation failed: {exc}", file=sys.stderr)
        return 1

    print(f"fetched {len(docs)}, inserted {inserted}, duplicates {len(books) - inserted}, skipped {skipped}")
    print(f"{len(rows)} books in {DB_PATH.name}\n")
    print_table(rows)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
