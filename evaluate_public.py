"""Run the official public benchmark and save its measured results for the report."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import hw3


def main() -> int:
    root = Path(__file__).resolve().parent
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "hw3.py", "--data-folder", "public_test"], cwd=root, check=False
    )
    if completed.returncode:
        return completed.returncode
    with (root / "results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    truth = json.loads((root / "public_test" / "ground_truth.json").read_text())
    analyses = {}
    for row in rows:
        points = dict(item.split(":", 1) for item in row["points"].split())
        analyses[row["company"]] = {"points": points}
    score = hw3.balanced_point_accuracy(analyses, truth, list(analyses), hw3.CHOSEN_POINTS)
    valid = sum(
        value in hw3.VERDICTS
        for entry in analyses.values() for value in entry["points"].values()
    )
    expected = len(rows) * len(hw3.CHOSEN_POINTS)
    lines = [
        "# Public evaluation", "",
        f"Run time (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}", "",
        f"Model: `{hw3.MODEL_NAME}`. Chosen points: {hw3.CHOSEN_POINTS}.", "",
        f"Companies: {len(rows)}. Valid verdicts: {valid}/{expected}.", "",
        f"Official balanced point accuracy: **{score:.1%}**.", "",
        f"Elapsed time: {time.monotonic() - started:.1f} seconds.", "",
    ]
    if valid < expected:
        lines.extend([
            "This run contains missing verdicts. The official scorer counts them as wrong; "
            "this is not a completed accuracy measurement of the decision rules.", "",
        ])
    mismatches = [row for row in rows if row["point_errors"]]
    lines.extend(["## Disagreements and unavailable analyses", ""])
    if not mismatches:
        lines.append("None: all selected verdicts match the public answer key.")
    for row in mismatches:
        lines.append(f"- `{row['company']}`: {row['point_errors']}. {row['summary']}")
    lines.extend(["", "## Interview usage", ""])
    lines.extend(f"- `{row['company']}`: {row['interviews_used']}." for row in rows)
    (root / "public_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Saved public_evaluation.md")
    return 0 if valid == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
