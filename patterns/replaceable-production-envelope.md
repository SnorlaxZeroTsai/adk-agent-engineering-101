# Replaceable Production Envelope

Status: candidate pattern, observed in Phase 8 offline production experiments.

## Problem

Generated projects often mix Agent code, environment values, secrets,
infrastructure, telemetry and deployment commands. A target change then forks
Agent behavior, while a successful deploy leaves too little evidence to
promote or roll back safely.

## Context

Use this pattern when one Agent must move between local, staging and one or
more production targets without changing its behavior contract.

## Architecture

```text
target-independent Agent source contract
  + target-independent behavior gate
  + runtime config and secret references
  + replaceable deployment-target adapter
  + explicit telemetry policy
  -> immutable release candidate
  -> append-only release record
  -> target-native promote/rollback action
```

The envelope defines shared evidence. The adapter owns actual platform
capabilities.

## Invariants

- Agent source and behavior expectations do not fork by deployment target.
- Plain configuration contains no secret material.
- Remote secrets reference a provider ID and immutable version.
- Remote state services and runtime identity are explicit.
- Telemetry content destinations, retention and approval are explicit.
- Artifact reference binds an immutable digest.
- Production uses the artifact and behavior report tested in staging.
- Every production release points to a prior recoverable release.
- Release history is append-only.
- Rollback uses the target's real capability, not a lowest-common-denominator
  fiction.

## Forces

- More typed metadata than a single manifest or deploy command.
- Clear ownership and smaller target-specific diffs.
- A release ledger and artifact retention become production dependencies.
- Strict drift detection may interrupt convenient imperative changes.
- Agent Runtime needs redeploy orchestration because it lacks revision traffic
  rollback.

## Implementation

1. Hash Agent source independently of deployment files.
2. Run the behavior gate and retain report ID plus digest.
3. Separate plain env from secret references.
4. Declare Session, artifact, memory and identity bindings.
5. Render runtime and target specs as independently owned artifacts.
6. Build or package one immutable artifact.
7. Record spec, source, artifact and behavior digests.
8. Promote the exact staging evidence to production.
9. Detect live drift before merge-style updates.
10. Append the successful platform resource/revision and previous release.
11. Generate a target-specific rollback plan.
12. Exercise restore procedures independently from normal deploy.

## Failure Modes

- Target-specific conditional branches inside Agent business logic.
- `.env` copied to production with API keys as plain values.
- Secret reference uses mutable `latest` during a release.
- Version tag or `latest` used without an artifact digest.
- Terraform and imperative deploy both own the same resource.
- Live out-of-band values silently inherited on update.
- Trace content disabled while full completion uploads remain enabled.
- Current resource ID mistaken for release history.
- Production rebuilds instead of promoting the tested artifact.
- Universal rollback API hides a target that only supports redeploy.
- Previous artifact garbage-collected before rollback testing.

## Counterexamples

Do not build a release ledger for a disposable local tutorial that has no
remote state or users.

Do not force every target through one deployment implementation. Standardize
evidence and policy, then keep target-native operations replaceable.

## Trade-Offs

- Stronger audit, promotion and recovery evidence.
- Easier replacement of deployment tooling.
- More artifact storage and metadata lifecycle work.
- Explicit tension between declarative desired state and imperative deploy.
- Recovery quality depends on state/data migration compatibility, not only
  application artifact rollback.

## Evidence

Lab 08 observed:

- local, Cloud Run and Agent Runtime retained the same Agent and behavior
  artifacts;
- only runtime/deployment/manifest/release files changed by target;
- staging and production shared artifact and behavior digests;
- Cloud Run used revision traffic shift;
- Agent Runtime required restore-and-redeploy orchestration;
- eight deliberate lifecycle failures produced 23 blocking reasons;
- mutable current-resource metadata failed the rollback contract.

## Sources

- Starter Pack template layering, upgrade and generated CI workflows
- Agents CLI project manifest, scaffold layering and three-way merge
- Agents CLI deploy env/secret/update and operation metadata code
- Agents CLI deployment and observability skills
- [`../docs/production/production-engineering.md`](../docs/production/production-engineering.md)
- [`../labs/08-production-engineering`](../labs/08-production-engineering/)
