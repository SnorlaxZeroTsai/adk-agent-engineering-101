# Production Engineering: Replaceable Lifecycle Contracts

Research snapshot: 2026-08-12. Starter Pack conclusions are pinned to
`GoogleCloudPlatform/agent-starter-pack@659f047`; current lifecycle conclusions
are pinned to `google/agents-cli@5a306f8`.

## Question

A working Agent still needs configuration, identity, stateful services,
deployment, telemetry, promotion and recovery. The engineering question is:

> Which production concerns belong around the Agent, who owns each concern,
> and what evidence makes a release replaceable and recoverable?

## Hypothesis

> Production readiness is a set of independently owned lifecycle contracts
> around a stable Agent behavior contract. A template or deploy command can
> implement those contracts, but it cannot replace them.

## Two Generations of Tooling

### Starter Pack: Rendered Project Product

The maintenance-mode Starter Pack remains useful architecture evidence.
`process_template` composes, in order:

1. language-independent shared base;
2. language base;
3. deployment-target shared and language overlays;
4. agent-specific files;
5. optional frontend, ingestion and CI/CD assets.

Its generated project owns Terraform, CI workflows, tests, telemetry helpers
and target adapters as files in the application repository.

Upgrade and enhance use a three-way comparison between the current project,
the old template and the new template. Agent code and environment/config files
are special categories that are not overwritten. This is a strong project
evolution model, but it also means generated infrastructure becomes
application-owned source that teams must review and maintain.

The generated pipeline expresses a useful promotion intent:

```text
PR tests
  -> deploy staging
  -> load test
  -> production approval
  -> deploy production
```

The intent is stronger than a direct deploy. It is not, by itself, immutable
release evidence: some rendered Cloud Run commands reference an image without
a digest, and the workflow does not write an append-only release ledger.

### Agents CLI: Active Lifecycle Commands

Agents CLI retains the same base/language/target layering in its scaffold, but
splits operations into lifecycle commands:

```text
scaffold -> eval -> deploy -> publish -> observe
```

`agents-cli-manifest.yaml` records project/scaffold metadata such as target,
agent directory, region, session type and CI runner. It is not a complete
desired-state deployment schema:

- absent files fall back to defaults;
- a CLI target flag can override the manifest;
- scaffold/CLI version mismatch emits guidance rather than blocking;
- CPU, memory, env, secrets, identity and rollback are deploy-time concerns.

The manifest answers "what kind of project is this?" It does not prove "what
exact release is currently serving?"

## Deployment-Target Contracts

The active deploy command has three materially different ownership models.

| Concern | Cloud Run | Agent Runtime | GKE |
|---|---|---|---|
| Build input | source or prebuilt image | source package plus Dockerfile | source build or prebuilt image |
| Sizing | deploy flags | deploy flags and update field masks | Terraform/HPA |
| Secret binding | `--update-secrets` | structured secret env | Kubernetes/CSI outside common flag |
| Update behavior | merge-oriented `gcloud` flags | preserve live plain env and omit unspecified shape fields | imperative image/env update |
| Async status | platform async operation | local pending-operation metadata | not supported by common `--no-wait` path |
| Immediate rollback | revision traffic shift | no native revision rollback; redeploy | `kubectl rollout undo` |

This is why one generic "deployment config" is insufficient. A shared
interface can require artifact, identity, behavior and recovery evidence, but
the target adapter must own its real capabilities and limitations.

## Configuration and Secret Boundary

### Source Facts

The pinned deploy utilities read project `.env` values and copy them into the
remote runtime. Explicit `--update-env-vars` wins. Structured `--secrets`
values are separate and supported on Cloud Run and Agent Runtime.

For Agent Runtime:

- `GOOGLE_CLOUD_PROJECT` is filtered because the platform reserves it;
- telemetry defaults keep model content out of spans;
- an update reads the live deployment and re-adds existing plain env values
  not supplied by the new deploy;
- structured secret values are masked for display, while ordinary `.env`
  values are formatted as plain strings.

The code correctly avoids printing Cloud Run command values through
`redact_command`, but copying a secret from `.env` still models it as ordinary
configuration. The safest contract is not "the command will hide it." It is
"secret material never enters plain configuration."

### Engineering Decision

Lab 08 separates:

```text
plain env name/value
secret env name -> provider secret ID + immutable version
```

Remote release policy blocks:

- secret-shaped names in plain env;
- the same key appearing as plain and secret;
- unpinned secret versions;
- reserved target keys;
- out-of-band live values that a merge update would silently preserve.

Drift is evidence, not configuration to inherit automatically. A team can
explicitly adopt or delete it after review.

## Stateful Service Placement

