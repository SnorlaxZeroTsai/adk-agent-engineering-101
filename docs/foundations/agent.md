# Foundation: The Agent Boundary

Status: baseline implemented; live ADK execution pending dependency installation.

## Question

What should an ADK `Agent` own, and what should remain in deterministic code or
application runtime services?

## Source-Derived Contract

The source snapshot is pinned in
[`references/upstream-lock.yaml`](../../references/upstream-lock.yaml).

### `BaseAgent`

Source facts from `google.adk.agents.base_agent.BaseAgent`:

- It is a Pydantic model and a workflow `BaseNode`.
- `name` must be a Python identifier, cannot be `user`, and identifies the
  Agent in a tree.
- `description` is model-visible delegation metadata.
- `sub_agents` form an owned tree. One Agent instance cannot have two parents.
- `run_async` creates a child invocation context, executes before callbacks,
  delegates to `_run_async_impl`, executes after callbacks and yields `Event`
  objects.
- A before callback can short-circuit the Agent; an after callback can append an
  additional response event.

Engineering interpretation:

> An Agent is a named, event-producing decision node with lifecycle hooks. It is
> not the database, session store, deployment unit or complete application.

### `LlmAgent` and `Agent`

In this snapshot, public `Agent` resolves to the LLM-backed Agent implementation.
Its configuration includes:

| Concern | ADK field | Boundary implication |
|---|---|---|
| Reasoning engine | `model` | Model choice is replaceable configuration, not domain state |
| Behavioral policy | `instruction`, `static_instruction` | Explain goals and decision policy; do not duplicate executable business rules |
| Capabilities | `tools` | Expose narrow, typed operations that can be observed and tested |
| Delegation behavior | `mode` | `chat`, `task` and `single_turn` imply different interaction contracts |
| Controlled data | `input_schema`, `output_schema`, `output_key` | Make handoffs explicit instead of scraping prose |
| Advanced reasoning | `planner`, `code_executor` | Add only when the task requires their risk and runtime cost |
| Enforcement hooks | model/tool callbacks | Intercept a specific boundary; coverage is not automatically global |

If `model` is omitted, source resolves it from an ancestor and then the class
default. The pinned source default is `gemini-3.5-flash`. Production code should
still configure the model explicitly so an upstream default change is observable.

### `App`

`App` is the top-level application container. It owns a root Agent or workflow
node and application-wide plugins, event compaction, context cache and
resumability configuration.

This produces a useful separation:

```text
App
  application-wide policy and lifecycle configuration
    |
    +-- root Agent or Workflow node
          model decision boundary
          |
          +-- deterministic tools
          +-- optional sub-agents/nodes

Runner
  session, artifact, memory and credential services
  event persistence and invocation lifecycle
```

The `Runner` and persistence services are covered in the execution-model module.
They are shown here only to prevent the Agent object from absorbing their
responsibilities.

## Responsibility Allocation

| Concern | Correct first home | Reason |
|---|---|---|
| Understand an ambiguous user request | Agent instruction/model | Requires semantic interpretation |
| Choose among bounded capabilities | Agent/model with tools | Choice is agentic; each capability stays observable |
| Calculate shipping price | Deterministic function/service | Formula must be testable and repeatable |
| Fetch an order | Tool/service boundary | External I/O and errors need a structured contract |
| Enforce a hard transaction limit | Code, policy callback or plugin | A prompt is not an enforcement mechanism |
| Fix execution order | Workflow/code | Ordering should not depend on model preference |
| Persist session history | Runner session service | Persistence lifecycle is outside model reasoning |
| Retain cross-session facts | Memory service with write policy | Requires explicit retention and recall semantics |
| Store a large generated file | Artifact service | It should not consume conversation state by default |
| Apply policy to every Agent | App plugin | App scope is explicit and centrally testable |

## Baseline Hypothesis

> A small support Agent remains understandable when it owns natural-language
> intent and tool choice, while typed tools own deterministic lookup and pricing
> rules.

Lab 01 tests this with:

- `get_order_status(order_id)`;
- `estimate_shipping(destination_zone, weight_kg)`;
- an Agent instruction that forbids inventing status or doing pricing math;
- structured success and error results;
- source-contract inspection that does not need an ADK import.

The Agent does not update orders, authenticate users, persist sessions or hide
shipping rates in its instruction.

## Intentional Breaks

### Break 1: Catch-All Tool

Replace both tools with:

```python
def handle_order_request(query: str) -> str:
    ...
```

Observed offline:

- the callable schema exposes only an unstructured `query`;
- order ID, destination zone and weight are no longer separately required;
- parsing, routing, business rules and response wording become one operation;
- deterministic tests cannot isolate tool-selection mistakes from pricing or
  extraction mistakes.

This shape may be reasonable for a remote legacy API that truly exposes one
endpoint, but it is a poor local abstraction when the capabilities are already
separate.

### Break 2: Raise on a Domain Miss

The broken lookup raises `KeyError` for an unknown order. The baseline returns:

```json
{
  "ok": false,
  "error": {
    "code": "order_not_found",
    "message": "No order exists with ID Z999."
  }
}
```

Observed offline:

- the structured result can be asserted and handed back to the model;
- the raised exception escapes a direct call and is indistinguishable from an
  implementation failure without additional translation.

Rule:

> Expected domain outcomes are data. Unexpected infrastructure or programming
> failures are exceptions.

The exact split remains domain-specific. A permission denial, timeout or corrupt
response may require retry and incident behavior rather than a normal result.

## Design Rules

1. Give an Agent one coherent decision responsibility.
2. Put deterministic, security-sensitive and transactional rules in code.
3. Make each tool name, docstring, parameter and return shape useful without
   relying on hidden prompt context.
4. Return machine-readable domain errors.
5. Keep side effects explicit in tool names and require confirmation where the
   operation warrants it.
6. Use structured Agent output for machine-to-machine handoffs.
7. Add callbacks/plugins only with a coverage matrix and tests.
8. Add a sub-agent only when it needs independent reasoning, identity, context
   or lifecycle; otherwise prefer a function or workflow node.
9. Keep model and environment configuration outside domain logic.
10. Treat emitted events as the observable contract; prose output alone is not
    enough for production verification.

## Decision Checklist

Before adding a responsibility to an Agent:

- Does it require semantic judgment, or can code decide it?
- Can the operation be independently named, typed and tested?
- Is a hard invariant being entrusted to prompt compliance?
- What state does it read and write, and who owns that state?
- Is the failure an expected domain result or an infrastructure exception?
- What event or metric proves the operation happened?
- Does the responsibility need its own Agent identity, or only isolation?
- How will the behavior be evaluated after model or ADK upgrades?

## Evidence and Limits

Offline evidence currently proves:

- deterministic tool behavior;
- explicit success/error contracts;
- Agent source contains the expected tools and configuration;
- broken variants expose a wider, less testable boundary.

It does not yet prove:

- actual model tool selection;
- `FunctionTool` generated schema;
- callback ordering in a real invocation;
- event trace, session persistence, latency, token usage or cost.

Those require the fake-model Runner trace and live-model gate in the next
foundation steps.

## Sources

- [`BaseAgent`, `LlmAgent`, `App`, `Runner` and `FunctionTool`
  index](../../references/source-index.md#adk-runtime)
- Lab: [`labs/01-agent-basics`](../../labs/01-agent-basics/)
