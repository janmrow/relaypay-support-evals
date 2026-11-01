from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    checks: list[CheckResult]
