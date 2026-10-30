from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import anthropic
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_PATH = PROJECT_ROOT / "data" / "golden_cases.yaml"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
ENV_PATH = PROJECT_ROOT / ".env"

SESSION_ID = "relaypay-support-evals"
MAX_TOKENS = 512

SYSTEM_PROMPT = """\
You draft one suggested reply for RelayPay customer support staff.
Use only the RelayPay rules provided in the context.
Do not invent facts, policies, timelines, fees, or account details.
Do not suggest actions or features that are not described in the context.
If the context does not contain enough information to answer, say clearly what \
cannot be answered from the available documentation.
Return only the suggested reply."""

RULE_HEADING = re.compile(r"^###\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\s+[—–-]\s+.+$")
ANY_HEADING = re.compile(r"^#+\s+")


def load_cases(cases_path: Path = CASES_PATH) -> list[dict[str, Any]]:
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError(f"{cases_path} must contain a YAML list of cases")
    return cases


def find_case(case_id: str, cases_path: Path = CASES_PATH) -> dict[str, Any]:
    cases = load_cases(cases_path)
    for case in cases:
        if isinstance(case, dict) and case.get("id") == case_id:
            return case

    available = ", ".join(
        str(case.get("id")) for case in cases if isinstance(case, dict)
    )
    raise ValueError(f"Unknown case {case_id!r}. Available cases: {available}")


def load_rule_texts(knowledge_dir: Path = KNOWLEDGE_DIR) -> dict[str, str]:
    rules: dict[str, str] = {}
    sources: dict[str, Path] = {}

    for path in sorted(knowledge_dir.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        starts = [
            (index, match.group(1))
            for index, line in enumerate(lines)
            if (match := RULE_HEADING.match(line))
        ]

        for start, rule_id in starts:
            end = len(lines)
            for index in range(start + 1, len(lines)):
                if ANY_HEADING.match(lines[index]):
                    end = index
                    break

            if rule_id in rules:
                raise ValueError(
                    f"Duplicate rule ID {rule_id!r} "
                    f"in {sources[rule_id]} and {path}"
                )

            rules[rule_id] = "\n".join(lines[start:end]).strip()
            sources[rule_id] = path

    return rules


def resolve_rules(
    rule_ids: list[str], knowledge_dir: Path = KNOWLEDGE_DIR
) -> list[tuple[str, str]]:
    rule_texts = load_rule_texts(knowledge_dir)
    missing = [rule_id for rule_id in rule_ids if rule_id not in rule_texts]
    if missing:
        raise ValueError(f"Unknown rule ID(s): {', '.join(missing)}")

    return [(rule_id, rule_texts[rule_id]) for rule_id in rule_ids]


def build_context(rules: list[tuple[str, str]]) -> str:
    return "\n\n".join(text for _, text in rules)


def build_user_message(question: str, context: str) -> str:
    return f"RelayPay rules:\n\n{context}\n\nCustomer question:\n{question}"


def load_config() -> dict[str, str]:
    load_dotenv(ENV_PATH)

    names = ("OPENCODE_API_KEY", "LLM_MODEL", "LLM_BASE_URL")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            f"Missing configuration: {', '.join(missing)}. "
            f"Set it in the environment or in {ENV_PATH}."
        )

    return {name: os.environ[name] for name in names}


def generate(case_id: str) -> tuple[dict[str, Any], list[tuple[str, str]], str]:
    config = load_config()
    case = find_case(case_id)
    rules = resolve_rules(case["relevant_rules"])
    user_message = build_user_message(case["question"], build_context(rules))
    return case, rules, request_llm(user_message, config)


def request_llm(user_message: str, config: dict[str, str]) -> str:
    client = anthropic.Anthropic(
        api_key=config["OPENCODE_API_KEY"],
        base_url=config["LLM_BASE_URL"],
        default_headers={"x-opencode-session": SESSION_ID},
    )
    response = client.messages.create(
        model=config["LLM_MODEL"],
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    answer = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    if not answer:
        raise RuntimeError("LLM returned an empty response")
    return answer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate one support response for a RelayPay golden case."
    )
    parser.add_argument("--case", required=True, help="Golden case ID")
    args = parser.parse_args(argv)

    try:
        case, rules, answer = generate(args.case)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
