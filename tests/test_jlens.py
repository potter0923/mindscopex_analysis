from __future__ import annotations

import unittest

from mindscopex_analysis.cases import LureCase
from mindscopex_analysis.jlens import (
    DEFAULT_TARGET_LAYER,
    LayerReadout,
    answer_contrast,
    answer_margin,
    answers_are_separable,
    bootstrap_delta_ci,
    bootstrap_mean_delta_ci,
    comparison_rows,
    divergence_layer,
    first_token_id,
    layer_correlations,
    spearman,
    split_fit_eval,
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

    def decode(self, ids):
        lookup = {value: key for key, value in self._ids.items()}
        return " ".join(lookup[i] for i in ids)


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


class AnswerContrastTests(unittest.TestCase):
    @staticmethod
    def _case(correct: str, lure: str) -> LureCase:
        return LureCase(
            case_id="c", family="f", prompt="p", correct_answer=correct, lure_answer=lure
        )

    def test_no_prefix_needed_when_they_differ_immediately(self) -> None:
        contrast = answer_contrast(_Tokenizer(), self._case("drive there", "walk there"))
        self.assertEqual(contrast.prefix, "")
        self.assertEqual(contrast.prefix_tokens, 0)
        self.assertFalse(contrast.needs_prefix)
        self.assertNotEqual(contrast.lure_token_id, contrast.correct_token_id)

    def test_shared_opening_becomes_the_prefix(self) -> None:
        # The real hagendorff shape: " $20.0" vs " $40.0" share their opening token.
        contrast = answer_contrast(_Tokenizer(), self._case("$ 20", "$ 40"))
        self.assertEqual(contrast.prefix, "$")
        self.assertEqual(contrast.prefix_tokens, 1)
        self.assertTrue(contrast.needs_prefix)

    def test_longer_shared_opening(self) -> None:
        contrast = answer_contrast(
            _Tokenizer(), self._case("go upstairs first", "go directly there")
        )
        self.assertEqual(contrast.prefix, "go")
        self.assertEqual(contrast.prefix_tokens, 1)

    def test_token_prefix_pair_is_rejected(self) -> None:
        # Nothing distinguishes them at any position, so there is no signal to read.
        with self.assertRaises(ValueError):
            answer_contrast(_Tokenizer(), self._case("twenty", "twenty dollars"))

    def test_separability_matches_the_contrast(self) -> None:
        tok = _Tokenizer()
        self.assertTrue(answers_are_separable(tok, self._case("$ 20", "$ 40")))
        self.assertFalse(answers_are_separable(tok, self._case("twenty", "twenty dollars")))


def _case(case_id: str) -> LureCase:
    return LureCase(
        case_id=case_id,
        family="f",
        prompt="p",
        correct_answer="a",
        lure_answer="b",
    )


class SplitFitEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = [_case(f"c{i}") for i in range(150)]

    def test_split_sizes_match_the_plan(self) -> None:
        fit, evaluation = split_fit_eval(self.cases, n_fit=105)
        self.assertEqual((len(fit), len(evaluation)), (105, 45))

    def test_split_is_disjoint_and_covers_everything(self) -> None:
        fit, evaluation = split_fit_eval(self.cases, n_fit=105)
        fit_ids = {c.case_id for c in fit}
        eval_ids = {c.case_id for c in evaluation}
        self.assertEqual(fit_ids & eval_ids, set())
        self.assertEqual(len(fit_ids | eval_ids), 150)

    def test_same_seed_reproduces_the_split(self) -> None:
        first = [c.case_id for c in split_fit_eval(self.cases, n_fit=105, seed=7)[1]]
        second = [c.case_id for c in split_fit_eval(self.cases, n_fit=105, seed=7)[1]]
        self.assertEqual(first, second)

    def test_different_seeds_give_different_splits(self) -> None:
        a = {c.case_id for c in split_fit_eval(self.cases, n_fit=105, seed=0)[1]}
        b = {c.case_id for c in split_fit_eval(self.cases, n_fit=105, seed=1)[1]}
        self.assertNotEqual(a, b)

    def test_input_order_is_not_mutated(self) -> None:
        before = [c.case_id for c in self.cases]
        split_fit_eval(self.cases, n_fit=105)
        self.assertEqual([c.case_id for c in self.cases], before)

    def test_degenerate_n_fit_raises(self) -> None:
        for n_fit in (0, 150, 151, -1):
            with self.assertRaises(ValueError):
                split_fit_eval(self.cases, n_fit=n_fit)


class AnswerMarginTests(unittest.TestCase):
    def test_positive_when_lure_scores_higher(self) -> None:
        self.assertEqual(answer_margin([1.0, 4.0, 2.0], 1, 2), 2.0)

    def test_negative_when_correct_scores_higher(self) -> None:
        self.assertEqual(answer_margin([1.0, 4.0, 2.0], 2, 1), -2.0)

    def test_out_of_range_raises(self) -> None:
        with self.assertRaises(IndexError):
            answer_margin([1.0, 2.0], 0, 9)


class SpearmanTests(unittest.TestCase):
    def test_perfect_monotone_is_one(self) -> None:
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)

    def test_perfect_reversal_is_minus_one(self) -> None:
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)

    def test_monotone_but_nonlinear_is_still_one(self) -> None:
        # Rank-based, so a curved relationship still scores 1.0.
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [1, 4, 9, 16]), 1.0)

    def test_constant_input_is_zero_not_a_crash(self) -> None:
        self.assertEqual(spearman([1, 1, 1, 1], [4, 3, 2, 1]), 0.0)

    def test_ties_are_averaged(self) -> None:
        # Known value: x=[1,2,2,3] vs y=[1,2,3,4] gives rho = 0.9486832...
        self.assertAlmostEqual(spearman([1, 2, 2, 3], [1, 2, 3, 4]), 0.9486832980505138)

    def test_length_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            spearman([1, 2, 3], [1, 2])

    def test_too_few_points_raises(self) -> None:
        with self.assertRaises(ValueError):
            spearman([1], [1])


class LayerCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.final = {"a": 1.0, "b": 2.0, "c": 3.0}
        self.margins = {
            0: {"a": 3.0, "b": 2.0, "c": 1.0},  # reversed
            5: {"a": 1.0, "b": 2.0, "c": 3.0},  # tracks the final answer
        }

    def test_tracking_layer_scores_higher(self) -> None:
        correlations = layer_correlations(self.margins, self.final)
        self.assertAlmostEqual(correlations[5], 1.0)
        self.assertAlmostEqual(correlations[0], -1.0)

    def test_layers_with_too_few_shared_cases_are_dropped(self) -> None:
        correlations = layer_correlations({9: {"a": 1.0}}, self.final)
        self.assertNotIn(9, correlations)

    def test_only_shared_cases_are_used(self) -> None:
        margins = {5: {"a": 1.0, "b": 2.0, "c": 3.0, "ghost": 99.0}}
        self.assertAlmostEqual(layer_correlations(margins, self.final)[5], 1.0)


class ComparisonRowTests(unittest.TestCase):
    def test_delta_is_jacobian_minus_logit(self) -> None:
        rows = comparison_rows({0: 0.35}, {0: 0.10})
        self.assertAlmostEqual(rows[0]["delta"], 0.25)

    def test_missing_side_leaves_delta_none(self) -> None:
        rows = comparison_rows({0: 0.35}, {})
        self.assertIsNone(rows[0]["delta"])

    def test_rows_are_sorted_by_layer(self) -> None:
        rows = comparison_rows({4: 0.1, 0: 0.2}, {4: 0.0, 0: 0.0})
        self.assertEqual([r["layer"] for r in rows], [0, 4])


