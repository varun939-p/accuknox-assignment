import sys
from pathlib import Path

import matplotlib.pyplot as plt
import requests

API_URL = "http://127.0.0.1:8000/api/scores"
CHART_PATH = Path(__file__).resolve().parent / "student_scores_chart.png"


def get_scores():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.ConnectionError:
        sys.exit(f"Could not connect to {API_URL}. Is mock_scores_api.py running?")
    except requests.RequestException as exc:
        sys.exit(f"Request failed: {exc}")
    return [s for s in data if s.get("name") and isinstance(s.get("score"), (int, float))]


def save_chart(students, average):
    students = sorted(students, key=lambda s: s["score"], reverse=True)
    names = [s["name"] for s in students]
    scores = [s["score"] for s in students]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(names, scores, color="steelblue")
    ax.bar_label(bars, padding=3)
    ax.axhline(average, color="crimson", linestyle="--", label=f"Average: {average:.2f}")
    ax.set_title("Student Test Scores")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(CHART_PATH, dpi=150)
    plt.close(fig)


def main():
    students = get_scores()
    if not students:
        sys.exit("The API returned no scores.")

    scores = [s["score"] for s in students]
    average = sum(scores) / len(scores)
    top = max(students, key=lambda s: s["score"])
    bottom = min(students, key=lambda s: s["score"])

    for s in students:
        print(f"{s['name']:<18}{s.get('subject', '-'):<20}{s['score']}")
    print(f"\nAverage: {average:.2f}")
    print(f"Highest: {top['score']} ({top['name']})")
    print(f"Lowest:  {bottom['score']} ({bottom['name']})")

    save_chart(students, average)
    print(f"\nChart saved to {CHART_PATH}")


if __name__ == "__main__":
    main()
