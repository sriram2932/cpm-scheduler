"""Task model and input loading for the CPM scheduler.

A task is defined by an id, a name, a duration in whole days, and the ids of
the tasks that must finish before it can start. Tasks can be loaded from
JSON or CSV. Both formats are documented in the README and in the examples
folder.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path


class ScheduleError(ValueError):
    """Raised when the input tasks cannot form a valid schedule."""


@dataclass
class Task:
    """One activity in the programme."""

    id: str
    name: str
    duration: int
    predecessors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ScheduleError("Task id must not be empty.")
        if not self.name:
            raise ScheduleError(f"Task {self.id!r} must have a name.")
        if not isinstance(self.duration, int) or self.duration < 0:
            raise ScheduleError(
                f"Task {self.id!r} duration must be a whole number of days, "
                "zero or more."
            )
        if self.id in self.predecessors:
            raise ScheduleError(f"Task {self.id!r} cannot depend on itself.")


def _tasks_from_dicts(rows: list[dict]) -> list[Task]:
    tasks: list[Task] = []
    seen: set[str] = set()
    for row in rows:
        task_id = str(row.get("id", "")).strip()
        if not task_id:
            raise ScheduleError("Every task needs an id.")
        if task_id in seen:
            raise ScheduleError(f"Duplicate task id: {task_id!r}.")
        seen.add(task_id)
        raw_duration = row.get("duration", 0)
        if isinstance(raw_duration, str):
            raw_duration = raw_duration.strip()
            try:
                raw_duration = int(raw_duration)
            except ValueError:
                try:
                    as_float = float(raw_duration)
                except ValueError:
                    as_float = None
                if as_float is None or not as_float.is_integer():
                    raise ScheduleError(
                        f"Task {task_id!r} duration must be a whole number "
                        "of days."
                    )
                raw_duration = int(as_float)
        if isinstance(raw_duration, float) and raw_duration.is_integer():
            raw_duration = int(raw_duration)
        if not isinstance(raw_duration, int):
            raise ScheduleError(
                f"Task {task_id!r} duration must be a whole number of days."
            )
        raw_preds = row.get("predecessors") or row.get("depends_on") or []
        if isinstance(raw_preds, str):
            preds = [p.strip() for p in raw_preds.split(",") if p.strip()]
        else:
            preds = [str(p).strip() for p in raw_preds if str(p).strip()]
        tasks.append(
            Task(
                id=task_id,
                name=str(row.get("name", task_id)).strip() or task_id,
                duration=raw_duration,
                predecessors=preds,
            )
        )
    known = {t.id for t in tasks}
    for task in tasks:
        for pred in task.predecessors:
            if pred not in known:
                raise ScheduleError(
                    f"Task {task.id!r} depends on unknown task {pred!r}."
                )
    return tasks


def load_tasks(path: str | Path) -> list[Task]:
    """Load tasks from a JSON or CSV file, chosen by file extension."""
    path = Path(path)
    if not path.exists():
        raise ScheduleError(f"File not found: {path}")
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            rows = data.get("tasks")
            if not isinstance(rows, list):
                raise ScheduleError(
                    "JSON input must be a list of tasks or an object with a "
                    "'tasks' list."
                )
        elif isinstance(data, list):
            rows = data
        else:
            raise ScheduleError("JSON input must be a list of tasks.")
        return _tasks_from_dicts(rows)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or "id" not in reader.fieldnames:
                raise ScheduleError(
                    "CSV input needs a header row with at least an 'id' "
                    "column."
                )
            return _tasks_from_dicts(list(reader))
    raise ScheduleError(
        f"Unsupported file type {path.suffix!r}. Use .json or .csv."
    )
