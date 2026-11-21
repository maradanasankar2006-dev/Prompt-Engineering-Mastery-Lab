"""Focused tests for answer parsing and JSON shape validation."""

import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from modules.reasoning import extract_numerical_answer, is_correct_math_answer
from modules.report_generator import generate_report
from modules.structured_output import validate_extraction
from modules.zero_few_shot import extract_sentiment


class ReasoningTests(unittest.TestCase):
    def test_extracts_labeled_decimal_final_answer(self):
        self.assertEqual(
            extract_numerical_answer("Key steps: 36 x .75 = 27. Final answer: 29.16"),
            Decimal("29.16"),
        )

    def test_unparseable_answer_is_not_marked_correct(self):
        self.assertIsNone(is_correct_math_answer("No numerical answer.", "18"))


class StructuredOutputTests(unittest.TestCase):
    def test_accepts_expected_json_types(self):
        valid, _, parsed = validate_extraction(
            '{"name":"Maya","date":"2026-03-15","amount":48.5,'
            '"currency":"USD","description":"Supplies"}'
        )
        self.assertTrue(valid)
        self.assertEqual(parsed["amount"], 48.5)

    def test_rejects_boolean_as_number(self):
        valid, message, _ = validate_extraction(
            '{"name":"","date":"","amount":true,"currency":"","description":""}'
        )
        self.assertFalse(valid)
        self.assertIn("number", message)

    def test_rejects_nonstandard_json_numbers(self):
        valid, message, _ = validate_extraction(
            '{"name":"","date":"","amount":NaN,"currency":"","description":""}'
        )
        self.assertFalse(valid)
        self.assertIn("Invalid JSON", message)


class SentimentTests(unittest.TestCase):
    def test_accepts_only_a_single_label(self):
        self.assertEqual(extract_sentiment("Positive"), "Positive")
        self.assertIsNone(extract_sentiment("The sentiment is Positive."))


class ReportTests(unittest.TestCase):
    def test_empty_report_marks_experiments_not_yet_run(self):
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "report.md"
            generate_report([], path)
            report = path.read_text(encoding="utf-8")
        self.assertIn("Not yet run", report)
        self.assertIn("JSON validation success rate", report)


if __name__ == "__main__":
    unittest.main()
