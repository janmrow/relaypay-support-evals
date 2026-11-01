"""First LLM-based semantic judge.

Evaluates meaning, not surface form, for `request_cancellation_gap_01`.
It uses the expected/forbidden criteria stored in the golden dataset.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from relaypay_support_evals.generate import (
    SESSION_ID,
    build_context,
    load_config,
    resolve_rules,
)
from relaypay_support_evals.results import CheckResult, EvalResult

CASE_ID = "request_cancellation_gap_01"
JUDGE_MAX_TOKENS = 4096

JUDGE_SYSTEM_PROMPT = """\
You are a strict evaluator for RelayPay customer support responses.
Evaluate the response against each criterion below.
Keep each reason short (one sentence).
Do not correct the response, do not reply to the customer, and do not add any text outside the requested JSON."""


def _build_judge_prompt(
    question: str,
    response: str,
    expected: list[str],
    forbidden: list[str],
    context: str | None = None,
) -> str:
    parts = [
        "Customer question:",
        question,
        "",
    ]
    if context is not None:
        parts.extend(
            [
                "RelayPay rules used as context:",
                context,
                "",
            ]
        )
    parts.extend(
        [
            "Generated response:",
            response,
            "",
            "Evaluate the response against these criteria.",
            "",
            "Expected criteria (the response must satisfy each):",
        ]
    )
    for index, criterion in enumerate(expected, start=1):
        parts.append(f"{index}. {criterion}")
    parts.extend(["", "Forbidden criteria (the response must NOT satisfy any):"])
    for index, criterion in enumerate(forbidden, start=1):
        parts.append(f"{index}. {criterion}")
    parts.extend(
        [
            "",
            "Return ONLY a JSON object with this exact structure:",
            "{",
            '  "checks": [',
            '    {"kind": "expected", "criterion": "...", "passed": true, "reason": "..."},',
            '    ...',
            "  ]",
            "}",
            "",
            "Use kind 'expected' or 'forbidden'. Include one entry for every criterion listed above, in the same order.",
            "Return only valid JSON. Do not use Markdown code fences. "
            "Do not add any text before or after the JSON object.",
        ]
    )
    return "\n".join(parts)


def _parse_judge_output(
    raw: str, expected: list[str], forbidden: list[str]
) -> EvalResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Judge JSON must be an object")
    if "checks" not in data:
        raise ValueError("Judge JSON must contain a 'checks' key")

    checks_data = data["checks"]
    if not isinstance(checks_data, list):
        raise ValueError("Judge JSON 'checks' must be a list")

    criteria = [("expected", item) for item in expected] + [
        ("forbidden", item) for item in forbidden
    ]
    if len(checks_data) != len(criteria):
        raise ValueError(
            f"Judge returned {len(checks_data)} checks, expected {len(criteria)}"
        )

    checks: list[CheckResult] = []
    for (kind, criterion), item in zip(criteria, checks_data):
        if not isinstance(item, dict):
            raise ValueError(f"Judge check must be an object: {item!r}")
        if item.get("kind") != kind or item.get("criterion") != criterion:
            raise ValueError(
                f"Judge check mismatch: expected ({kind!r}, {criterion!r}), "
                f"got ({item.get('kind')!r}, {item.get('criterion')!r})"
            )
        passed = item.get("passed")
        if not isinstance(passed, bool):
            raise ValueError(f"Judge check 'passed' must be a boolean: {passed!r}")
        reason = item.get("reason", "")
        if not isinstance(reason, str):
            reason = str(reason)
        checks.append(
            CheckResult(
                name=kind,
                passed=passed,
                detail=f"{criterion} ({reason})",
            )
        )

    return EvalResult(
        case_id=CASE_ID,
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def request_judge(prompt: str) -> str:
    config = load_config()
    client = anthropic.Anthropic(
        api_key=config["OPENCODE_API_KEY"],
        base_url=config["LLM_BASE_URL"],
        default_headers={"x-opencode-session": SESSION_ID},
    )
    response = client.messages.create(
        model=config["LLM_MODEL"],
        max_tokens=JUDGE_MAX_TOKENS,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    if not answer:
        raise RuntimeError("Judge returned an empty response")
    return answer


def evaluate(response: str, case: dict[str, Any]) -> EvalResult:
    if case.get("id") != CASE_ID:
        raise ValueError(
            f"Semantic judge only supports {CASE_ID!r}, got {case.get('id')!r}."
        )

    question = case["question"]
    expected = case["expected"]
    forbidden = case["forbidden"]

    context = None
    if "relevant_rules" in case:
        rules = resolve_rules(case["relevant_rules"])
        context = build_context(rules)

    prompt = _build_judge_prompt(question, response, expected, forbidden, context)
    raw = request_judge(prompt)
    return _parse_judge_output(raw, expected, forbidden)
