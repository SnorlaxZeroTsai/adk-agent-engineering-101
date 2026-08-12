# Lab 12 Observations

## Baseline

- 6個components。
- 12個artifacts與6種storage classes。
- 9個trust boundaries。
- 7個extension points。
- 7個release stages與2個rollback stages。
- 3個Blueprint lifecycle walkthroughs。
- 6份Accepted ADRs。

## Gate Results

- Dependency-free tests：18。
- Baseline exit：`0`。
- Broken exit：`1`。
- 15個invalid cases全部由指定issue code攔下。
- 三個walkthroughs都產生digest-chained candidate、behavior report與release
  record。
- 兩次17,713-byte evidence renders byte-identical。
- SHA-256：
  `6a4d24895c644f9fc862bb264c86970e25965febed26f601974d150c07c72423`。

## Decisions

- Component依authority、credential與write model分界，不依CLI subcommand
  分界。
- Deployment Controller與Release Ledger分開。
- Behavior Gate與Contract Validator分開。
- Git/filesystem、content-addressed store、workspace、target cache、secret
  manager與append-only ledger有不同write model。
- New architecture kind需要typed core change；provider與target使用受限adapter。
- CLI是caller，不是Catalog、policy或release truth。

## Limits

- Walkthrough使用deterministic receipts，沒有呼叫cloud target。
- Release record尚未簽章，也沒有與platform promotion做transactional commit。
- Secret boundary只驗證reference-only contract。
- Access control、concurrent writers、remote trust與Phase 13 CLI尚未實作。
