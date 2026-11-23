# accuknox-assignment

Submission for the AI Security Engineer Trainee role at AccuKnox.

## Where each requirement lives

| Requirement | Location |
|---|---|
| Problem Statement 1, Q1: fetch books (JSON) from a REST API, store them in SQLite, display them | [problem1_books_api/fetch_books.py](problem1_books_api/fetch_books.py) |
| Problem Statement 1, Q2: fetch student scores from an API, calculate the average, plot a bar chart | [problem2_student_scores/](problem2_student_scores/): [mock_scores_api.py](problem2_student_scores/mock_scores_api.py), [scores_chart.py](problem2_student_scores/scores_chart.py), [student_scores_chart.png](problem2_student_scores/student_scores_chart.png) |
| Problem Statement 1, Q3: read users (name, email) from a CSV file and insert them into SQLite | [problem3_csv_to_sqlite/](problem3_csv_to_sqlite/): [users.csv](problem3_csv_to_sqlite/users.csv), [import_users.py](problem3_csv_to_sqlite/import_users.py) |
| Problem Statement 1, Q4: link to my most complex Python code | [answers/problem1_code_links.md](answers/problem1_code_links.md#q4-most-complex-python-code) |
| Problem Statement 1, Q5: link to my most complex database code | [answers/problem1_code_links.md](answers/problem1_code_links.md#q5-most-complex-database-code) |
| Assignment 2, Q1: self-rating on LLM, Deep Learning, AI and ML | [answers/assignment2_ai_questions.md](answers/assignment2_ai_questions.md#1-self-rating-llm-deep-learning-ai-ml) |
| Assignment 2, Q2: key architectural components of an LLM-based chatbot | [answers/assignment2_ai_questions.md](answers/assignment2_ai_questions.md#2-key-architectural-components-of-an-llm-based-chatbot) |
| Assignment 2, Q3: vector databases and which one I would choose | [answers/assignment2_ai_questions.md](answers/assignment2_ai_questions.md#3-vector-databases-and-which-one-i-would-choose) |
| Assignment 3: proudest project and why it was hard | [answers/assignment3_project.md](answers/assignment3_project.md) |

## Setup

Python 3.10 or newer (developed on 3.12).

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Every script resolves its files relative to its own folder, so the commands below work from the repo root or from inside each folder. The SQLite files (`books.db`, `users.db`) are created at runtime and are gitignored.

## Problem 1 - Books API to SQLite

```bash
python problem1_books_api/fetch_books.py
```

Queries the Open Library Search API for "computer security" (15 results), stores title, author and publication year in `problem1_books_api/books.db`, then prints every stored row as an aligned table. Inserts use `INSERT OR IGNORE` against `UNIQUE(title, author)`, so a second run reports `inserted 0`. Network errors, timeouts and non-JSON responses exit with a one-line error and status 1.

## Problem 2 - Student scores chart

The scores come from a small local API, so start it first and leave it running:

```bash
# terminal 1
python problem2_student_scores/mock_scores_api.py      # serves http://127.0.0.1:8000/api/scores

# terminal 2
python problem2_student_scores/scores_chart.py
```

The API serves `GET /health` and `GET /api/scores` (optional, case-insensitive `?subject=physics` filter). The chart script fetches the scores with a 5-second timeout, skips malformed entries (non-numeric, boolean or outside 0-100), prints the table with the average, highest and lowest score, and saves the chart. If the API is not running it says so in one line and exits with status 1.

![Student Test Scores](problem2_student_scores/student_scores_chart.png)

## Problem 3 - CSV to SQLite

```bash
python problem3_csv_to_sqlite/import_users.py
```

Reads `users.csv` (13 rows), validates each row, and inserts the valid ones into `problem3_csv_to_sqlite/users.db` in a single transaction. Expected first run: `inserted: 10  duplicates: 1  skipped_invalid: 2`, with line 13 rejected for an invalid email and line 14 for a missing name. A second run reports `inserted: 0`.

## Assumptions

- Books come from the Open Library Search API because it is free and needs no key. Only the first two authors are kept, and `first_publish_year` is used as the publication year. Open Library can list the same title and author twice as separate works, so the second copy counts as a duplicate.
- No scores API was specified, so `mock_scores_api.py` serves 12 synthetic students with FastAPI. `scores_chart.py` still treats it as an external service: timeout, error handling and input validation.
- `users.csv` is synthetic: made-up names and placeholder `example.*` addresses. It deliberately includes one duplicate email in a different case, one invalid email and one blank name to show that validation and deduplication work.
- Emails are trimmed and lowercased before insert, so the `UNIQUE` constraint deduplicates case-insensitively. The email check is a practical regex, not full RFC 5322.
- Names starting with `=`, `+`, `-` or `@` are rejected, because spreadsheet apps evaluate those as formulas if the data is ever exported (CSV injection).
- All SQL uses parameterized `?` placeholders.
