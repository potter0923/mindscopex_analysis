from __future__ import annotations

import unittest

from experiments.jobs.thinking_patch import (
    body_until_close,
    gap_closure,
    rank_difference_features,
    summarise,
    tail_after_close,
)


class GapClosureTests(unittest.TestCase):
    def test_reaching_the_on_margin_is_one(self) -> None:
        self.assertAlmostEqual(gap_closure(3.0, -9.0, -9.0), 1.0)

    def test_no_change_is_zero(self) -> None:
        self.assertAlmostEqual(gap_closure(3.0, 3.0, -9.0), 0.0)

    def test_halfway(self) -> None:
        self.assertAlmostEqual(gap_closure(2.0, -2.0, -6.0), 0.5)

    def test_moving_the_wrong_way_is_negative(self) -> None:
        self.assertLess(gap_closure(2.0, 4.0, -6.0), 0.0)

    def test_no_gap_gives_none_not_a_huge_ratio(self) -> None:
        # Thinking barely moved this item: a ratio over a 0.1-nat gap is noise.
        self.assertIsNone(gap_closure(1.0, -3.0, 0.9))
        self.assertIsNone(gap_closure(-1.0, -3.0, 2.0))


class TraceTextTests(unittest.TestCase):
    def test_opening_tag_is_stripped_and_close_kept(self) -> None:
        body, done = body_until_close("<think>\nreason\n</think>\n\ncat<|im_end|>")
        self.assertEqual(body, "reason\n</think>")
        self.assertTrue(done)

    def test_unclosed_trace_is_closed_and_flagged(self) -> None:
        body, done = body_until_close("<think>\nstill going")
        self.assertTrue(body.endswith("</think>"))
        self.assertFalse(done)

    def test_tail_after_the_last_close(self) -> None:
        close = [9]
        self.assertEqual(tail_after_close([1, 2, 9, 5, 5], close), [5, 5])
        self.assertEqual(tail_after_close([1, 9, 2, 9], close), [])
        self.assertIsNone(tail_after_close([1, 2, 3], close))


class RankingTests(unittest.TestCase):
    def test_absent_counts_as_zero_and_sign_is_kept(self) -> None:
        off = [{1: 10.0, 2: 1.0}, {1: 12.0}]
        on = [{3: 4.0}, {3: 6.0, 2: 1.0}]
        rows = rank_difference_features(off, on, top_n=10)
        by_id = {r["feature_id"]: r for r in rows}
        self.assertEqual(rows[0]["feature_id"], 1)  # |-11| is the largest change
        self.assertEqual(by_id[1]["direction"], "down_in_on")
        self.assertAlmostEqual(by_id[3]["mean_diff"], 5.0)
        self.assertEqual(by_id[3]["direction"], "up_in_on")
        self.assertNotIn(2, by_id)  # +1 on one item, -1 on the other: mean 0

    def test_one_item_outlier_shows_low_agreement(self) -> None:
        off = [{}, {}, {}, {}]
        on = [{7: 40.0}, {}, {}, {}]
        row = rank_difference_features(off, on, top_n=5)[0]
        self.assertAlmostEqual(row["sign_agreement"], 0.25)

    def test_top_n_and_rank(self) -> None:
        off = [{i: float(i) for i in range(1, 6)}]
        on = [{}]
        rows = rank_difference_features(off, on, top_n=2)
        self.assertEqual([r["feature_id"] for r in rows], [5, 4])
        self.assertEqual([r["rank"] for r in rows], [1, 2])

    def test_unpaired_input_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            rank_difference_features([{}], [], top_n=1)


class SummariseTests(unittest.TestCase):
    def test_gap_ignores_unfinished_traces_but_counts_answers(self) -> None:
        rows = [
            {
                "arm": "a",
                "label": "correct",
                "margin": -1.0,
                "gap_closure": 1.0,
                "on_completed": True,
            },
            {"arm": "a", "label": "lure", "margin": 1.0, "gap_closure": 9.0, "on_completed": False},
            {"arm": "a", "label": "lure", "margin": 2.0, "gap_closure": None, "on_completed": True},
        ]
        (out,) = summarise(rows, ["arm"])
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["correct"], 1)
        self.assertEqual(out["n_gap"], 1)
        self.assertAlmostEqual(out["mean_gap_closure"], 1.0)


if __name__ == "__main__":
    unittest.main()
