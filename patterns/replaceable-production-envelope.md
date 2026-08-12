# Replaceable Production Envelope

Status: `validated`.

Portability: `portable`.

Canonical manifest:
[`manifests/replaceable-production-envelope.json`](manifests/replaceable-production-envelope.json).

## Problem

Generated projects often mix Agent code, environment values, secrets,
infrastructure, telemetry and deploy commands. A target change then forks Agent
behavior while a successful deploy leaves too little recovery evidence.

## Context

Use this pattern when one Agent must move through local, staging and one or
more production targets without changing its behavior contract.

## Forces

- Typed lifecycle artifacts cost more than one manifest.
- Strict drift detection interrupts convenient imperative changes.
- Artifact retention and release history become production dependencies.
- Platform rollback capabilities differ.

## Decision

Separate target-independent Agent and behavior contracts from runtime config,
secret references, deployment spec and release history. Promote exact tested
evidence and keep rollback execution target-native.

## Architecture

```text
Agent source contract + behavior gate
  + runtime config and secret refs
  + replaceable target adapter
  + telemetry policy
  -> immutable release candidate
  -> append-only release record
  -> target-native promote/rollback
```

## Observable Contract

| ID | Contract |
|---|---|
| `target-independent-behavior` | Target changes leave Agent and behavior artifacts byte-equivalent. |
| `secret-and-drift-boundary` | Remote config uses secret refs and blocks unmanaged live drift. |
| `telemetry-content-separation` | Trace content and full completion capture have separate governance. |
| `immutable-release-history` | Production binds tested artifact, behavior report, prior release and rollback action. |

## When To Use

- one Agent targets multiple environments or platforms;
- secrets, identity and durable services need explicit owners;
- staging promotion must preserve exact artifacts and behavior evidence;
- rollback and telemetry privacy are release requirements.

## When Not To Use

- a disposable local tutorial has no remote users or retained state;
- a universal deploy implementation would hide target capabilities;
- no artifact or prior release is retained for recovery.

## Implementation

1. Hash Agent source independently from deployment files.
2. Retain the behavior report ID and digest.
3. Separate plain env from pinned secret references.
4. Declare Session, artifact, memory and identity bindings.
5. Render target-owned runtime and deployment specs.
6. Build one immutable artifact.
7. Detect live drift before update.
8. Promote exact staging evidence.
9. Append successful platform and previous-release evidence.
10. Generate and exercise a target-specific rollback plan.

## Failure Modes

| ID | Failure |
|---|---|
| `plain-env-secret` | Secret material travels through ordinary `.env` configuration. |
| `silent-live-drift` | Merge update retains an unreviewed out-of-band value. |
| `current-metadata-as-ledger` | Current resource ID is mistaken for release history. |
| `universal-rollback-fiction` | One generic command hides restore-and-redeploy targets. |

## Counterexamples

Use the minimal local run path for a disposable tutorial. Share evidence and
policy across real targets, but keep target-native adapters separate.

## ADK Versions

- Agents CLI at `5a306f8` is validated as current lifecycle source evidence.
- Agent Starter Pack at `659f047` remains comparative rendered-project
  evidence.

## Evidence

- Source and claim-level links:
  [`manifests/replaceable-production-envelope.json`](manifests/replaceable-production-envelope.json)
- Architecture analysis:
  [`../docs/production/production-engineering.md`](../docs/production/production-engineering.md)
- Executable evidence:
  [`../labs/08-production-engineering`](../labs/08-production-engineering/)

## Rejected Decisions

`deploy-success-as-release-proof`: reject treating a successful deploy and
current resource ID as enough for promotion and rollback. Append immutable
source, artifact, behavior, platform and previous-release evidence.
