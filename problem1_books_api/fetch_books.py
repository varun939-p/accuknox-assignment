import sqlite3
import sys
from pathlib import Path

import requests

DB_PATH = Path(__file__).resolve().parent / "books.db"


def fetch_books(query="computer security", limit=15):
    response = requests.get(
        "https://openlibrary.org/search.json",
        params={"q": query, "limit": limit, "fields": "title,author_name,first_publish_year"},
        headers={"User-Agent": "accuknox-assignment/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    books = []
    for doc in response.json().get("docs", []):
        title = (doc.get("title") or "").strip()
        if not title:
            continue
        author = ", ".join(doc.get("author_name", [])[:2]) or "Unknown"
        books.append((title, author, doc.get("first_publish_year")))
    return books


def save_books(books):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            publication_year INTEGER,
            UNIQUE(title, author)
        )
    """)
    with conn:
        inserted = conn.executemany(
            "INSERT OR IGNORE INTO books (title, author, publication_year) VALUES (?, ?, ?)", books
        ).rowcount
    rows = conn.execute(
        "SELECT id, title, author, publication_year FROM books ORDER BY publication_year DESC, title"
    ).fetchall()
    conn.close()
    return inserted, rows


if __name__ == "__main__":
    try:
        books = fetch_books()
    except requests.RequestException as exc:
        sys.exit(f"Failed to fetch books: {exc}")

    inserted, rows = save_books(books)
    print(f"fetched {len(books)}, inserted {inserted}, duplicates {len(books) - inserted}\n")
    print(f"{'ID':<4}{'Title':<47}{'Author':<32}Year")
    for book_id, title, author, year in rows:
        print(f"{book_id:<4}{title[:45]:<47}{author[:30]:<32}{year or '-'}")
