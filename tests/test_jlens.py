from __future__ import annotations

import unittest

from mindscopex_analysis.cases import LureCase
from mindscopex_analysis.jlens import (
    DEFAULT_TARGET_LAYER,
    LayerReadout,
    answers_are_separable,
    divergence_layer,
    first_token_id,
    token_rank,
    trajectory_rows,
)


class _Tokenizer:
    """Maps each distinct word to a stable id; enough for first-token logic."""

    def __init__(self) -> None:
        self._ids: dict[str, int] = {}

    def encode(self, text: str, add_special_tokens: bool = True):
        del add_special_tokens
        return [self._ids.setdefault(word, len(self._ids)) for word in text.split()]


def _readout(condition: str, layer: int, lure: int, correct: int) -> LayerReadout:
    return LayerReadout(condition=condition, layer=layer, lure_rank=lure, correct_rank=correct)


class TokenRankTests(unittest.TestCase):
    def test_rank_is_one_for_the_argmax(self) -> None:
        self.assertEqual(token_rank([0.1, 0.9, 0.4], 1), 1)

    def test_rank_counts_strictly_greater_scores(self) -> None:
        self.assertEqual(token_rank([0.1, 0.9, 0.4], 2), 2)
        self.assertEqual(token_rank([0.1, 0.9, 0.4], 0), 3)

    def test_ties_share_the_better_rank(self) -> None:
        # Two equal scores: neither is "beaten", so both rank 1.
        self.assertEqual(token_rank([0.5, 0.5, 0.1], 0), 1)
        self.assertEqual(token_rank([0.5, 0.5, 0.1], 1), 1)

    def test_out_of_range_raises(self) -> None:
        with self.assertRaises(IndexError):
            token_rank([0.1, 0.2], 5)


class LayerReadoutTests(unittest.TestCase):
    def test_lure_advantage_above_one_when_lure_leads(self) -> None:
        self.assertGreater(_readout("hostile", 3, lure=1, correct=40).lure_advantage, 1.0)

    def test_lure_advantage_below_one_when_correct_leads(self) -> None:
        self.assertLess(_readout("explicit", 3, lure=50, correct=2).lure_advantage, 1.0)

    def test_rank_one_denominator_is_safe(self) -> None:
        self.assertEqual(_readout("hostile", 0, lure=1, correct=7).lure_advantage, 7.0)


class DivergenceLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        # hostile keeps the lure near the top from layer 2 on; explicit pushes it away.
        self.traj = {
            "hostile": {
                0: _readout("hostile", 0, lure=90, correct=95),
                2: _readout("hostile", 2, lure=10, correct=40),
                4: _readout("hostile", 4, lure=1, correct=60),
            },
            "explicit": {
                0: _readout("explicit", 0, lure=88, correct=96),
                2: _readout("explicit", 2, lure=30, correct=12),
                4: _readout("explicit", 4, lure=200, correct=2),
            },
        }

    def test_picks_the_layer_with_the_widest_gap(self) -> None:
        layer, ratio = divergence_layer(self.traj)
        self.assertEqual(layer, 4)
        self.assertAlmostEqual(ratio, 200.0)

    def test_missing_condition_raises(self) -> None:
        with self.assertRaises(KeyError):
            divergence_layer(self.traj, control="neutral")

    def test_disjoint_layers_raise(self) -> None:
        traj = {
            "hostile": {0: _readout("hostile", 0, 1, 2)},
            "explicit": {5: _readout("explicit", 5, 1, 2)},
        }
        with self.assertRaises(ValueError):
            divergence_layer(traj)


class TrajectoryRowsTests(unittest.TestCase):
    def test_rows_are_sorted_by_condition_then_layer(self) -> None:
        traj = {
            "hostile": {4: _readout("hostile", 4, 1, 9), 0: _readout("hostile", 0, 5, 6)},
            "explicit": {0: _readout("explicit", 0, 7, 3)},
        }
        rows = trajectory_rows(traj)
        self.assertEqual(
            [(r["condition"], r["layer"]) for r in rows],
            [("explicit", 0), ("hostile", 0), ("hostile", 4)],
        )
        self.assertIn("lure_advantage", rows[0])


class AnswerTokenTests(unittest.TestCase):
    def test_first_token_is_taken(self) -> None:
        tok = _Tokenizer()
        self.assertEqual(first_token_id(tok, "drive there"), first_token_id(tok, "drive away"))

    def test_empty_answer_raises(self) -> None:
        with self.assertRaises(ValueError):
            first_token_id(_Tokenizer(), "")

    def test_separable_when_first_tokens_differ(self) -> None:
        case = LureCase(
            case_id="c",
            family="f",
            prompt="p",
            correct_answer="drive there",
            lure_answer="walk there",
        )
        self.assertTrue(answers_are_separable(_Tokenizer(), case))

    def test_not_separable_when_first_tokens_match(self) -> None:
        # A real hazard: the lens reads one token, so these two are indistinguishable.
        case = LureCase(
            case_id="c",
            family="f",
            prompt="p",
            correct_answer="go upstairs first",
            lure_answer="go directly there",
        )
        self.assertFalse(answers_are_separable(_Tokenizer(), case))


class DefaultsTests(unittest.TestCase):
    def test_target_layer_matches_the_paper(self) -> None:
        # The paper transports to the penultimate layer, not the final one.
        self.assertEqual(DEFAULT_TARGET_LAYER, -2)

    def test_module_imports_without_jlens_installed(self) -> None:
        import mindscopex_analysis.jlens as module

        self.assertTrue(hasattr(module, "condition_trajectories"))


if __name__ == "__main__":
    unittest.main()