Deployment target does not remove the data-lifecycle decisions from Phase 4.
The production envelope names Session, artifact and memory services
independently.

| Environment | Session | Artifact | Memory |
|---|---|---|---|
| Local lab | in-memory | in-memory | in-memory |
| Cloud Run baseline | durable SQL/service | object store | managed memory |
| Agent Runtime baseline | managed Session service | object store | managed memory |

The exact services are replaceable. The enforceable rule is that a horizontally
scaled or restartable remote target cannot accidentally retain in-memory
services as its durability claim.

## Telemetry Privacy

Agents CLI exposes two independent content paths:

1. trace/log span content, defaulting to `NO_CONTENT` and
   `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`;
2. prompt-response completion uploads to GCS/BigQuery, enabled by Terraform
   when the logs bucket and upload hook are configured.

Turning off content in spans does not turn off completion uploads. A production
telemetry contract therefore needs separate fields for:

- trace export;
- span/event content mode;
- full prompt-response capture;
- destination;
- retention;
- data-governance approval.

Lab 08 fails a release that enables full content without explicit approval,
sink and retention evidence.

## Release and Rollback

`deployment_metadata.json` stores either:

- a pending operation with project, location, target and start time; or
- the current Agent Runtime resource ID, target and timestamp.

Malformed metadata is treated as empty so deploy can continue. This is useful
local recovery state, not an append-only release record. It does not retain:

- source commit and digest;
- immutable build artifact;
- rendered deployment-spec digest;
- behavior-report identity and digest;
- staging promotion evidence;
- previous release;
- rollback decision.

Lab 08 adds an application-owned release ledger:

```text
release ID
  + source commit/digest
  + artifact ref/digest
  + rendered spec digest
  + behavior report/digest
  + platform resource/revision
  + staging source
  + previous release
```

Rollback then remains target-specific:

- Cloud Run shifts traffic to the prior recorded revision.
- Agent Runtime restores the prior immutable source bundle and redeploys
  through an external release orchestrator.
- Local runtime restarts the prior source artifact.

The shared abstraction is release evidence. The platform action is deliberately
not normalized into a fake universal command.

## Replaceable Ownership

Lab 08 renders six owned artifacts:

| Artifact | Owner | Authority |
|---|---|---|
| `agent/contract.json` | Agent team | authoritative |
| `quality/behavior-gate.json` | quality team | authoritative |
| `runtime/config.json` | service operator | authoritative |
| `deployment/spec.json` | platform team | authoritative |
| `lifecycle/manifest.json` | developer platform | authoritative |
| `release/candidate.json` | release engineering | derived |

Changing local to Cloud Run or Agent Runtime left the Agent and behavior files
unchanged. Only runtime, deployment, manifest and derived release candidate
changed.

This is the Phase 8 exit property:

> Environment, config, secret, eval, deploy, telemetry and rollback concerns
> can change through their owning artifact without forking Agent behavior.

## Deliberate Breakage

| Break | Blocking evidence |
|---|---|
| API key in plain env | plain/secret overlap, plaintext secret and rendered material |
| Full content telemetry | span content, approval and lifecycle failures |
| Failed/missing eval | behavior verdict and report identity failures |
| Mutable `latest` image | artifact reference lacks digest binding |
| Agent Runtime using Cloud Run semantics | artifact-kind and rollback mismatch |
| Live `DEBUG_BYPASS` plus changed log level | unmanaged and changed drift |
| Current-resource metadata only | eight missing release-evidence fields |
| Missing previous/staging records | rollback and promotion references unresolved |

The baseline's seven scenarios passed. All eight broken scenarios failed with
23 blocking reasons and process exit `1`.

## Decision Rules

1. Keep Agent source and behavior expectations target-independent.
2. Treat scaffold metadata, desired runtime config and release records as
   different types.
3. Never route secret material through plain `.env` propagation in production.
4. Detect live drift before applying merge-style updates.
5. Require explicit durable Session/artifact/memory choices for remote targets.
6. Separate trace metadata from full prompt-response capture.
7. Promote the exact artifact and behavior report tested in staging.
8. Store release history append-only; current-resource metadata is a cache.
9. Use native target rollback where it exists.
10. For redeploy-only targets, preserve an immutable prior artifact and a
    tested release procedure.

## Evidence and Limits

Lab 08 provides:

- 18 dependency-free tests;
- baseline exit `0` and broken exit `1`;
- a deterministic 43,765-byte evidence bundle;
- SHA-256
  `d3d51a6a421c37ef7dd775bb456b84142b9166dfaab603b081e07a624355cf89`.

No real cloud build, IAM binding, Terraform apply, traffic shift, datastore
migration or rollback was executed. Those remain environment-specific
integration gates.
