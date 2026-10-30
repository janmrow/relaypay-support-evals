# RelayPay Support Evals

A small learning project for evaluating an LLM-assisted customer support component in a fictional payments app.

## What this project is

RelayPay is a fictional app for fast, private payments between people.

The component uses RelayPay documentation and an LLM to prepare suggested responses for customer support staff.

This project focuses on evaluating that component rather than building a complete support product.

## Current state

The project defines the ground truth and golden dataset, and can now generate one LLM response for a single golden case using a known-good context.

The generator loads a case by ID, reads the rules listed in `relevant_rules` directly from `knowledge/`, and sends the customer question plus those rule texts to Claude Haiku 5.5 through OpenCode Console (pay-as-you-go; Go is meant for coding-agent traffic).

Retrieval and evaluation are not implemented yet. There is no automatic rule selection, test oracle, scoring, or eval runner for the whole dataset.

This is intentional: generation is tested first with known-good context so that generation failures can be understood separately from retrieval failures.

## Repository structure

```text
relaypay-support-evals/
├── data/
│   └── golden_cases.yaml
├── knowledge/
│   ├── product-rules.md
│   └── support-policy.md
├── relaypay_support_evals/
│   ├── __init__.py
│   └── generate.py
├── tests/
│   └── test_generate.py
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

### `knowledge/product-rules.md`

Defines how RelayPay works: transfer states, cancellation rules, payment requests, and fees.

These are product facts, not instructions for support staff or the LLM.

### `knowledge/support-policy.md`

Defines how RelayPay support should handle customer cases, including identity verification, security, and fraud escalation.

Keeping support behavior separate from product behavior makes the source of each rule explicit.

### `data/golden_cases.yaml`

Contains the initial evaluation dataset.

Each case defines a customer question, relevant rules, expected behavior, and forbidden behavior.

There is intentionally no single expected response. LLM output is nondeterministic, so different answers may be valid as long as they satisfy the same evaluation criteria.

### `pyproject.toml`

Contains the Python project metadata, supported Python version, and runtime dependencies: `anthropic`, `PyYAML`, and `python-dotenv`.

## Generate a response for one golden case

Create a local `.env` from `.env.example` and set `OPENCODE_API_KEY`:

```bash
cp .env.example .env
```

`LLM_MODEL` and `LLM_BASE_URL` are already set for OpenCode Console. The `.env` file is gitignored. Use a personal Console API key for `OPENCODE_API_KEY`.

Run one existing case:

```bash
uv run python -m relaypay_support_evals.generate --case transfer_pending_01
```

The command prints the case ID, the rule IDs used, and the model's response. It makes one real LLM request.

Run the deterministic tests:

```bash
uv run python -m unittest discover -s tests -v
```

The tests do not make LLM requests.

## Evaluation model

The full evaluation flow will be:

```text
customer question
       ↓
   retrieval  ←  RelayPay knowledge
       ↓
retrieved context
       ↓
      LLM
       ↓
    response
       ↓
 test oracles  ←  golden case criteria
       ↓
   eval result
```

Retrieval selects relevant knowledge for the question. The LLM uses that context to generate a response. Together, retrieval and generation will form the small RAG pipeline used by the project.

At this stage, `relevant_rules` in each golden case provides the known-good context directly, so generation can be tested without retrieval.

Retrieval and test oracles are separate future steps: retrieval will select knowledge automatically, while test oracles will evaluate whether the generated response satisfies the golden case criteria.

## Key concepts

| Concept | Meaning in this project |
| --- | --- |
| **Ground truth** | The product facts and support rules used as the reference for correctness. |
| **Golden dataset** | Curated customer cases used repeatedly to evaluate the system. |
| **Retrieval** | Selecting relevant RelayPay knowledge for a customer question. |
| **RAG** | Generating an answer using knowledge retrieved from an external source. |
| **Test oracle** | The mechanism or criteria used to decide whether a response is acceptable. |
| **Eval** | Running evaluation cases and measuring how well the system behaves. |
| **Hallucination** | A claim produced by the model that is not supported by the available knowledge. |

## Next step

The current executable path is:

```text
one golden case
→ known-good context from relevant_rules
→ one LLM response
```

The next step is to evaluate that response while keeping the context fixed:

```text
one golden case
→ known-good context
→ one LLM response
→ one simple oracle
→ one evaluation result
```

Retrieval will be added later, after generation and evaluation can be understood independently.

The implementation should stay intentionally small and make each part of the flow easy to understand.