class BootstrapDeltaTests(unittest.TestCase):
    def test_clear_win_excludes_zero(self) -> None:
        # J tracks the final margin exactly; the logit baseline is reversed.
        ids = [f"c{i}" for i in range(12)]
        final = {c: float(i) for i, c in enumerate(ids)}
        jacobian = dict(final)
        logit = {c: -float(i) for i, c in enumerate(ids)}
        point, low, high = bootstrap_delta_ci(jacobian, logit, final, draws=400)
        self.assertAlmostEqual(point, 2.0)
        self.assertGreater(low, 0.0)
        self.assertGreaterEqual(high, low)

    def test_tie_interval_contains_zero(self) -> None:
        ids = [f"c{i}" for i in range(12)]
        final = {c: float(i) for i, c in enumerate(ids)}
        point, low, high = bootstrap_delta_ci(dict(final), dict(final), final, draws=400)
        self.assertAlmostEqual(point, 0.0)
        self.assertLessEqual(low, 0.0)
        self.assertGreaterEqual(high, 0.0)

    def test_too_few_shared_cases_raises(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_delta_ci({"a": 1.0}, {"a": 1.0}, {"a": 1.0})


class BootstrapMeanDeltaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ids = [f"c{i}" for i in range(12)]
        self.final = {c: float(i) for i, c in enumerate(self.ids)}
        self.tracking = dict(self.final)
        self.reversed = {c: -float(i) for i, c in enumerate(self.ids)}

    def test_averages_over_every_shared_layer(self) -> None:
        # One layer where J wins by 2.0, one where the two tie: mean is 1.0.
        jacobian = {0: self.tracking, 4: self.tracking}
        logit = {0: self.reversed, 4: self.tracking}
        point, low, high, layers = bootstrap_mean_delta_ci(
            jacobian, logit, self.final, draws=400
        )
        self.assertEqual(layers, [0, 4])
        self.assertAlmostEqual(point, 1.0)
        self.assertGreater(low, 0.0)
        self.assertGreaterEqual(high, low)

    def test_a_single_strong_layer_does_not_decide_the_average(self) -> None:
        # Three ties and one win average to 0.5, well under the winning layer's 2.0.
        jacobian = {n: self.tracking for n in (0, 2, 4, 6)}
        logit = {0: self.reversed, 2: self.tracking, 4: self.tracking, 6: self.tracking}
        point, _low, _high, _layers = bootstrap_mean_delta_ci(
            jacobian, logit, self.final, draws=200
        )
        self.assertAlmostEqual(point, 0.5)

    def test_tie_everywhere_contains_zero(self) -> None:
        layers = {n: self.tracking for n in (0, 2)}
        point, low, high, _ = bootstrap_mean_delta_ci(
            layers, layers, self.final, draws=400
        )
        self.assertAlmostEqual(point, 0.0)
        self.assertLessEqual(low, 0.0)
        self.assertGreaterEqual(high, 0.0)

    def test_only_layers_present_in_both_are_used(self) -> None:
        jacobian = {0: self.tracking, 9: self.tracking}
        logit = {0: self.tracking}
        _point, _low, _high, layers = bootstrap_mean_delta_ci(
            jacobian, logit, self.final, draws=100
        )
        self.assertEqual(layers, [0])

    def test_no_shared_layer_raises(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_mean_delta_ci({0: self.tracking}, {1: self.tracking}, self.final)

    def test_too_few_shared_cases_raises(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_mean_delta_ci({0: {"a": 1.0}}, {0: {"a": 1.0}}, {"a": 1.0})


class DefaultsTests(unittest.TestCase):
    def test_target_layer_matches_the_paper(self) -> None:
        # The paper transports to the penultimate layer, not the final one.
        self.assertEqual(DEFAULT_TARGET_LAYER, -2)

    def test_module_imports_without_jlens_installed(self) -> None:
        import mindscopex_analysis.jlens as module

        self.assertTrue(hasattr(module, "condition_trajectories"))


if __name__ == "__main__":
    unittest.main()
