# Labs

Labs turn architecture claims into observable behavior. Each lab should contain:

- a baseline implementation,
- one or more intentionally broken variants,
- deterministic tests where possible,
- live-model tests kept separate,
- a short observation log that updates the related documentation.

Current labs:

- [`01-agent-basics`](01-agent-basics/): Agent, tool and Runner boundaries.
- [`02-workflow-engineering`](02-workflow-engineering/): legacy composite versus
  graph Workflow control, failure and resume semantics.
- [`03-multi-agent`](03-multi-agent/): function, single-turn, transfer and task
  specialist boundaries under failure, overlap and state conflict.
- [`04-context-and-memory`](04-context-and-memory/): transient context, state,
  artifacts and memory under staleness, isolation and deletion failures.
- [`05-rag-engineering`](05-rag-engineering/): managed native Search versus
  explicit vector retrieval under provenance, ACL, version and deletion faults.
- [`06-evaluation`](06-evaluation/): typed datasets, normalized traces,
  deterministic/judge metrics and an enforceable cross-architecture release
  gate.
- [`07-safety-hitl`](07-safety-hitl/): global policy boundaries, tool and
  Workflow approval, credential scope and side-effect replay.
- [`08-production-engineering`](08-production-engineering/): replaceable
  runtime/deployment renders, secret and telemetry policy, release promotion,
  drift and target-specific rollback.
- [`09-pattern-catalog`](09-pattern-catalog/): canonical pattern manifests,
  claim-level evidence, relation boundaries and deliberate invalid catalog
  gates.
- [`10-agent-garden-discovery`](10-agent-garden-discovery/): recipe, template
  and project metadata ownership, stable catalog identity, immutable
  implementation provenance and misleading-entry gates.
- [`11-blueprint-schema`](11-blueprint-schema/): example-first executable
  Blueprint schema, Git/AST/graph semantic validation, invalid combinations
  and identity-preserving migration.
- [`12-mvp-architecture`](12-mvp-architecture/): authority-separated
  components, storage/trust/extension boundaries, release/rollback dataflow
  and three Blueprint lifecycle walkthroughs.
- [`13-mini-agent-garden`](13-mini-agent-garden/): local Catalog discovery,
  Blueprint validation, pinned-source scaffolding, candidate behavior tests,
  managed upgrades and typed architecture dispatch.
