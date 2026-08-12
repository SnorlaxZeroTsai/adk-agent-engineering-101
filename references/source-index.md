# Primary Source Index

All links are pinned to the commits in `upstream-lock.yaml`.

## ADK Runtime

| Concern | Source | Why it matters |
|---|---|---|
| Agent base contract | [`BaseAgent`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/base_agent.py) | Defines identity, tree ownership, callbacks and event-producing lifecycle |
| LLM Agent composition | [`LlmAgent`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/llm_agent.py) | Model, instruction, tools, modes, structured I/O and model/tool callbacks |
| Application boundary | [`App`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/apps/app.py) | Root node plus application-wide plugins, compaction, cache and resumability |
| Runtime boundary | [`Runner`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/runners.py) | Connects execution to session, memory, artifact and credential services |
| Observable unit | [`Event`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/events/event.py) | Conversation content, actions, workflow output, branch and node metadata |
| Durable conversation | [`Session`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/sessions/session.py) | Persisted state plus ordered event history |
| Function tool adapter | [`FunctionTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/function_tool.py) | Converts Python signatures/docstrings into model-visible contracts |
| Agent as tool | [`AgentTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/agent_tool.py) | Shows isolation and state forwarding; source now discourages direct use |
| Agent modes and automatic wrappers | [`LlmAgent.model_post_init`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/llm_agent.py#L1128) | Adds finish-task, single-turn and task tools according to child mode |
| Conversational transfer | [`agent_transfer.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/flows/llm_flows/agent_transfer.py) | Builds eligible chat targets and excludes task/single-turn children |
| LLM Agent Workflow adapter | [`_llm_agent_wrapper.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/workflow/_llm_agent_wrapper.py) | Defines single-turn isolation, task dispatch, synthesized responses and completion |
| Task completion contract | [`FinishTaskTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/llm/task/_finish_task_tool.py) | Validates task output and keeps invalid completion inside the child loop |
| Task API runtime matrix | [`test_task_api_e2e.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/tests/unittests/workflow/test_task_api_e2e.py) | Covers coordinator dispatch, sequential tasks, validation retry, isolation and resume limits |
| Runtime tool context | [`Context`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/context.py) | Delta-aware state, artifacts, memory, credentials and confirmation actions |
| Tool base contract | [`BaseTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/base_tool.py) | Separates model declaration/request mutation from local execution |
| Provider built-in tool | [`GoogleSearchTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/google_search_tool.py) | Adds provider-native search configuration without local function execution |
| Native data-store search | [`VertexAiSearchTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/vertex_ai_search_tool.py) | Adds data-store/engine retrieval, filters and limits inside the Gemini request |
| Multi-tool search conversion | [`_convert_tool_union_to_tools`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/llm_agent.py#L140) | Can replace native Vertex AI Search with a local Discovery Engine FunctionTool |
| Explicit Discovery Engine search | [`DiscoveryEngineSearchTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/discovery_engine_search_tool.py) | Owns API calls, chunk/document parsing, errors and structured result serialization |
| Vertex AI RAG retrieval | [`VertexAiRagRetrieval`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/retrieval/vertex_ai_rag_retrieval.py) | Uses provider-native RAG for Gemini and a query FunctionTool fallback for other models |
| MCP lifecycle | [`McpToolset`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/mcp_tool/mcp_toolset.py) | Dynamic discovery, filtering, auth, caching and connection cleanup |
| Invocation contract | [`InvocationContext`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/invocation_context.py) | Defines invocation, agent-call and model-step hierarchy |
| State delta contract | [`State`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/sessions/state.py) | Tracks current state and pending event delta with optional schema validation |
| Per-invocation model context | [`RunConfig.model_input_context`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/run_config.py#L256) | Adds transient model contents without writing them to Session history |
| Dynamic instruction assembly | [`instructions.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/flows/llm_flows/instructions.py) | Resolves string placeholders, callable providers, static instruction and request placement |
| State scope materialization | [`_session_util.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/sessions/_session_util.py) | Separates app, user, session and temporary deltas when Sessions are read and persisted |
| Artifact service contract | [`BaseArtifactService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/artifacts/base_artifact_service.py) | Defines versioned save, load, list and delete operations with Session and user namespaces |
| In-memory artifact semantics | [`InMemoryArtifactService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/artifacts/in_memory_artifact_service.py) | Makes version increments, namespace isolation and deletion behavior observable |
| Memory service contract | [`BaseMemoryService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/memory/base_memory_service.py) | Requires explicit ingestion and app/user-scoped search but defines no portable delete API |
| In-memory recall semantics | [`InMemoryMemoryService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/memory/in_memory_memory_service.py) | Provides deterministic token search while documenting backend-specific retention limits |
| Automatic memory preload | [`PreloadMemoryTool`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/tools/preload_memory_tool.py) | Searches before model execution and injects past conversations as dynamic instruction |
| Test session service | [`InMemorySessionService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/sessions/in_memory_session_service.py) | Makes persistence behavior observable while documenting production limits |
| Legacy sequence | [`SequentialAgent`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/sequential_agent.py) | Deprecated ordered child execution with current-child checkpoints |
| Legacy fan-out | [`ParallelAgent`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/parallel_agent.py) | Deprecated concurrent branches and merged child Event streams |
| Legacy loop | [`LoopAgent`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/agents/loop_agent.py) | Deprecated iteration state, escalation exit and maximum-iteration bound |
| Graph orchestration | [`Workflow`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/workflow/_workflow.py) | Trigger scheduling, join handling, routed loops, checkpoints and replay |
| Graph validation | [`_graph_validation.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/workflow/utils/_graph_validation.py) | Rejects duplicate/unreachable structure, unconditional cycles and schema mismatch |
| Per-node execution | [`NodeRunner`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/workflow/_node_runner.py) | Owns node context, timeout, retry, error Event and output/delta flushing |
| Workflow rehydration | [`ReplayManager`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/workflow/utils/_replay_manager.py) | Reconstructs direct-child executions and deterministic completion order from Events |
| Evaluation case contract | [`EvalCase` and `Invocation`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/eval_case.py) | Defines static/scenario cases, Session input, final state and reduced intermediate evidence |
| Evaluation dataset | [`EvalSet`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/eval_set.py) | Groups stable case identity and metadata separately from generated results |
| Metric and criterion schema | [`eval_metrics.py`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/eval_metrics.py) | Defines thresholds, judge sampling, trajectory match types and prebuilt metrics |
| Tool trajectory evaluator | [`TrajectoryEvaluator`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/trajectory_evaluator.py) | Compares exact tool names and arguments, then averages per-invocation scores |
| Local evaluation lifecycle | [`LocalEvalService`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/local_eval_service.py) | Separates inference, per-metric evaluation, per-invocation results and final case status |
| Evaluation result contract | [`EvalCaseResult`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/eval_result.py) | Retains overall and per-invocation metric results with generated Session details |
| Legacy score aggregation | [`AgentEvaluator._process_metrics_and_get_failures`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/agent_evaluator.py#L797) | Uses a mean across invocation scores, which can mask one critical failed case |
| Custom metric registry | [`MetricEvaluatorRegistry`](https://github.com/google/adk-python/blob/a56f6e13ae38296b608808c7a3b37efe4b8c862e/src/google/adk/evaluation/metric_evaluator_registry.py) | Resolves built-in and import-path custom evaluators with instance-local registration |

## Recipe Productization

| Concern | Source | Why it matters |
|---|---|---|
| Recipe metadata | [`manifest-schema.json`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/.github/schemas/manifest-schema.json) | Minimal catalog contract: type, status, language, architecture, dependencies and ownership |
| Repository policy | [`.github/policy.yml`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/.github/policy.yml) | Active roots, frozen legacy roots, required files and size limits |
| Recipe anatomy | [`docs/recipe-handbook/anatomy.md`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/docs/recipe-handbook/anatomy.md) | Turns a sample into a validated, owned recipe |
| Recipe preparation | [`prepare-python-recipe`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/.agents/skills/prepare-python-recipe/SKILL.md) | Encodes scaffolding and validation as a reusable developer workflow |

## Representative Architecture Evidence

| Pattern | Source |
|---|---|
| Deterministic sequence | [`llm-auditor/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/python/agents/llm-auditor/llm_auditor/agent.py) |
| Custom iterative loop | [`deep-search/app/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/deep-search/app/agent.py) |
| Private composite patching | [`global-kyc-agent/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/python/agents/global-kyc-agent/global_kyc_agent/agent.py) |
| Coordinator and specialist tools | [`financial-advisor/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/contrib/python/financial-advisor/financial_advisor/agent.py) |
| Cross-session memory | [`cross-session-memory/app/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/cross-session-memory/app/agent.py) |
| Global guardrails | [`safety-plugins/plugins/agent_as_a_judge.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/safety-plugins/safety_plugins/plugins/agent_as_a_judge.py) |
| Event-driven HITL | [`ambient-expense-agent/expense_agent/agent.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/ambient-expense-agent/expense_agent/agent.py) |
| Long-horizon interfaces | [`long-horizon-harness/AGENTS.md`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/long-horizon-harness/AGENTS.md) |
| Managed RAG runtime seam | [`rag-agent-search/app/retrievers.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-agent-search/app/retrievers.py) |
| Managed connector lifecycle | [`agent_platform_search.tf`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-agent-search/infra/terraform/agent_platform_search.tf) |
| Explicit vector retrieval | [`rag-vector-search/app/retrievers.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-vector-search/app/retrievers.py) |
| Explicit chunking and IDs | [`process_data.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-vector-search/data_ingestion/data_ingestion_pipeline/components/process_data.py) |
| Vector ingestion reconciliation | [`ingest_data.py`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-vector-search/data_ingestion/data_ingestion_pipeline/components/ingest_data.py) |
| RAG sample evaluation | [`rag-agent-search/eval_config.yaml`](https://github.com/google/adk-samples/blob/4b5dd7705750dafbd987aa83efc323c3691d45fc/core/python/rag-agent-search/tests/eval/eval_config.yaml) | Shows generic response-quality and turn-count metrics without retrieval-specific release thresholds |

## Production Lifecycle

| Concern | Source | Why it matters |
|---|---|---|
| Starter Pack layer composition | [`process_template`](https://github.com/GoogleCloudPlatform/agent-starter-pack/blob/659f047742457bd55e5db0edd088cf678b6f0669/agent_starter_pack/cli/utils/template.py) | Merges shared base, language base, deployment target and agent overlay |
| Template capability metadata | [`agents/adk/.template/templateconfig.yaml`](https://github.com/GoogleCloudPlatform/agent-starter-pack/blob/659f047742457bd55e5db0edd088cf678b6f0669/agent_starter_pack/agents/adk/.template/templateconfig.yaml) | Declares requirements, targets, dependencies and example prompt |
| Current project manifest | [`ProjectConfig`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/_project.py) | Reads `agents-cli-manifest.yaml` as lifecycle metadata |
| Current eval lifecycle | [`eval/_paths.py`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/eval/_paths.py) | Separates datasets, generated traces and graded results |
| Trace generation | [`eval/cmd_generate.py`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/eval/cmd_generate.py) | Captures HTTP Agent events, supports N+1 conversations and records per-case inference failures |
| Trace grading | [`eval/cmd_grade.py`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/eval/cmd_grade.py) | Runs predefined, local custom or remote custom metrics and writes grade artifacts |
| Custom metric execution | [`eval/eval_utils.py`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/eval/eval_utils.py) | Compiles local metric code in process and makes eval configuration a code-execution boundary |
| Evaluation comparison | [`eval/cmd_compare.py`](https://github.com/google/agents-cli/blob/5a306f8956cb1eeae69f9709de0e4d61b44e11e7/src/google/agents/cli/eval/cmd_compare.py) | Produces recursive JSON differences and numeric deltas without regression policy or blocking status |
