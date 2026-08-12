# Lab 08: Production Engineering

This dependency-free lab holds one Agent source and one behavior report
constant while rendering three replaceable runtime targets:

- local development;
- Cloud Run;
- Agent Runtime.

The render is structured data rather than a cloud deployment. It separates:

- Agent source contract;
- behavior gate evidence;
- runtime configuration and secret references;
- deployment topology and identity;
- lifecycle manifest;
- derived release candidate.

## Production Contract

Every remote release must bind:

- a full source commit and source digest;
- an immutable artifact reference and digest;
- a passing behavior report and digest;
- explicit runtime services and identity;
- privacy-aware telemetry policy;
- an append-only previous-release and promotion chain.

Cloud Run uses revision traffic shifting. Agent Runtime has no native
revision rollback in the pinned tooling, so an application-owned release
orchestrator restores a prior source bundle and redeploys it. These strategies
share release evidence, not a fictional common platform command.

## Intentional Breakages

The broken suite injects:

- a plaintext API key in `.env`-style configuration;
- full content telemetry without approval or retention;
- a failed/missing behavior report;
- a mutable `latest` artifact;
- Agent Runtime with Cloud Run artifact and rollback semantics;
- an out-of-band environment value preserved by a merge update;
- current-resource metadata without release history;
- orphaned promotion and rollback references.

## Run

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_production_gate.py --variant baseline
! python3 scripts/run_production_gate.py --variant broken
python3 scripts/run_production_traces.py
```

From the repository root:

```bash
make verify-production
```

## Limits

The lab does not call Google Cloud, build a real container, authenticate a
service account, execute Terraform, shift real traffic or prove datastore
migrations. Those remain environment-specific integration and recovery gates.
