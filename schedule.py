"""Critical Path Method calculation: forward pass, backward pass, slack.

Days are counted from day 0, the programme start. A task with no
predecessors starts on day 0. A task starts the day after its latest
predecessor finishes, so a task of duration 3 starting on day 0 finishes
on day 2 (it occupies days 0, 1 and 2). The project duration is the
finish day of the last task plus one, i.e. the number of working days
from start to finish.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import ScheduleError, Task


@dataclass
class ScheduledTask:
    """A task with its computed schedule dates."""

    task: Task
    early_start: int = 0
    early_finish: int = 0
    late_start: int = 0
    late_finish: int = 0

    @property
    def total_float(self) -> int:
        """Days the task can slip without delaying the project."""
        return self.late_start - self.early_start

    @property
    def is_critical(self) -> bool:
        return self.total_float == 0


@dataclass
class Schedule:
    """The full computed programme."""

    tasks: list[ScheduledTask] = field(default_factory=list)
    project_duration: int = 0

    @property
    def critical_path(self) -> list[ScheduledTask]:
        """Critical tasks in programme order."""
        return [t for t in self.tasks if t.is_critical]

    def critical_path_ids(self) -> list[str]:
        return [t.task.id for t in self.critical_path]


def _topological_order(tasks: list[Task]) -> list[Task]:
    """Order tasks so every predecessor comes before its successors.

    Raises ScheduleError if the dependencies contain a cycle.
    """
    by_id = {t.id: t for t in tasks}
    index = {t.id: i for i, t in enumerate(tasks)}
    in_degree = {t.id: len(t.predecessors) for t in tasks}
    successors: dict[str, list[str]] = {t.id: [] for t in tasks}
    for task in tasks:
        for pred in task.predecessors:
            successors[pred].append(task.id)
    ready = [t.id for t in tasks if in_degree[t.id] == 0]
    order: list[Task] = []
    while ready:
        current = ready.pop(0)
        order.append(by_id[current])
        for nxt in successors[current]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                ready.append(nxt)
        # Keep input order so the printed schedule reads naturally.
        ready.sort(key=lambda tid: index[tid])
    if len(order) != len(tasks):
        remaining = [tid for tid, deg in in_degree.items() if deg > 0]
        raise ScheduleError(
            "Dependencies contain a cycle involving: "
            + ", ".join(sorted(remaining))
            + ". A schedule cannot be computed."
        )
    return order


def compute_schedule(tasks: list[Task]) -> Schedule:
    """Run the forward and backward passes and return the schedule."""
    if not tasks:
        raise ScheduleError("At least one task is required.")
    order = _topological_order(tasks)
    by_id = {t.id: t for t in tasks}
    successors: dict[str, list[str]] = {t.id: [] for t in tasks}
    for task in tasks:
        for pred in task.predecessors:
            successors[pred].append(task.id)

    scheduled: dict[str, ScheduledTask] = {}
    for task in order:
        if task.predecessors:
            # A normal predecessor finishes on its finish day, so the
            # successor starts the next day. A zero-duration predecessor
            # (a milestone) finishes on its start day, so the successor
            # can start that same day.
            early_start = max(
                scheduled[p].early_finish + (1 if scheduled[p].task.duration > 0 else 0)
                for p in task.predecessors
            )
        else:
            early_start = 0
        scheduled[task.id] = ScheduledTask(
            task=task,
            early_start=early_start,
            early_finish=early_start + task.duration - 1
            if task.duration > 0
            else early_start,
        )

    project_duration = max(s.early_finish for s in scheduled.values()) + 1

    for task in reversed(order):
        if successors[task.id]:
            late_finish = min(
                scheduled[s].late_start - (1 if task.duration > 0 else 0)
                for s in successors[task.id]
            )
        else:
            late_finish = project_duration - 1
        item = scheduled[task.id]
        item.late_finish = late_finish
        item.late_start = late_finish - task.duration + 1 if task.duration > 0 else late_finish

    ordered = [scheduled[t.id] for t in order]
    return Schedule(tasks=ordered, project_duration=project_duration)
