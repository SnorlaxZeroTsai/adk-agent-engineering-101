# Evidence-Preserving RAG

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/evidence-preserving-rag.json`](manifests/evidence-preserving-rag.json).

## Problem

A plausible answer can hide unauthorized, stale, deleted or uncitable
retrieval. Response-only evaluation cannot distinguish those failures.

## Context

Use this pattern when an Agent answers from managed Search, Vector Search or a
custom index and source lifecycle or citation integrity matters.

## Forces

- Managed services reduce ingestion code but hide some reconciliation behavior.
- Explicit pipelines increase control and operational responsibility.
- Structured provenance increases payload size but enables audit and deletion.

## Decision

Apply trusted authorization before ranking, preserve source identity through
generation, reconcile source lifecycle explicitly, and evaluate retrieval,
answer and citations separately.

## Architecture

```text
versioned source + ACL
  -> ingestion + reconciliation + deletion
  -> ACL filter before rank/top-k
  -> structured source/version/chunk/URI hits
  -> evidence-bound answer and citations
  -> independent retrieval/lifecycle/answer/citation gates
```

## Observable Contract

| ID | Contract |
|---|---|
| `provenance-survives` | Every model-visible hit retains document, version, chunk, locator and authorization identity. |
| `acl-before-ranking` | Trusted principal filters run before ranking and top-k. |
| `lifecycle-reconciliation` | Obsolete versions and deleted sources disappear after reconciliation. |
| `separate-grounding-gates` | Retrieval, answer, citation and abstention receive independent verdicts. |

## When To Use

- answers depend on a changing document corpus;
- users need citations or audit evidence;
- ACL, version and deletion rules apply;
- managed and explicit backends must be compared under one contract.

## When Not To Use

- a small current lookup belongs in a database or API;
- static bounded context is sufficient;
- provenance has no product or policy value.

## Implementation

1. Version source, parser, chunker and index schema.
2. Assign deterministic source and chunk IDs.
3. Apply access filters before ranking.
4. Return structured hits rather than anonymous text.
5. Require no-hit abstention.
6. Cite only current retrieval-response identities.
7. Reconcile obsolete versions and deletions.
8. Gate retrieval and citation independently from final text.

## Failure Modes

| ID | Failure |
|---|---|
| `prompt-only-acl` | Authorization is prompt text or a post-top-k filter. |
| `anonymous-chunk-text` | Formatted chunks lose source identity and become uncitable. |
| `create-only-ingestion` | Old versions or deleted chunks remain searchable. |
| `response-only-eval` | A generic judge accepts text despite invalid retrieval evidence. |

## Counterexamples

Use a transactional tool for deterministic current records. Do not introduce a
vector index merely because a payload is large; artifact placement may be the
correct lifecycle.

## ADK Versions

- ADK 2.6.3 native Search and explicit FunctionTool trajectories are validated.
- Live provider relevance, deletion propagation, latency and cost remain
  backend-specific gates.

## Evidence

- Source and claim-level links:
  [`manifests/evidence-preserving-rag.json`](manifests/evidence-preserving-rag.json)
- Architecture analysis:
  [`../docs/rag/rag-engineering.md`](../docs/rag/rag-engineering.md)
- Executable evidence:
  [`../labs/05-rag-engineering`](../labs/05-rag-engineering/)

## Rejected Decisions

`citation-format-as-provenance`: reject accepting a citation-looking URL as
proof of grounded retrieval. Bind citations to exact structured hits from the
current invocation.
