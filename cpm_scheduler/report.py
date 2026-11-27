"""Plain text reports for a computed schedule: a table and a Gantt chart."""

from __future__ import annotations

from .schedule import Schedule


def render_table(schedule: Schedule) -> str:
    """Render the schedule as an aligned text table."""
    rows = [
        ("ID", "Task", "Dur", "ES", "EF", "LS", "LF", "Float", "Critical"),
    ]
    for item in schedule.tasks:
        rows.append(
            (
                item.task.id,
                item.task.name,
                str(item.task.duration),
                str(item.early_start),
                str(item.early_finish),
                str(item.late_start),
                str(item.late_finish),
                str(item.total_float),
                "YES" if item.is_critical else "",
            )
        )
    widths = [
        max(len(row[col]) for row in rows) for col in range(len(rows[0]))
    ]
    lines: list[str] = []
    for i, row in enumerate(rows):
        padded = [
            row[col].ljust(widths[col]) if col == 1 else row[col].rjust(widths[col])
            for col in range(len(row))
        ]
        lines.append("  ".join(padded).rstrip())
        if i == 0:
            lines.append("  ".join("-" * w for w in widths))
    lines.append("")
    lines.append(f"Project duration: {schedule.project_duration} days")
    lines.append(
        "Critical path: " + " -> ".join(schedule.critical_path_ids())
    )
    return "\n".join(lines)


def render_gantt(schedule: Schedule, max_width: int = 80) -> str:
    """Render a simple text Gantt chart using early start and finish."""
    if not schedule.tasks:
        return ""
    label_width = max(len(item.task.id) for item in schedule.tasks)
    duration = schedule.project_duration
    scale = max(1, duration / max(1, max_width - label_width - 3))
    lines = ["Gantt chart (early dates, one char per "
             f"{scale:.1f} day{'s' if scale != 1 else ''})"]
    for item in schedule.tasks:
        start = int(item.early_start / scale)
        length = max(1, int(item.task.duration / scale)) if item.task.duration else 1
        bar = " " * start + ("#" if item.is_critical else "=") * length
        lines.append(
            f"{item.task.id.ljust(label_width)} | {bar}"
        )
    lines.append("")
    lines.append("# = critical task, = = non-critical task")
    return "\n".join(lines)
