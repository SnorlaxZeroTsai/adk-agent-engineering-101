# Phase 12 Learning Note: MVP Architecture

日期：2026-08-12

## 問題

1. 哪些components被Phase 8、10與11的contracts真正要求？
2. 哪些artifacts是authority、derived evidence或mutable cache？
3. Credential、code execution與release history應如何隔離？
4. Architecture extension何時需要core schema change？

## 初始假設

1. Registry、validator、renderer、evaluation與release service共五個components。
2. Deployment metadata可以同時作platform status與release history。
3. Validator可以順便執行evaluation。
4. 所有extension都能使用同一個plugin interface。

## Derivation

Phase 10要求stable Catalog identity與immutable Implementation selection；Phase
11要求Blueprint、Git/AST/graph semantics與architecture-specific validation；
Phase 6要求candidate execution與per-case blocking metrics；Phase 8要求target
credentials、mutable deployment status、immutable promotion evidence與
target-specific rollback。

這些authority不能由五個components安全承擔。Deployment與Ledger必須分開：

- Deployment Controller持有target credentials與mutable platform status。
- Release Ledger持有append-only promotion/rollback truth但沒有target
  credentials。

Validator與Behavior Gate也必須分開：

- Validator讀source並做static/semantic checks。
- Behavior Gate在sandbox中執行candidate與custom metric code。

## Component Result

```text
Catalog Registry
Contract Validator
Project Renderer
Deployment Controller
Behavior Gate
Release Ledger
```

CLI、event bus與database都不是第七個component。CLI是caller；event bus與
database尚沒有repeated evidence，storage先以write semantics描述。

## Storage And Trust

六種storage classes分別保留：

- reviewed Git authority；
- regenerable workspace；
- content-addressed evidence；
- append-only release ledger；
- mutable target control-plane cache；
- external secret manager。

九個trust boundaries涵蓋selection、source、render、deployment、secret、
evaluation、promotion、record與rollback。Secret只以reference通過boundary。

## Extension Result

Architecture kind保留在typed core，因single Agent、Workflow與multi-agent有
不同topology invariants。Source、renderer、runtime service、metric、
deployment target與release store則使用受限external adapters。

Adapter不得覆蓋identity、immutability、state ownership、blocking policy、
secret policy或release evidence。

## Walkthrough Experiment

三份Phase 11 Blueprints都走：

```text
discover -> validate -> render -> stage -> evaluate -> promote -> record
```

Workflow/RAG增加graph與retrieval validators；multi-agent/HITL增加delegation
與approval validators。Required metrics直接取自各Blueprint，platform不以
單一generic score取代architecture contract。

每個stage receipt對inputs與outputs做canonical SHA-256 binding。三條path都
沒有secret material。

## Deliberate Breakage

15個mutations破壞ownership、credentials、secret、immutability、cache、
extension、promotion evidence、walkthrough coverage與ADR。全部由指定issue
code攔下，broken CLI exit `1`。

## Results

```text
6 components
12 artifacts / 6 storage classes
9 trust boundaries / 7 extension points
7 release stages / 2 rollback stages
3 Blueprint walkthroughs
6 ADRs
15 invalid cases detected
18 dependency-free tests
baseline exit 0
broken exit 1
17,713-byte deterministic evidence bundle
```

SHA-256：

```text
6a4d24895c644f9fc862bb264c86970e25965febed26f601974d150c07c72423
```

## Architecture Decisions

- Split components by authority, credentials and write model.
- Separate Deployment Controller from Release Ledger.
- Separate Contract Validator from Behavior Gate.
- Keep rendering pure and credential-free.
- Promote only the exact candidate bound to a passing behavior report.
- Keep architecture kinds typed and external adapters constrained.
- Treat deployment status as cache, never release truth.
- Start with Git/filesystem semantics instead of a premature distributed
  platform.

## Limits

- No cloud deployment or live model was executed.
- No signed release record or transactional deployment/ledger commit exists.
- Storage adapters, registry ACL, job concurrency and remote trust remain
  unimplemented.
- Phase 13 must prove the component model through discover, scaffold,
  validate, test and upgrade CLI workflows.
