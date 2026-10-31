import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from relaypay_support_evals import eval as eval_module


PASS_ANSWER = (
    "The conversion fee is 2 EUR, so 198 EUR remains to be converted. "
    "The exact USD amount cannot be determined because no exchange rate "
    "is provided. The fee and final amount are shown before confirmation."
)

FAIL_ANSWER = "Hello."


def fake_generate_pass(case_id: str):
    return (
        {"id": "fees_conversion_01", "relevant_rules": ["PRODUCT-06"]},
        [("PRODUCT-06", "rule text")],
        PASS_ANSWER,
    )


def fake_generate_fail(case_id: str):
    return (
        {"id": "fees_conversion_01", "relevant_rules": ["PRODUCT-06"]},
        [("PRODUCT-06", "rule text")],
        FAIL_ANSWER,
    )


class EvalTests(unittest.TestCase):
    def test_run_eval_passes_good_response(self) -> None:
        with patch.object(eval_module, "generate", fake_generate_pass):
            case, rules, answer, result = eval_module.run_eval(
                "fees_conversion_01"
            )

        self.assertEqual(case["id"], "fees_conversion_01")
        self.assertEqual(answer, PASS_ANSWER)
        self.assertTrue(result.passed)

    def test_run_eval_fails_bad_response(self) -> None:
        with patch.object(eval_module, "generate", fake_generate_fail):
            _, _, _, result = eval_module.run_eval("fees_conversion_01")

        self.assertFalse(result.passed)
        self.assertEqual(len(result.checks), 6)

    def test_run_eval_rejects_unsupported_case(self) -> None:
        mock_generate = MagicMock(
            side_effect=AssertionError("generate must not be called")
        )

        with patch.object(eval_module, "generate", mock_generate):
            with self.assertRaisesRegex(ValueError, "Unsupported case"):
                eval_module.run_eval("transfer_pending_01")

        mock_generate.assert_not_called()

    def test_main_prints_result(self) -> None:
        with patch.object(eval_module, "generate", fake_generate_pass):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = eval_module.main(["--case", "fees_conversion_01"])

        self.assertEqual(code, 0)
        output = buf.getvalue()
        self.assertIn("Case: fees_conversion_01", output)
        self.assertIn("Result: PASS", output)
        self.assertIn("states_fee_2_eur", output)

    def test_main_returns_nonzero_on_fail(self) -> None:
        with patch.object(eval_module, "generate", fake_generate_fail):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = eval_module.main(["--case", "fees_conversion_01"])

        self.assertEqual(code, 1)
        self.assertIn("Result: FAIL", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
