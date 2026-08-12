# Lab 13 Observations

## Baseline

- Catalog entries：3。
- Blueprint architectures：single Agent、Workflow/RAG、multi-agent/HITL。
- Managed files：24、18、18。
- Actual implementation contract tests：13、7、7，共27。
- Behavior reports：3 baseline + 1 compatible-upgrade + 1 typed-extension。
- v0.1 migration保留Blueprint、CatalogEntry與Implementation identity。
- Compatible upgrade保留unlisted `user/notes.txt`。
- Local append-only ledger records：1。

## Gate Results

- Dependency-free tests：22。
- Baseline exit：`0`。
- Broken exit：`1`。
- 11個invalid flows全部被指定code攔下。
- 兩次5,083-byte evidence renders byte-identical。
- SHA-256：
  `e1d492a7a7050f2b8cc203bbcf48cdef22877e7688809ce5ebac93e9554fe420`。

## Decisions

- CLI只做orchestration，validation rules保留在Phase 11 component。
- Project Instance直接讀pinned Git objects，不依賴network或mutable branch。
- Blueprint不能提供test shell command；architecture handler提供controlled
  unittest spec。
- Managed/unmanaged file list是upgrade ownership boundary。
- Candidate與Behavior Report分別content-addressed。
- Implementation change需要review，compatible schema/composition change可
  regenerate。
- New architecture需要typed schema/validator/handler；CLI dispatch不變。

## Limits

- Contract tests是deterministic local tests，不是74個ADK runtime tests。
- JSONL append-only adapter沒有locking、signature或transaction。
- No cloud deploy, remote ACL, live model or durable migration was executed.
