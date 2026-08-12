# Mini Agent Garden MVP

Research snapshot: 2026-08-12.

## Product Boundary

The MVP proves that one local product surface can discover, validate, scaffold,
test and upgrade three materially different Agent architectures without
combining their authorities.

It is not a cloud control plane. It does not create remote resources, resolve
secret material or claim durable distributed coordination.

## Command To Component Mapping

| Command | Components | Typed outputs |
|---|---|---|
| `list` | Catalog Registry | catalog projection |
| `inspect` | Catalog Registry | Implementation Selection |
| `validate` | Catalog Registry, Contract Validator | Validation Report |
| `create` | Registry, Validator, Project Renderer | Project Instance |
| `test` | Deployment Controller, Behavior Gate | Candidate, Behavior Report |
| `upgrade` | Registry, Validator, Renderer | Upgrade Plan, regenerated Project Instance |

The CLI owns no Catalog entry, Blueprint rule, metric, deployment status or
Release Record.

## Three Blueprint Proof

| Blueprint | Architecture | Managed files | Contract tests |
|---|---|---:|---:|
| `order-support-read-only` | single Agent | 24 | 13 |
| `research-workflow-rag` | Workflow/RAG | 18 | 7 |
| `case-triage-with-approval` | multi-agent/HITL | 18 | 7 |

All source files come from the Catalog-selected commit
`9702a79d15f81a9a44a8d40af3ca038196746c46`.

## Artifact Flow

```text
CatalogEntry + Blueprint
  -> Implementation Selection
  -> Validation Report
  -> Project Instance
  -> Local Candidate
  -> Behavior Report
```

Each arrow uses canonical JSON and SHA-256. The candidate is rejected when a
managed file, manifest digest or candidate digest changes.

## Project Ownership

Renderer-owned files are enumerated in `garden-project.json`. Upgrade may:

- replace a listed managed file;
- add a new managed file;
- remove an obsolete managed file.

Upgrade may not remove or overwrite an unlisted project-team file. Lab 13
creates `user/notes.txt`, applies a compatible Blueprint update and verifies the
file is unchanged.

## Upgrade Semantics

The MVP keeps three changes distinct:

1. v0.1 to v1.0 Blueprint schema migration preserves Blueprint, CatalogEntry
   and Implementation identity.
2. Compatible Blueprint composition changes regenerate managed artifacts.
3. Implementation ID/revision changes require explicit review.

This is a planning and local-apply contract. Database, Session, artifact,
memory and index migrations remain outside this local prototype.

## Extension Result

Architecture handlers are registered behind one typed interface, so CLI
command dispatch has no architecture-specific branch.

This does not make architecture an untyped plugin. The published Blueprint
schema and semantic validator remain the core authority. The default validator
rejects an experimental kind until its typed branch exists; a test-only typed
validator/handler pair proves the CLI itself does not need modification.

## Exit Evidence

- 3 CatalogEntries and Blueprints discovered.
- 3 deterministic Project Instances rendered.
- 27 implementation contract tests passed.
- 11 deliberate lifecycle failures blocked.
- 22 Lab 13 tests passed.
- Baseline exit `0`, broken exit `1`.
- Deterministic evidence bundle: 5,083 bytes.
- SHA-256:
  `e1d492a7a7050f2b8cc203bbcf48cdef22877e7688809ce5ebac93e9554fe420`.

## Remaining Production Work

- signed Catalog and release provenance;
- registry ACL and trust policy;
- file locking or a durable transactional store;
- cloud target adapters and deploy/ledger coordination;
- live-model behavior, latency and cost gates;
- durable upgrade migrations for stateful services.
