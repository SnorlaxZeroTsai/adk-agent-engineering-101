# Behavior Contract Gate

Status: candidate pattern, observed through Phase 7 local/scripted experiments.

## Problem

An Agent can receive a high response-quality score while violating a tool,
state, authorization, retrieval or cost contract. Aggregate scores can also
hide one critical failed case.

## Context

Use this pattern when an Agent release has observable behaviors that must hold
independently of model fluency.

## Architecture

```text
versioned EvalDataset
  -> generate complete TraceSet
  -> deterministic contract metrics
  -> separately identified judge metrics
  -> per-case blocking policy
  -> aggregate reporting
  -> CI exit status
```

Dataset, trace and grade result remain distinct artifacts.

## Invariants

- Generated case IDs exactly match the input dataset.
- Required blocking metrics cannot be `NOT_EVALUATED`.
- Critical metrics pass for every applicable case.
- Judge model, sampling and threshold have explicit provenance.
- An aggregate pass never deletes a failed per-case result.
- The final report maps to an enforceable process status.

## Forces

- Strict deterministic gates catch architectural regressions but require
  precise expected behavior.
- Judge metrics cover semantic quality but are noisy and model-dependent.
- Full traces improve diagnosis but increase retention and privacy burden.
- Per-case gates reduce masking but can become brittle if they assert
  irrelevant implementation details.
- Partial trace generation helps debugging but needs a completeness check.

## Implementation

1. Version stable case identity and expected behavior.
2. Generate runtime evidence without assigning a verdict.
3. Preserve tool arguments, trajectory, state, errors and domain evidence.
4. Run deterministic metrics before optional judges.
5. Mark safety, authorization, side-effect and terminal-state metrics
   `all_cases`.
6. Use means only where compensation is intentionally acceptable.
7. Emit expected, observed and reason for each failure.
8. Fail closed when required evidence is absent.
9. Make the broken reference variant return nonzero in CI.

## Failure Modes

- Grading only final text.
- Using one mean across critical cases.
- Dropping failed inference cases before grading.
- Treating `NOT_EVALUATED` as pass.
- Running judge and deterministic results under one unlabeled score.
- Comparing result files without a regression policy.
- Executing untrusted custom metric code in the CI process.
- Asserting unstable prompt wording instead of owned behavior.

## Counterexamples

Do not require an exact trajectory when multiple paths are intentionally
equivalent and side-effect/state contracts are sufficient.

Do not make a probabilistic judge blocking without calibration, sampling,
failure review and a deterministic fallback for critical policy.

## Trade-Offs

- More dataset and normalization code.
- Stronger failure ownership and release confidence.
- More explicit migration work when architecture changes.
- Higher trace storage and privacy requirements.
- Ability to change thresholds without re-running inference when evidence is
  sufficient.

## Evidence

Lab 06 observed:

- six baseline architecture cases passed;
- all six deliberate breakages failed;
- broken CLI exited `1`;
- scripted judge mean `13/3` passed while deterministic release failed;
- cross-user memory leakage failed only the policy metric;
- provenance loss failed retrieval/citation despite a correct fact;
- two renders of the 90,166-byte bundle were byte-identical.

## Sources

- ADK `EvalCase`, `EvalSet`, `LocalEvalService` and `TrajectoryEvaluator`
- Agents CLI `eval generate`, `grade`, `compare` and `_paths`
- [`../docs/evaluation/evaluation-engineering.md`](../docs/evaluation/evaluation-engineering.md)
- [`../labs/06-evaluation`](../labs/06-evaluation/)
