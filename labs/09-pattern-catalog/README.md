# Lab 09: Pattern Catalog

This dependency-free lab turns seven observed architecture patterns into a
machine-verifiable catalog.

The human-facing Markdown cards are paired with canonical JSON manifests.
Validation covers:

- maturity and portability as separate fields;
- required context, forces, decisions and implementation guidance;
- observable contracts and failure modes;
- at least one pinned primary source and executable lab reference per claim;
- counterexamples and explicitly rejected decisions;
- ADK version scope;
- cross-pattern relations and decision-boundary coverage;
- Markdown heading, status, portability and claim-ID synchronization.

## Deliberate Breakages

Twelve mutation fixtures cover:

- missing source/lab evidence type;
- dangling evidence ID;
- invalid maturity status;
- unpinned source URL;
- full-length source commit absent from the upstream lock;
- GitHub repository absent from the upstream lock;
- missing counterexample field;
- missing lab evidence file;
- absent rejected decision;
- unknown relation target;
- duplicate catalog entry;
- version-specific pattern without a validated version.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_pattern_gate.py --variant baseline
! python3 scripts/run_pattern_gate.py --variant broken
python3 scripts/run_pattern_traces.py
```

From the repository root:

```bash
make verify-pattern-catalog
```

## Limits

The stdlib validator implements the repository's contract directly and checks
that required fields match the published JSON Schemas. It is not a general
JSON Schema engine. Pattern status means validated by the pinned source and
local labs; it does not claim live production validation.
