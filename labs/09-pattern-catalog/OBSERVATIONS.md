# Lab 09 Observations

Observed from the normalized catalog and deliberate invalid fixtures.

## Catalog Shape

- 7 validated patterns.
- 6 portable patterns.
- 1 version-specific pattern: Bounded Specialist.
- 28 observable contracts.
- 28 failure modes.
- 7 explicitly rejected decisions.
- 11 cross-pattern relations.
- 5 decision boundaries.

## Normalization Findings

Maturity and portability are independent. Bounded Specialist is locally
validated against ADK 2.6.3 while its current `chat`, `single_turn` and `task`
implementation remains version-specific.

Pattern evidence must be claim-level. A source list at the bottom of a card
does not prove which source or experiment supports one invariant.

The catalog relation graph exposed five boundaries that individual phase notes
did not express in one place:

1. deterministic control versus semantic specialist ownership;
2. lifecycle placement versus ranked retrieval;
3. runtime enforcement versus evaluation;
4. framework resume versus side-effect idempotency;
5. Agent behavior versus deployment target.

## Gate Results

The baseline catalog passed with zero issues. All 12 deliberately invalid
mutations were rejected by their expected issue code.

- Offline tests: 14.
- Baseline exit: `0`.
- Broken exit: `1`.
- Two 3,327-byte evidence renders were byte-identical.
- SHA-256:
  `4bf1fea24ebc3ce4a06c2423da64ab017be11cba911d6452f4875730b92d91a9`.

## Limits

- The catalog contains seven patterns extracted from the current learning
  phases; it is not an exhaustive Agent architecture taxonomy.
- Portable means the decision contract is not tied to one ADK API. Only the
  pinned implementations were executed.
- A schema cannot prove that a source claim is interpreted correctly; review
  and executable evidence remain required.
