"""Critical Path Method scheduler.

A small command line tool that takes a list of tasks with durations and
dependencies and works out the earliest and latest start and finish dates,
the slack for each task, and the critical path. It also prints a simple
text Gantt chart so the programme can be read at a glance.

Only the Python standard library is used, so there is nothing to install.
"""

from .model import Task, load_tasks, ScheduleError
from .schedule import Schedule, compute_schedule
from .report import render_table, render_gantt

__all__ = [
    "Task",
    "Schedule",
    "ScheduleError",
    "compute_schedule",
    "load_tasks",
    "render_table",
    "render_gantt",
]

__version__ = "1.0.0"
