from __future__ import annotations

import unittest

from experiments.jobs.screen_traps import classify, contains_answer, normalise


class NormaliseTests(unittest.TestCase):
    def test_case_and_padding_are_removed(self) -> None:
        self.assertEqual(normalise("  90 Minutes.  "), "90 minutes.")

    def test_currency_survives_but_commas_do_not(self) -> None:
        self.assertEqual(normalise("$1,100"), "$1100")


class ContainsAnswerTests(unittest.TestCase):
    def test_plain_substring(self) -> None:
        self.assertTrue(contains_answer("It takes 60 minutes.", " 60 minutes"))

    def test_same_number_said_differently_still_counts(self) -> None:
        # A screen that only did string matching would reject this, and we would
        # drop items the model actually answered correctly.
        self.assertTrue(contains_answer("0.10 dollars", "$0.10"))

    def test_a_different_number_does_not_count(self) -> None:
        self.assertFalse(contains_answer("It takes 90 minutes.", " 60 minutes"))

    def test_trailing_punctuation_is_tolerated(self) -> None:
        self.assertTrue(contains_answer("  $0.05.  ", "$0.05"))


class ClassifyTests(unittest.TestCase):
    def test_lure_only(self) -> None:
        self.assertEqual(classify("60 minutes.", " 90 minutes", " 60 minutes"), "lure")

    def test_correct_only(self) -> None:
        self.assertEqual(
            classify("The job takes 90 minutes.", " 90 minutes", " 60 minutes"), "correct"
        )

    def test_neither_is_other(self) -> None:
        self.assertEqual(classify("I am not sure.", " 2", " 30"), "other")

    def test_nested_answers_are_told_apart(self) -> None:
        # "Eligible" sits inside "Not eligible"; a substring check sees both.
        self.assertEqual(classify("Not eligible.", "Not eligible", "Eligible"), "correct")
        self.assertEqual(
            classify("The return is not eligible.", "Not eligible", "Eligible"), "correct"
        )
        self.assertEqual(classify("Eligible.", "Not eligible", "Eligible"), "lure")
        self.assertEqual(classify("Unclear.", "Not eligible", "Eligible"), "other")

    def test_both_present_is_other_not_a_pass(self) -> None:
        # "60, no — 90" states the answer but also the lure; counting that as a
        # trap would inflate the keep rate, so it is not a verdict either way.
        self.assertEqual(
            classify("60, sorry, 90 minutes.", " 90 minutes", " 60 minutes"), "other"
        )


if __name__ == "__main__":
    unittest.main()
