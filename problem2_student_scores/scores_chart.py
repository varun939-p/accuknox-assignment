import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import requests
from matplotlib.patches import Patch

API_URL = "http://127.0.0.1:8000/api/scores"
CHART_PATH = Path(__file__).resolve().parent / "student_scores_chart.png"

ABOVE_COLOR = "#4682B4"
BELOW_COLOR = "#9AA5B1"
AVERAGE_COLOR = "#C8553D"


def fetch_records() -> list:
    response = requests.get(API_URL, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def clean_records(records: list) -> list[tuple[str, str, float]]:
    students = []
    for item in records:
        if not isinstance(item, dict):
            continue
        name, subject, score = item.get("name"), item.get("subject"), item.get("score")
        if not isinstance(name, str) or not name.strip():
            continue
        # bool is a subclass of int in Python, so a JSON true would otherwise count as a score of 1.
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            continue
        if not 0 <= score <= 100:
            continue
        subject = subject.strip() if isinstance(subject, str) and subject.strip() else "-"
        students.append((name.strip(), subject, float(score)))
    return students


def print_summary(students: list[tuple[str, str, float]], average: float) -> None:
    print(f"{'Name':<18}  {'Subject':<18}  {'Score':>5}")
    print(f"{'-' * 18}  {'-' * 18}  {'-' * 5}")
    for name, subject, score in students:
        print(f"{name[:18]:<18}  {subject[:18]:<18}  {score:>5g}")

    top = max(students, key=lambda s: s[2])
    bottom = min(students, key=lambda s: s[2])
    print()
    print(f"students: {len(students)}")
    print(f"average:  {average:.2f}")
    print(f"highest:  {top[2]:g} ({top[0]})")
    print(f"lowest:   {bottom[2]:g} ({bottom[0]})")


def plot_scores(students: list[tuple[str, str, float]], average: float, path: Path) -> None:
    ranked = sorted(students, key=lambda s: s[2], reverse=True)
    names = [s[0] for s in ranked]
    scores = [s[2] for s in ranked]
    colors = [ABOVE_COLOR if score >= average else BELOW_COLOR for score in scores]
    # Numeric x positions so two students with the same name still get separate bars.
    positions = range(len(ranked))

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(positions, scores, color=colors, width=0.65, zorder=2)
    ax.bar_label(bars, labels=[f"{score:g}" for score in scores], padding=3, fontsize=9)

    ax.axhline(average, color=AVERAGE_COLOR, linestyle="--", linewidth=1.3, zorder=3)
    ax.text(len(ranked) - 0.5, average + 1.2, f"Class average: {average:.2f}",
            ha="right", va="bottom", fontsize=9, color=AVERAGE_COLOR)

    ax.set_xticks(positions, names, rotation=30, ha="right")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Score")
    ax.set_title(f"Student Test Scores (n={len(ranked)})", loc="left", fontsize=13)
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color="#E3E6EA", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(
        handles=[Patch(color=ABOVE_COLOR, label="At or above average"), Patch(color=BELOW_COLOR, label="Below average")],
        loc="upper right",
        frameon=False,
        fontsize=9,
    )

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    try:
        records = fetch_records()
    except requests.ConnectionError:
        print(f"error: cannot reach {API_URL} - start it first with: python mock_scores_api.py", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"error: failed to fetch scores: {exc}", file=sys.stderr)
        return 1

    students = clean_records(records)
    if len(students) < len(records):
        print(f"skipped {len(records) - len(students)} malformed record(s)")
    if not students:
        print("error: no valid scores to plot", file=sys.stderr)
        return 1

    average = sum(s[2] for s in students) / len(students)
    print_summary(students, average)
    plot_scores(students, average, CHART_PATH)
    print(f"\nchart saved to {CHART_PATH}")
    return 0


if __name__ == "__main__":
    # Redirected stdout on Windows defaults to cp1252, which crashes on names outside that code page.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
