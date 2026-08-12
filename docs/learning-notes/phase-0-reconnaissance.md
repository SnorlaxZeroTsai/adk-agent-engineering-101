# Phase 0 Learning Note: Repository Reconnaissance

Date: 2026-08-12

## Question

What should be treated as authoritative evidence for learning Google Agent
Engineering from `adk-samples` and Agent Starter Pack?

## Initial Hypotheses

1. `adk-samples` is a set of peer examples that can be classified directly by
   folder.
2. Agent Starter Pack is the current production starting point.
3. A sample using ADK can be compared with another sample without first treating
   ADK version as an architecture variable.
4. Official samples mostly demonstrate recommended end-state design.
5. Existing manifests are close to the future Agent Garden blueprint.

All five hypotheses were weakened or rejected by source inspection.

## Method

The reconnaissance experiment used only repository source at fixed commits:

1. Enumerated active and legacy roots.
2. Read repository policies and JSON/YAML schemas before sample READMEs.
3. Counted samples by language and contribution tier.
4. Traced imports and dependency ranges into representative Agent entry points.
5. Inspected tests, callbacks, tools, state keys and deployment assets.
6. Compared documentation claims with implementation and test coverage.
7. Followed deprecation pointers from Starter Pack to Agents CLI.
8. Read ADK runtime source to avoid inferring 2.0 semantics from 1.x samples.

No model or Google Cloud execution was performed in this phase. The observed
behavior is repository validation and source structure, not runtime quality.

## Observations

### 1. Repository Layout Is Lifecycle Metadata

`core`, `contrib` and frozen `<language>/agents` roots describe ownership and
contribution policy. They do not reliably classify single-agent, multi-agent,
workflow, RAG or safety architecture.

Observed evidence:

- 11 active Python recipes exist under `core/python` and `contrib/python`.
- 40 older samples remain under frozen language roots.
- CI requires different files and size limits by tier.
- Transitional duplicate RAG paths are not byte-identical.

Lesson:

> Build the architecture taxonomy from imports, runtime wiring, tools, state and
> event flow; never infer it from the top-level folder alone.

### 2. Version Is an Architecture Boundary

The snapshot contains loose ADK 1.x ranges, explicit 2.x ranges and a
long-horizon recipe requiring a later 2.x range. ADK 2.0 introduces graph
`Workflow` and Task concepts while legacy composite APIs remain visible in
samples.

Lesson:

> Dependency version is part of the pattern record. A migration must preserve
> behavior and observability, not merely make imports pass.

### 3. Production Tooling Moved

Starter Pack's source still provides rich evidence for four-layer template
composition, Terraform, CI/CD, eval, tests, telemetry and deployment targets.
Its current README explicitly limits future work and directs new projects to
Agents CLI.

Lesson:

> Historical code can remain excellent design evidence without being the right
> product dependency for a new system.

### 4. Official Samples Contain Useful Failures

Examples found during source review:

- private ADK execution methods are monkey-patched in `global-kyc-agent`;
- `customer-service` blocks with `time.sleep` in a callback and uses mocked
  mutation backends;
- `cross-session-memory` can run with an in-memory service that does not prove
  durable cross-session recall;
- `safety-plugins` documentation and implementation coverage differ, while tests
  do not execute the plugin boundaries;
- a RAG custom score exists without a hard minimum gate;
- some READMEs, package names and model choices drift from current source.

Lesson:

> An official sample is a case study. Its shortcuts and drift are often as
> educational as its intended pattern.

### 5. Manifests Solve a Smaller Problem Than Blueprints

The recipe manifest validates type, status, language, ownership and optional
high-level architecture/dependency metadata. Starter Pack and Agents CLI add
different scaffold/lifecycle configuration.

Missing from a complete executable blueprint:

- tool and structured I/O contracts;
- runtime and persistence services;
- state/memory ownership and retention;
- policy hook coverage;
- evaluation datasets and release thresholds;
- secrets, SLOs, cost limits and upgrade behavior.

Lesson:

> Reuse the minimal catalog fields, but earn the rest of the blueprint through
> repeated labs and production cases.

## Intentional Break: README-Only Analysis

The deliberate failure mode was to form a map from README claims before reading
policy, dependency and implementation source.

It produced three incorrect outputs:

1. Starter Pack appeared to be the current lifecycle tool.
2. All sample folders appeared equally active.
3. "Safety plugin" appeared to imply complete input/output coverage.

Reading the maintenance notice, frozen-path policy and plugin implementation
invalidated those outputs. This establishes a project rule: every material
claim needs a source path and, where behavior matters, an experiment.

## Decisions

- Pin four repositories, not only the two initial entry points.
- Use `adk-python` as runtime authority.
- Preserve Starter Pack as template-composition evidence.
- Use Agents CLI for current lifecycle study.
- Select exactly 15 study units spanning simple, advanced, failure and
  production concerns.
- Teach ADK 2.0 foundations before comparing ADK 1.x patterns.
- Keep labs offline-testable, then add explicitly gated live/cloud evidence.

## Limitations

- Static source inspection cannot establish model behavior, latency, cost,
  concurrency correctness or cloud permission behavior.
- Some upstream commits are newer than locally available ADK packages; exact
  environment reproduction is still pending.
- The repository count is a snapshot and will change.
- The 15 units are a study syllabus, not a quality ranking.

## Next Experiment

Implement the smallest Agent boundary with deterministic tools, inspect its
contract offline, intentionally make tool boundaries ambiguous, and then add a
fake-model `Runner` trace when ADK dependencies are available.

See:

- [`../repo-map.md`](../repo-map.md)
- [`../roadmap.md`](../roadmap.md)
- [`../../references/source-index.md`](../../references/source-index.md)
