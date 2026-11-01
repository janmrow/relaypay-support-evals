import json
import unittest
from unittest.mock import patch

from relaypay_support_evals import semantic_judge as judge_module
from relaypay_support_evals.results import CheckResult, EvalResult


CASE = {
    "id": "request_cancellation_gap_01",
    "question": (
        "I sent a payment request to a friend, but I changed my mind. "
        "Can I cancel the request, will my friend still be able to pay it, "
        "and has any money been reserved?"
    ),
    "relevant_rules": ["PRODUCT-05", "SUPPORT-05"],
    "expected": [
        "States that payment requests never move money automatically or reserve funds.",
        "Acknowledges that cancellation of a payment request is not defined in the available documentation.",
        "Does not claim whether cancellation is possible or what its effect would be.",
    ],
    "forbidden": [
        "Asserts that the request can be cancelled or gives cancellation steps.",
        "Asserts that the request cannot be cancelled.",
    ],
}

GOOD_RESPONSE = (
    "Payment requests never move money automatically or reserve funds. "
    "The documentation does not define how to cancel a payment request, "
    "so I cannot say whether cancellation is possible."
)


def _judge_response(checks: list[tuple[str, str, bool, str]]) -> str:
    return json.dumps(
        {
            "checks": [
                {
                    "kind": kind,
                    "criterion": criterion,
                    "passed": passed_flag,
                    "reason": reason,
                }
                for kind, criterion, passed_flag, reason in checks
            ]
        }
    )


class ParseJudgeOutputTests(unittest.TestCase):
    def test_parses_all_checks_passing(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], True, "stated clearly"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim made"),
            ("forbidden", CASE["forbidden"][0], True, "no steps given"),
            ("forbidden", CASE["forbidden"][1], True, "not asserted"),
        ]
        raw = _judge_response(checks)

        result = judge_module._parse_judge_output(raw, CASE["expected"], CASE["forbidden"])

        self.assertIsInstance(result, EvalResult)
        self.assertEqual(result.case_id, "request_cancellation_gap_01")
        self.assertTrue(result.passed)
        self.assertEqual(len(result.checks), 5)
        self.assertTrue(all(check.passed for check in result.checks))
        self.assertEqual(result.checks[0].name, "expected")
        self.assertIn(CASE["expected"][0], result.checks[0].detail)

    def test_parses_expected_failure(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], False, "not mentioned"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim made"),
            ("forbidden", CASE["forbidden"][0], True, "no steps given"),
            ("forbidden", CASE["forbidden"][1], True, "not asserted"),
        ]
        raw = _judge_response(checks)

        result = judge_module._parse_judge_output(raw, CASE["expected"], CASE["forbidden"])

        self.assertFalse(result.passed)
        self.assertFalse(result.checks[0].passed)
        self.assertTrue(result.checks[1].passed)

    def test_parses_forbidden_failure(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], True, "stated clearly"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim made"),
            ("forbidden", CASE["forbidden"][0], False, "gives cancellation steps"),
            ("forbidden", CASE["forbidden"][1], True, "not asserted"),
        ]
        raw = _judge_response(checks)

        result = judge_module._parse_judge_output(raw, CASE["expected"], CASE["forbidden"])

        self.assertFalse(result.passed)
        self.assertEqual(result.checks[3].name, "forbidden")
        self.assertFalse(result.checks[3].passed)

    def test_raises_on_invalid_json(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            judge_module._parse_judge_output("{not json}", CASE["expected"], [])

    def test_raises_on_missing_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "must contain a 'checks' key"):
            judge_module._parse_judge_output('{}', CASE["expected"], [])

    def test_raises_on_wrong_number_of_checks(self) -> None:
        raw = '{"checks": [{"kind": "expected", "criterion": "x", "passed": true, "reason": "r"}]}'
        with self.assertRaisesRegex(ValueError, "Judge returned 1 checks, expected 3"):
            judge_module._parse_judge_output(raw, CASE["expected"], [])

    def test_raises_on_check_mismatch(self) -> None:
        raw = '{"checks": [{"kind": "expected", "criterion": "wrong", "passed": true, "reason": "r"}]}'
        with self.assertRaisesRegex(ValueError, "Judge check mismatch"):
            judge_module._parse_judge_output(raw, ["expected criterion"], [])

    def test_raises_on_non_boolean_passed(self) -> None:
        raw = '{"checks": [{"kind": "expected", "criterion": "expected criterion", "passed": "yes", "reason": "r"}]}'
        with self.assertRaisesRegex(ValueError, "'passed' must be a boolean"):
            judge_module._parse_judge_output(raw, ["expected criterion"], [])


class SemanticJudgeEvaluateTests(unittest.TestCase):
    def test_passes_when_all_criteria_pass(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], True, "stated"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim"),
            ("forbidden", CASE["forbidden"][0], True, "ok"),
            ("forbidden", CASE["forbidden"][1], True, "ok"),
        ]
        raw = _judge_response(checks)

        with patch.object(judge_module, "request_judge", return_value=raw):
            result = judge_module.evaluate(GOOD_RESPONSE, CASE)

        self.assertTrue(result.passed)
        self.assertEqual(len(result.checks), 5)

    def test_fails_when_expected_missing(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], False, "not stated"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim"),
            ("forbidden", CASE["forbidden"][0], True, "ok"),
            ("forbidden", CASE["forbidden"][1], True, "ok"),
        ]
        raw = _judge_response(checks)

        with patch.object(judge_module, "request_judge", return_value=raw):
            result = judge_module.evaluate(GOOD_RESPONSE, CASE)

        self.assertFalse(result.passed)
        self.assertFalse(result.checks[0].passed)

    def test_fails_when_forbidden_violated(self) -> None:
        checks = [
            ("expected", CASE["expected"][0], True, "stated"),
            ("expected", CASE["expected"][1], True, "acknowledged"),
            ("expected", CASE["expected"][2], True, "no claim"),
            ("forbidden", CASE["forbidden"][0], False, "gives steps"),
            ("forbidden", CASE["forbidden"][1], True, "ok"),
        ]
        raw = _judge_response(checks)

        with patch.object(judge_module, "request_judge", return_value=raw):
            result = judge_module.evaluate(GOOD_RESPONSE, CASE)

        self.assertFalse(result.passed)
        self.assertFalse(result.checks[3].passed)
        self.assertEqual(result.checks[3].name, "forbidden")

    def test_raises_on_invalid_judge_output(self) -> None:
        with patch.object(judge_module, "request_judge", return_value="{not json}"):
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                judge_module.evaluate(GOOD_RESPONSE, CASE)

    def test_rejects_unsupported_case(self) -> None:
        wrong_case = dict(CASE)
        wrong_case["id"] = "fees_conversion_01"

        with patch.object(
            judge_module, "request_judge", side_effect=AssertionError("must not be called")
        ):
            with self.assertRaisesRegex(ValueError, "Semantic judge only supports"):
                judge_module.evaluate(GOOD_RESPONSE, wrong_case)


if __name__ == "__main__":
    unittest.main()
