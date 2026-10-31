import unittest

from relaypay_support_evals.oracle import evaluate


GOOD_RESPONSE = (
    "The conversion fee is 2 EUR, so 198 EUR remains to be converted. "
    "The exact USD amount cannot be determined because no exchange rate "
    "is provided. The fee and final amount are shown before confirmation."
)


class OracleTests(unittest.TestCase):
    def test_pass_on_good_response(self) -> None:
        result = evaluate(GOOD_RESPONSE)

        self.assertEqual(result.case_id, "fees_conversion_01")
        self.assertTrue(result.passed)
        self.assertTrue(all(check.passed for check in result.checks))

    def test_fails_when_fee_missing(self) -> None:
        response = (
            "A conversion fee applies, so less than 200 EUR will be converted. "
            "The exact USD amount cannot be determined because no exchange "
            "rate is provided. The fee and final amount are shown "
            "before confirmation."
        )

        result = evaluate(response)

        self.assertFalse(result.passed)
        by_name = {check.name: check for check in result.checks}
        self.assertFalse(by_name["states_fee_2_eur"].passed)
        self.assertFalse(by_name["states_198_eur_remains"].passed)
        self.assertTrue(by_name["no_hallucinated_usd_amount"].passed)

    def test_fails_when_usd_hallucinated(self) -> None:
        response = (
            "The conversion fee is 2 EUR, so 198 EUR remains to be converted. "
            "Your friend will receive 215.50 USD at 1 EUR = 1.09 USD. "
            "The fee and final amount are shown before confirmation."
        )

        result = evaluate(response)

        self.assertFalse(result.passed)
        by_name = {check.name: check for check in result.checks}
        self.assertFalse(by_name["no_hallucinated_usd_amount"].passed)

    def test_fails_when_unknown_not_acknowledged(self) -> None:
        response = (
            "The conversion fee is 2 EUR, so 198 EUR remains to be converted. "
            "Your friend will receive the converted funds. "
            "The fee and final amount are shown before confirmation."
        )

        result = evaluate(response)

        self.assertFalse(result.passed)
        by_name = {check.name: check for check in result.checks}
        self.assertFalse(by_name["states_usd_amount_unknown"].passed)

    def test_reports_each_check(self) -> None:
        result = evaluate("Hello.")

        self.assertFalse(result.passed)
        self.assertEqual(len(result.checks), 6)
        for check in result.checks:
            self.assertTrue(check.name)
            self.assertTrue(check.detail)

    def test_unknown_case_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported case"):
            evaluate(GOOD_RESPONSE, case_id="transfer_pending_01")

    def test_fails_when_flat_fee_claimed(self) -> None:
        response = (
            "The conversion fee is a 2 EUR flat fee, so 198 EUR remains "
            "to be converted. The exact USD amount cannot be determined. "
            "The fee and final amount are shown before confirmation."
        )

        result = evaluate(response)

        self.assertFalse(result.passed)
        by_name = {check.name: check for check in result.checks}
        self.assertFalse(by_name["no_flat_fee_or_spread"].passed)

    def test_fails_when_shown_word_missing(self) -> None:
        response = (
            "The conversion fee is 2 EUR, so 198 EUR remains to be converted. "
            "The exact USD amount cannot be determined. "
            "You can cancel before confirming."
        )

        result = evaluate(response)

        self.assertFalse(result.passed)
        by_name = {check.name: check for check in result.checks}
        self.assertFalse(
            by_name["states_shown_before_confirmation"].passed
        )

    def test_pass_on_valid_paraphrase(self) -> None:
        response = (
            "For your 200 EUR transfer, the fee is 2 EUR, and the remaining "
            "198 EUR is converted into USD. I can't give the exact USD amount "
            "your friend will receive, because our documentation doesn't "
            "include the exchange rate. The final amount is shown "
            "before you confirm the transfer."
        )

        result = evaluate(response)

        self.assertTrue(result.passed)

    def test_documents_negation_limitation(self) -> None:
        # Known surface-form limitation: the check sees the presence of
        # "2 EUR", not the meaning of the sentence. A future semantic
        # judge should fail this response; the deterministic oracle passes it.
        response = (
            "The fee is not 2 EUR, so 198 EUR remains to be converted. "
            "The exact USD amount cannot be determined because no exchange "
            "rate is provided. The fee and final amount are shown "
            "before confirmation."
        )

        result = evaluate(response)

        by_name = {check.name: check for check in result.checks}
        self.assertTrue(by_name["states_fee_2_eur"].passed)


if __name__ == "__main__":
    unittest.main()
