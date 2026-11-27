"""Command line interface for the CPM scheduler.

Usage:
    python -m cpm_scheduler examples/single-storey-house.json
    python -m cpm_scheduler examples/single-storey-house.csv --gantt
    python -m cpm_scheduler my-project.json --output schedule.txt
"""

from __future__ import annotations

import argparse
import sys

from .model import ScheduleError, load_tasks
from .report import render_gantt, render_table
from .schedule import compute_schedule


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cpm-scheduler",
        description=(
            "Compute a Critical Path Method schedule from a JSON or CSV "
            "task list."
        ),
    )
    parser.add_argument(
        "input",
        help="Path to a JSON or CSV file with tasks "
        "(see examples/single-storey-house.json).",
    )
    parser.add_argument(
        "--gantt",
        action="store_true",
        help="Also print a text Gantt chart.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write the report to this file instead of printing it.",
    )
    args = parser.parse_args(argv)

    try:
        tasks = load_tasks(args.input)
        schedule = compute_schedule(tasks)
    except ScheduleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = render_table(schedule)
    if args.gantt:
        report += "\n\n" + render_gantt(schedule)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
        print(f"Report written to {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
