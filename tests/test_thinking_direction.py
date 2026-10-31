from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from experiments.jobs.thinking_direction import RowLog, count_table, leave_one_out_means


class LeaveOneOutTests(unittest.TestCase):
    def test_each_item_gets_the_others_mean(self) -> None:
        out = leave_one_out_means({"a": 2.0, "b": 4.0, "c": 9.0}, include=["a", "b"])
        self.assertEqual(out["a"], 4.0)  # only b
        self.assertEqual(out["b"], 2.0)  # only a
        # c never contributes (its trace did not finish) but is still evaluated
        self.assertEqual(out["c"], 3.0)

    def test_nothing_to_average(self) -> None:
        self.assertEqual(leave_one_out_means({"a": 1.0}, include=[]), {})
        self.assertEqual(leave_one_out_means({"a": 1.0}, include=["a"]), {})


class CountTableTests(unittest.TestCase):
    def test_fix_and_damage_are_relative_to_the_same_item(self) -> None:
        rows = [
            {"item": "x", "kind": "trap", "arm": "none", "label": "lure"},
            {"item": "x", "kind": "trap", "arm": "d", "label": "correct"},
            {"item": "y", "kind": "trap", "arm": "none", "label": "correct"},
            {"item": "y", "kind": "trap", "arm": "d", "label": "lure"},
            {"item": "z", "kind": "trap", "arm": "none", "label": "correct"},
            {"item": "z", "kind": "trap", "arm": "d", "label": "correct"},
        ]
        by_arm = {r["arm"]: r for r in count_table(rows, ["arm"])}
        self.assertEqual(by_arm["d"]["correct"], 2)
        self.assertEqual(by_arm["d"]["lure_to_correct"], 1)  # z was already right
        self.assertEqual(by_arm["d"]["correct_to_lure"], 1)


class RowLogTests(unittest.TestCase):
    def test_resume_skips_rows_on_disk(self) -> None:
        path = Path(tempfile.mkdtemp()) / "rows.csv"
        log = RowLog(path, ["item", "alpha"])
        log.add({"item": "x", "alpha": 2.0, "label": "correct"})
        log.flush()
        again = RowLog(path, ["item", "alpha"])
        self.assertTrue(again.has(item="x", alpha=2.0))
        self.assertFalse(again.has(item="x", alpha=1.0))
        self.assertEqual(len(again.rows), 1)


if __name__ == "__main__":
    unittest.main()
