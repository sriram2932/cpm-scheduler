"""Tests for the CPM scheduler.

Run with:  python -m unittest discover -s tests -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from cpm_scheduler.model import ScheduleError, Task, load_tasks
from cpm_scheduler.report import render_gantt, render_table
from cpm_scheduler.schedule import compute_schedule

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def make_tasks(specs):
    return [
        Task(id=t, name=t, duration=d, predecessors=list(p))
        for t, d, p in specs
    ]


class TestForwardPass(unittest.TestCase):
    def test_simple_chain(self):
        tasks = make_tasks([("A", 2, []), ("B", 3, ["A"]), ("C", 1, ["B"])])
        schedule = compute_schedule(tasks)
        by_id = {s.task.id: s for s in schedule.tasks}
        self.assertEqual((by_id["A"].early_start, by_id["A"].early_finish), (0, 1))
        self.assertEqual((by_id["B"].early_start, by_id["B"].early_finish), (2, 4))
        self.assertEqual((by_id["C"].early_start, by_id["C"].early_finish), (5, 5))
        self.assertEqual(schedule.project_duration, 6)
        self.assertEqual(schedule.critical_path_ids(), ["A", "B", "C"])

    def test_parallel_tasks_start_together(self):
        tasks = make_tasks([("A", 2, []), ("B", 4, []), ("C", 1, ["A", "B"])])
        schedule = compute_schedule(tasks)
        by_id = {s.task.id: s for s in schedule.tasks}
        self.assertEqual(by_id["C"].early_start, 4)
        self.assertEqual(schedule.project_duration, 5)
        self.assertEqual(schedule.critical_path_ids(), ["B", "C"])

    def test_zero_duration_task(self):
        tasks = make_tasks([("A", 0, []), ("B", 3, ["A"])])
        schedule = compute_schedule(tasks)
        by_id = {s.task.id: s for s in schedule.tasks}
        self.assertEqual(by_id["B"].early_start, 0)
        self.assertEqual(schedule.project_duration, 3)

    def test_single_task(self):
        schedule = compute_schedule(make_tasks([("A", 5, [])]))
        self.assertEqual(schedule.project_duration, 5)
        self.assertEqual(schedule.critical_path_ids(), ["A"])


class TestFloatAndCriticalPath(unittest.TestCase):
    def test_float_on_short_branch(self):
        # A -> B (long) and A -> C (short), both feed D.
        tasks = make_tasks(
            [("A", 2, []), ("B", 6, ["A"]), ("C", 2, ["A"]), ("D", 1, ["B", "C"])]
        )
        schedule = compute_schedule(tasks)
        by_id = {s.task.id: s for s in schedule.tasks}
        self.assertEqual(by_id["C"].total_float, 4)
        self.assertEqual(by_id["B"].total_float, 0)
        self.assertEqual(by_id["C"].late_start, 6)
        self.assertEqual(schedule.critical_path_ids(), ["A", "B", "D"])

    def test_example_house_programme(self):
        tasks = load_tasks(EXAMPLES / "single-storey-house.json")
        schedule = compute_schedule(tasks)
        self.assertEqual(schedule.project_duration, 42)
        self.assertEqual(
            schedule.critical_path_ids(),
            ["A", "B", "C", "D", "E", "H", "I", "J", "K", "L"],
        )
        by_id = {s.task.id: s for s in schedule.tasks}
        self.assertEqual(by_id["F"].total_float, 2)
        self.assertEqual(by_id["G"].total_float, 2)


class TestValidation(unittest.TestCase):
    def test_cycle_is_rejected(self):
        tasks = make_tasks([("A", 1, ["B"]), ("B", 1, ["A"])])
        with self.assertRaises(ScheduleError):
            compute_schedule(tasks)

    def test_self_dependency_is_rejected(self):
        with self.assertRaises(ScheduleError):
            Task(id="A", name="A", duration=1, predecessors=["A"])

    def test_negative_duration_is_rejected(self):
        with self.assertRaises(ScheduleError):
            Task(id="A", name="A", duration=-1)

    def test_empty_task_list_is_rejected(self):
        with self.assertRaises(ScheduleError):
            compute_schedule([])

    def test_unknown_predecessor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    [{"id": "A", "name": "A", "duration": 1,
                      "predecessors": ["ZZZ"]}]
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ScheduleError):
                load_tasks(path)

    def test_duplicate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": "A", "name": "A", "duration": 1},
                        {"id": "A", "name": "A again", "duration": 2},
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ScheduleError):
                load_tasks(path)


class TestLoadingAndReports(unittest.TestCase):
    def test_json_and_csv_examples_agree(self):
        from_json = compute_schedule(
            load_tasks(EXAMPLES / "single-storey-house.json")
        )
        from_csv = compute_schedule(
            load_tasks(EXAMPLES / "single-storey-house.csv")
        )
        self.assertEqual(from_json.project_duration, from_csv.project_duration)
        self.assertEqual(
            from_json.critical_path_ids(), from_csv.critical_path_ids()
        )

    def test_table_mentions_critical_path(self):
        schedule = compute_schedule(
            load_tasks(EXAMPLES / "single-storey-house.json")
        )
        table = render_table(schedule)
        self.assertIn("Project duration: 42 days", table)
        self.assertIn("Critical path:", table)
        self.assertIn("Final inspection", table)

    def test_gantt_marks_critical_tasks(self):
        schedule = compute_schedule(
            load_tasks(EXAMPLES / "single-storey-house.json")
        )
        gantt = render_gantt(schedule)
        self.assertIn("# = critical task", gantt)
        self.assertIn("A |", gantt)


if __name__ == "__main__":
    unittest.main()
