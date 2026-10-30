# RelayPay Support Evals

A small learning project for evaluating an LLM-assisted customer support component in a fictional payments app.

## What this project is

RelayPay is a fictional app for fast, private payments between people.

The planned component uses RelayPay documentation and an LLM to prepare suggested responses for customer support staff.

This project focuses on evaluating that component rather than building a complete support product.

## Current state

The project currently defines the two things needed before running an LLM evaluation:

1. **Ground truth** — explicit product rules and support policies that define what a correct response may rely on.
2. **Golden dataset** — a small set of realistic customer questions with criteria describing expected and forbidden behavior.

There is no LLM integration, retrieval pipeline, or executable eval runner yet.

This is intentional: the project first defines what "correct" means, then builds the system that will be evaluated.

## Repository structure

```text
relaypay-support-evals/
├── data/
│   └── golden_cases.yaml
├── knowledge/
│   ├── product-rules.md
│   └── support-policy.md
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

Contains the basic Python project metadata and supported Python version. The project has no runtime dependencies yet.

## Evaluation model

The planned evaluation flow is:

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

Retrieval selects relevant knowledge for the question. The LLM uses that context to generate a response. Together, retrieval and generation form the small RAG pipeline used by the project.

Test oracles then decide whether the response satisfies the evaluation criteria.

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

Build the smallest executable evaluation path:

```text
one golden case
→ relevant knowledge
→ one LLM response
→ one simple oracle
→ one evaluation result
```

The first implementation should stay intentionally small and make each part of that flow easy to understand.
