# Mini Agent Garden

這是Phase 10–12 contracts的dependency-free local reference implementation。
CLI只編排Catalog Registry、Contract Validator、Project Renderer、local
Deployment Controller、Behavior Gate與Release Ledger adapter；business rules
仍由各component擁有。

## Commands

```text
list      discover CatalogEntry/Blueprint combinations
inspect   resolve Catalog, Blueprint and immutable Implementation
validate  run the Phase 11 schema/Git/AST/graph validator
create    render a deterministic Project Instance from pinned Git objects
test      stage an immutable local candidate and run contract tests
upgrade   plan or apply schema/Implementation/render regeneration
```

Run from the repository root:

```bash
PYTHONPATH=mini-agent-garden \
  python3 -m mini_agent_garden --repository . list

PYTHONPATH=mini-agent-garden \
  python3 -m mini_agent_garden --repository . \
  create order-support-read-only /tmp/order-support

PYTHONPATH=mini-agent-garden \
  python3 -m mini_agent_garden --repository . \
  test /tmp/order-support
```

Package installation is optional:

```bash
python3 -m pip install -e mini-agent-garden
mini-agent-garden --repository . list
```

## Project Instance

`create` produces:

```text
garden-project.json
README.md
contracts/
  blueprint.json
  implementation-selection.json
generated/
  architecture.json
implementation/
  ...pinned source tree...
reports/
  validation-report.json
```

`garden-project.json` lists every renderer-owned file and SHA-256 digest.
Unlisted files are project-team-owned and survive `upgrade --apply`.

## Test Evidence

`test`:

1. verifies every managed file;
2. builds a local content-addressed candidate;
3. resolves a code-owned test command from the typed architecture handler;
4. executes deterministic contract tests;
5. stores a candidate-bound Behavior Report under
   `.garden/behavior-reports/sha256/`.

The Blueprint cannot inject a shell command. The handler only permits the
controlled Python unittest runtime.

## Upgrade

Upgrade plans distinguish:

- `blueprint-schema-migration`;
- `blueprint-composition-change`;
- `implementation-change`;
- `renderer-change`;
- `project-instance-regeneration`;
- `no-change`.

Implementation changes and non-compatible composition changes require
`--accept-review`. Compatible regeneration only replaces paths listed in the
old/new manifests.

## Architecture Extension

CLI dispatch does not branch on `single-agent`, `workflow` or `multi-agent`.
It asks an `ArchitectureRegistry` for a typed handler.

Adding a new architecture still requires:

- a Blueprint schema branch;
- semantic validator rules;
- an architecture handler;
- lifecycle and behavior evidence.

Lab 13 injects an experimental typed handler and validator to prove the same
`create`/`test` CLI path works without modifying command dispatch. The default
validator rejects that fixture because it is not part of the published schema.

## Boundaries

- Source is read from immutable local Git objects; no network clone occurs.
- Secret values are never rendered or accepted by the ledger adapter.
- Behavior tests are local deterministic tests, not live-model or cloud tests.
- Local JSONL append-only semantics do not provide process locking, signatures
  or a transactional deploy/ledger commit.
- Cloud deployment, remote registry trust, ACL and durable job execution remain
  integration work.
