import tempfile
import unittest
from pathlib import Path

from relaypay_support_evals.generate import (
    build_context,
    find_case,
    resolve_rules,
)


class GenerateTests(unittest.TestCase):
    def test_loads_case_by_id(self) -> None:
        case = find_case("transfer_pending_01")

        self.assertEqual(case["id"], "transfer_pending_01")
        self.assertEqual(case["relevant_rules"], ["PRODUCT-01", "SUPPORT-05"])

    def test_unknown_case_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown case 'missing_case'"):
            find_case("missing_case")

    def test_resolves_relevant_rules_from_knowledge(self) -> None:
        rules = resolve_rules(["PRODUCT-01", "SUPPORT-05"])

        self.assertEqual(
            [rule_id for rule_id, _ in rules], ["PRODUCT-01", "SUPPORT-05"]
        )
        self.assertIn("### PRODUCT-01", rules[0][1])
        self.assertIn("at most 24 hours", rules[0][1])
        self.assertIn("### SUPPORT-05", rules[1][1])
        self.assertIn("must not promise", rules[1][1])

    def test_unknown_rule_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown rule ID"):
            resolve_rules(["PRODUCT-99"])

    def test_builds_context_in_rule_order(self) -> None:
        rules = [("PRODUCT-01", "first rule"), ("SUPPORT-05", "second rule")]

        self.assertEqual(build_context(rules), "first rule\n\nsecond rule")

    def test_duplicate_rule_reports_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "a.md"
            second = Path(tmpdir) / "b.md"
            first.write_text(
                "### PRODUCT-01 — First\n\nBody.\n", encoding="utf-8"
            )
            second.write_text(
                "### PRODUCT-01 — Second\n\nBody.\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError, r"Duplicate rule ID 'PRODUCT-01'.*a\.md.*b\.md"
            ):
                resolve_rules(["PRODUCT-01"], knowledge_dir=Path(tmpdir))


if __name__ == "__main__":
    unittest.main()
