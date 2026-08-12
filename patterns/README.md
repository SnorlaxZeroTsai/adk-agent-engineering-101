# Pattern Catalog

The catalog has two synchronized surfaces:

- [`catalog.json`](catalog.json) and
  [`manifests/`](manifests/) are the canonical machine contract.
- The Markdown cards are the human-facing architecture explanation.

Published schemas:

- [`schema/pattern.schema.json`](schema/pattern.schema.json)
- [`schema/catalog.schema.json`](schema/catalog.schema.json)

## Status Semantics

`status` and `portability` are independent:

| Field | Values | Meaning |
|---|---|---|
| `status` | `candidate`, `validated`, `rejected` | evidence maturity |
| `portability` | `portable`, `version-specific` | implementation scope |

`validated` means the pattern has pinned source evidence, an executable local
implementation, an intentional failure and observable tests. It does not claim
live production validation.

## Current Catalog

| Pattern | Status | Portability | Evidence |
|---|---|---|---|
| [Deterministic Workflow](deterministic-workflow.md) | validated | portable | Lab 02 |
| [Bounded Specialist](bounded-specialist.md) | validated | version-specific | Lab 03 |
| [Data Lifecycle Placement](data-lifecycle-placement.md) | validated | portable | Lab 04 |
| [Evidence-Preserving RAG](evidence-preserving-rag.md) | validated | portable | Lab 05 |
| [Behavior Contract Gate](behavior-contract-gate.md) | validated | portable | Lab 06 |
| [Durable Approval Boundary](durable-approval-boundary.md) | validated | portable | Lab 07 |
| [Replaceable Production Envelope](replaceable-production-envelope.md) | validated | portable | Lab 08 |

Every observable contract and failure mode references at least one pinned
primary source and one executable lab artifact. Every pattern also includes a
counterexample and an explicitly rejected decision.

## Validation

```bash
make verify-pattern-catalog
```

The gate verifies manifests, Markdown synchronization, evidence paths,
relations and decision-boundary coverage. Twelve deliberate invalid mutations
must return a nonzero process status.

Architecture findings and overlap analysis:
[`../docs/patterns/pattern-catalog.md`](../docs/patterns/pattern-catalog.md).
