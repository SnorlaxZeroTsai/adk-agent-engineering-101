# Lab 10 Observations

## Source Coverage

- 3個metadata surfaces。
- 33個field rows。
- Ownership counts：catalog 16、scaffold 19、runtime 6、governance 7。
- Recipe manifest涵蓋9個required discovery facts中的4個。
- Template config涵蓋3個。
- Project manifest只提供1個可靠的catalog classification fact。
- 沒有任何upstream surface單獨完整。
- Registry-composed CatalogEntry涵蓋9/9。

## Consumer Finding

Pinned Agents CLI的ADK discovery掃描已frozen的`python/agents`，未讀取目前
`core/`與`contrib/` recipe manifests。Repository-valid不等於consumer-visible。

## Gate Results

- Offline tests：16。
- Baseline exit：`0`。
- Broken exit：`1`。
- 13個misleading cases全部由指定issue code攔下。
- 兩次5,578-byte evidence renders byte-identical。
- SHA-256：
  `406fa09ddf419acfa0821fc1faa6796626ba485cae65ab5aa8aff87b767fdfee`。

## Decisions

- Stable Agent identity與implementation identity分開。
- Project name不能成為catalog ID。
- Full commit、path、framework constraint與assurance綁implementation。
- Template capability不是runtime proof。
- Active entry不能指向frozen source root。
- Deprecation需要replacement。
- Catalog不承擔executable Blueprint fields。

## Limits

- Baseline只有一個ADK 1.x recipe。
- Compatibility使用source-declared dependency constraint，沒有執行跨version
  migration。
- Assurance只有runnability evidence；production behavior仍由Phase 6/8
  contracts負責。
