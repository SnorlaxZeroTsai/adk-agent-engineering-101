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
