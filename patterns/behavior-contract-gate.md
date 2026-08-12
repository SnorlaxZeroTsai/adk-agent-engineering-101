# Behavior Contract Gate

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/behavior-contract-gate.json`](manifests/behavior-contract-gate.json).

## Problem

An Agent can receive a high response-quality score while violating tool, state,
authorization, retrieval, trajectory or cost contracts. Averages can also hide
one critical failed case.

## Context

Use this pattern when a release has observable behavior that must hold
independently of model fluency.

## Forces

- Deterministic metrics require precise owned expectations.
- Judge metrics cover semantic quality but are probabilistic.
- Full traces improve diagnosis while increasing retention and privacy burden.
- Exact trajectory checks can become brittle when several paths are valid.

## Decision

Separate versioned dataset, generated runtime evidence and grade report.
Require complete case identity and per-case deterministic blockers. Keep judge
metrics advisory until their calibration and failure policy are explicit.

## Architecture

```text
EvalDataset
  -> complete TraceSet
  -> deterministic contract metrics
  -> separately identified judge metrics
  -> per-case blocking policy
  -> aggregate reporting
  -> CI exit status
```

## Observable Contract

| ID | Contract |
|---|---|
| `case-completeness` | Generated trace IDs exactly match the input dataset. |
| `per-case-blocking` | Every applicable deterministic metric passes per case. |
| `stage-separation` | Dataset, trace and grade remain distinct serializable artifacts. |
| `enforceable-exit` | Baseline exits zero and deliberate breakage exits nonzero. |

## When To Use

- owned tool arguments, state or trajectory define correctness;
- safety or authorization failures must never be averaged away;
- retrieval and citation need independent evidence;
- CI must enforce a release decision.

## When Not To Use

- an exact trajectory is not owned and several paths are intentionally valid;
- a probabilistic judge has no calibration or deterministic critical fallback;
- the asserted detail is unstable prompt wording rather than product behavior.

## Implementation

1. Version case identity and expected behavior.
2. Generate evidence without assigning a verdict.
3. Preserve tool, trajectory, state, error, policy and domain fields.
4. Run deterministic metrics before optional judges.
5. Treat missing required evidence as failure.
6. Preserve per-case failures in aggregate reports.
7. Return a nonzero process status for broken release behavior.

## Failure Modes

| ID | Failure |
|---|---|
| `mean-masks-case` | One critical failure is compensated by other scores. |
| `partial-generation-passes` | Failed inference cases disappear before grading. |
| `judge-overrides-contract` | Fluent text overrides tool, state, policy or retrieval failure. |
| `diff-without-policy` | Numeric comparison has no blocking release decision. |

## Counterexamples

Evaluate stable state/effect outcomes rather than exact trajectories when paths
are intentionally equivalent. Keep uncalibrated judges advisory.

## ADK Versions

- ADK 2.6.3 Event and Session evidence is validated across six architectures.
- Agents CLI at the pinned commit is comparative lifecycle evidence for
  dataset, generate, grade and compare stages.

## Evidence

- Source and claim-level links:
  [`manifests/behavior-contract-gate.json`](manifests/behavior-contract-gate.json)
- Architecture analysis:
  [`../docs/evaluation/evaluation-engineering.md`](../docs/evaluation/evaluation-engineering.md)
- Executable evidence:
  [`../labs/06-evaluation`](../labs/06-evaluation/)

## Rejected Decisions

`single-aggregate-score`: reject using one response-quality mean as the release
gate. Preserve per-case deterministic blockers and report aggregate/judge
metrics separately.
