import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Mock Student Scores API")

STUDENTS = [
    {"id": 1, "name": "Aarav Sharma", "subject": "Mathematics", "score": 84},
    {"id": 2, "name": "Priya Nair", "subject": "Physics", "score": 91},
    {"id": 3, "name": "Rohan Mehta", "subject": "Computer Science", "score": 67},
    {"id": 4, "name": "Ananya Iyer", "subject": "Mathematics", "score": 96},
    {"id": 5, "name": "Daniel Okafor", "subject": "Physics", "score": 72},
    {"id": 6, "name": "Sofia Martinez", "subject": "Computer Science", "score": 88},
    {"id": 7, "name": "Karthik Reddy", "subject": "Mathematics", "score": 58},
    {"id": 8, "name": "Emily Chen", "subject": "Physics", "score": 79},
    {"id": 9, "name": "Arjun Patel", "subject": "Computer Science", "score": 93},
    {"id": 10, "name": "Fatima Khan", "subject": "Mathematics", "score": 74},
    {"id": 11, "name": "Lucas Weber", "subject": "Physics", "score": 63},
    {"id": 12, "name": "Sneha Kulkarni", "subject": "Computer Science", "score": 85},
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scores")
def get_scores(subject: str | None = None) -> list[dict]:
    if subject is None:
        return STUDENTS
    return [s for s in STUDENTS if s["subject"].casefold() == subject.strip().casefold()]


if __name__ == "__main__":
    # Bound to localhost on purpose: this is a dev mock, not something to expose on the network.
    uvicorn.run(app, host="127.0.0.1", port=8000)
