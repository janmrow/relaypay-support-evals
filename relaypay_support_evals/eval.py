from __future__ import annotations

import argparse
from typing import Any

import anthropic
import yaml

from relaypay_support_evals.generate import generate
from relaypay_support_evals.oracle import EvalResult, assert_supported, evaluate


def run_eval(
    case_id: str,
) -> tuple[dict[str, Any], list[tuple[str, str]], str, EvalResult]:
    assert_supported(case_id)
    case, rules, answer = generate(case_id)
    result = evaluate(answer, case_id=case["id"])
    return case, rules, answer, result


def format_result(result: EvalResult) -> str:
    lines = [f"Result: {'PASS' if result.passed else 'FAIL'}", "", "Checks:"]
    for check in result.checks:
        mark = "PASS" if check.passed else "FAIL"
        lines.append(f"  [{mark}] {check.name}: {check.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate one LLM response for a RelayPay golden case."
    )
    parser.add_argument("--case", required=True, help="Golden case ID")
    args = parser.parse_args(argv)

    try:
        case, rules, answer, result = run_eval(args.case)
    except (
        ValueError, RuntimeError, FileNotFoundError, KeyError, yaml.YAMLError
    ) as exc:
        parser.exit(1, f"error: {exc}\n")
    except anthropic.AnthropicError as exc:
        parser.exit(1, f"error: LLM request failed: {exc}\n")

    print(f"Case: {case['id']}")
    print(f"Rules: {', '.join(rule_id for rule_id, _ in rules)}")
    print("Response:")
    print(answer)
    print()
    print(format_result(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
