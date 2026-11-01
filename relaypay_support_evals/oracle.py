"""First case-specific deterministic oracle.

Checks surface-level properties of responses for `fees_conversion_01`.
It intentionally does not perform semantic evaluation; broader paraphrase
handling belongs to a future semantic or LLM-based judge.
"""

from __future__ import annotations

import re

from relaypay_support_evals.results import CheckResult, EvalResult


CASE_ID = "fees_conversion_01"

_FEE_2_EUR = re.compile(r"\b2\s*(eur|€|euros?)\b", re.IGNORECASE)
_REMAINING_198_EUR = re.compile(r"\b198\s*(eur|€|euros?)\b", re.IGNORECASE)

_UNKNOWN_MARKERS = (
    "cannot be determined",
    "can't be determined",
    "cannot determine",
    "can't determine",
    "can not determine",
    "not determin",
    "unknown",
    "no exchange rate",
    "no rate",
    "not provided",
    # Paraphrases of "unknown / not available"; kept small on purpose.
    "can't give",
    "cannot give",
    "unable to give",
    "doesn't include",
    "does not include",
)

_USD_AMOUNT = re.compile(r"\$\s*\d", re.IGNORECASE)
_NUMBER_BEFORE_USD = re.compile(
    r"\b\d[\d\s,]*(\.\d+)?\s*(usd|us\s*dollars?|dollars?)\b", re.IGNORECASE
)
_USD_BEFORE_NUMBER = re.compile(
    r"\b(usd|dollars?)\s*(is|of|=|:)?\s*\d", re.IGNORECASE
)
_EXCHANGE_RATE_VALUE = re.compile(
    r"\b1\s*(eur|€)\s*=\s*\d", re.IGNORECASE
)
_WRONG_FEE_MODEL = re.compile(r"\bflat\s+fee\b|\bspread\b", re.IGNORECASE)
_BEFORE_CONFIRM = re.compile(r"before\s+(you\s+)?confirm", re.IGNORECASE)


def _check_fee_is_2_eur(response: str) -> CheckResult:
    passed = bool(_FEE_2_EUR.search(response))
    return CheckResult(
        name="states_fee_2_eur",
        passed=passed,
        detail="Response states the conversion fee is 2 EUR."
        if passed
        else "Response does not state the conversion fee is 2 EUR.",
    )


def _check_remaining_198_eur(response: str) -> CheckResult:
    passed = bool(_REMAINING_198_EUR.search(response))
    return CheckResult(
        name="states_198_eur_remains",
        passed=passed,
        detail="Response states that 198 EUR remains to be converted."
        if passed
        else "Response does not state that 198 EUR remains to be converted.",
    )


def _check_usd_unknown(response: str) -> CheckResult:
    lowered = response.lower().replace("’", "'")
    passed = "usd" in lowered and any(
        marker in lowered for marker in _UNKNOWN_MARKERS
    )
    return CheckResult(
        name="states_usd_amount_unknown",
        passed=passed,
        detail="Response states the exact USD amount cannot be determined."
        if passed
        else "Response does not state that the exact USD amount is unknown.",
    )


def _check_shown_before_confirmation(response: str) -> CheckResult:
    lowered = response.lower()
    passed = bool(_BEFORE_CONFIRM.search(response)) and (
        "shown" in lowered or "displayed" in lowered
    )
    return CheckResult(
        name="states_shown_before_confirmation",
        passed=passed,
        detail="Response states the fee and final amount are shown "
        "before confirmation."
        if passed
        else "Response does not state the amounts are shown "
        "before confirmation.",
    )


def _check_no_hallucinated_usd(response: str) -> CheckResult:
    hallucinated = (
        _USD_AMOUNT.search(response)
        or _NUMBER_BEFORE_USD.search(response)
        or _USD_BEFORE_NUMBER.search(response)
        or _EXCHANGE_RATE_VALUE.search(response)
    )
    passed = hallucinated is None
    return CheckResult(
        name="no_hallucinated_usd_amount",
        passed=passed,
        detail="Response does not invent a specific USD amount or rate."
        if passed
        else "Response states a specific USD amount or exchange rate.",
    )


def _check_no_wrong_fee_model(response: str) -> CheckResult:
    passed = _WRONG_FEE_MODEL.search(response) is None
    return CheckResult(
        name="no_flat_fee_or_spread",
        passed=passed,
        detail="Response does not describe the fee as flat or spread."
        if passed
        else "Response wrongly describes the fee as flat or spread.",
    )


def evaluate_fees_conversion_01(response: str) -> EvalResult:
    checks = [
        _check_fee_is_2_eur(response),
        _check_remaining_198_eur(response),
        _check_usd_unknown(response),
        _check_shown_before_confirmation(response),
        _check_no_hallucinated_usd(response),
        _check_no_wrong_fee_model(response),
    ]
    return EvalResult(
        case_id=CASE_ID,
        passed=all(check.passed for check in checks),
        checks=checks,
    )


def assert_supported(case_id: str) -> None:
    if case_id != CASE_ID:
        raise ValueError(
            f"Unsupported case {case_id!r}. "
            f"First oracle only supports {CASE_ID!r}."
        )


def evaluate(response: str, case_id: str = CASE_ID) -> EvalResult:
    assert_supported(case_id)
    return evaluate_fees_conversion_01(response)
