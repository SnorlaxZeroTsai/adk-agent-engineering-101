#!/usr/bin/env python3
"""Verify the current learning-project milestone with stdlib only."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    "README.md",
    "PROJECT_STATE.md",
    "docs/roadmap.md",
    "docs/repo-map.md",
    "docs/learning-notes/phase-0-reconnaissance.md",
    "docs/learning-notes/phase-1-foundations.md",
    "docs/learning-notes/phase-2-workflows.md",
    "docs/learning-notes/phase-3-multi-agent.md",
    "docs/learning-notes/phase-4-context-memory.md",
    "docs/learning-notes/phase-5-rag.md",
    "docs/learning-notes/phase-6-evaluation.md",
    "docs/foundations/agent.md",
    "docs/foundations/tools.md",
    "docs/foundations/execution-model.md",
    "docs/workflows/deterministic-workflows.md",
    "docs/multi-agent/specialist-boundaries.md",
    "docs/context/data-lifecycle.md",
    "docs/rag/rag-engineering.md",
    "docs/evaluation/evaluation-engineering.md",
    "patterns/README.md",
    "patterns/deterministic-workflow.md",
    "patterns/bounded-specialist.md",
    "patterns/data-lifecycle-placement.md",
    "patterns/evidence-preserving-rag.md",
    "patterns/behavior-contract-gate.md",
    "labs/README.md",
    "labs/01-agent-basics/README.md",
    "labs/01-agent-basics/agent_basics/runtime_trace.py",
    "labs/01-agent-basics/runtime_tests/test_runtime_trace.py",
    "labs/01-agent-basics/scripts/run_runtime_trace.py",
    "labs/02-workflow-engineering/README.md",
    "labs/02-workflow-engineering/workflow_lab/domain.py",
    "labs/02-workflow-engineering/workflow_lab/graph_pipeline.py",
    "labs/02-workflow-engineering/workflow_lab/legacy_pipeline.py",
    "labs/02-workflow-engineering/runtime_tests/test_workflow_comparison.py",
    "labs/02-workflow-engineering/scripts/run_workflow_traces.py",
    "labs/03-multi-agent/README.md",
    "labs/03-multi-agent/multi_agent_lab/domain.py",
    "labs/03-multi-agent/multi_agent_lab/builders.py",
    "labs/03-multi-agent/runtime_tests/test_multi_agent.py",
    "labs/03-multi-agent/scripts/run_multi_agent_traces.py",
    "labs/04-context-and-memory/README.md",
    "labs/04-context-and-memory/context_memory_lab/domain.py",
    "labs/04-context-and-memory/context_memory_lab/runtime.py",
    "labs/04-context-and-memory/runtime_tests/test_context_memory.py",
    "labs/04-context-and-memory/scripts/run_context_memory_traces.py",
    "labs/05-rag-engineering/README.md",
    "labs/05-rag-engineering/rag_lab/domain.py",
    "labs/05-rag-engineering/rag_lab/retrieval.py",
    "labs/05-rag-engineering/rag_lab/evaluation.py",
    "labs/05-rag-engineering/rag_lab/runtime.py",
    "labs/05-rag-engineering/runtime_tests/test_rag_runtime.py",
    "labs/05-rag-engineering/scripts/run_rag_traces.py",
    "labs/06-evaluation/README.md",
    "labs/06-evaluation/evaluation_lab/contracts.py",
    "labs/06-evaluation/evaluation_lab/dataset.py",
    "labs/06-evaluation/evaluation_lab/engine.py",
    "labs/06-evaluation/evaluation_lab/metrics.py",
    "labs/06-evaluation/evaluation_lab/cross_lab.py",
    "labs/06-evaluation/evaluation_lab/gate.py",
    "labs/06-evaluation/tests/test_evaluation_engine.py",
    "labs/06-evaluation/runtime_tests/test_cross_phase_gate.py",
    "labs/06-evaluation/scripts/run_eval_gate.py",
    "labs/06-evaluation/scripts/run_evaluation_traces.py",
    "case-studies/README.md",
    "agent-garden/README.md",
    "mini-agent-garden/README.md",
    "references/upstream-lock.yaml",
    "references/source-index.md",
)

EXPECTED_REPOSITORIES = (
    "google/adk-samples",
    "GoogleCloudPlatform/agent-starter-pack",
    "google/adk-python",
    "google/agents-cli",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing:
        fail("missing required paths: " + ", ".join(missing))

    lock_text = (ROOT / "references/upstream-lock.yaml").read_text(
        encoding="utf-8"
    )
    for repository in EXPECTED_REPOSITORIES:
        if repository not in lock_text:
            fail(f"upstream lock does not contain {repository}")

    repo_map = (ROOT / "docs/repo-map.md").read_text(encoding="utf-8")
    representative_rows = [
        line
        for line in repo_map.splitlines()
        if line.startswith("| R") and line[3:5].strip("0123456789") == ""
    ]
    if len(representative_rows) != 15:
        fail(
            "repo map must contain exactly 15 representative rows; "
            f"found {len(representative_rows)}"
        )

    roadmap = (ROOT / "docs/roadmap.md").read_text(encoding="utf-8")
    if "ADK 1.x" not in roadmap or "ADK 2.0" not in roadmap:
        fail("roadmap must preserve the ADK 1.x/2.0 migration boundary")
    if "Phase 7 Safety and HITL | Next" not in roadmap:
        fail("roadmap does not point to the next architecture dependency")

    workflow_note = (
        ROOT / "docs/workflows/deterministic-workflows.md"
    ).read_text(encoding="utf-8")
    for required_concept in (
        "Loop Exhaustion",
        "Duplicate Output",
        "Resume Comparison",
    ):
        if required_concept not in workflow_note:
            fail(f"Workflow module lacks {required_concept!r}")

    multi_agent_note = (
        ROOT / "docs/multi-agent/specialist-boundaries.md"
    ).read_text(encoding="utf-8")
    for required_concept in (
        "Conversational Ownership",
        "Overlapping Responsibility",
        "Shared-State Conflict",
    ):
        if required_concept not in multi_agent_note:
            fail(f"multi-agent module lacks {required_concept!r}")

    context_note = (ROOT / "docs/context/data-lifecycle.md").read_text(
        encoding="utf-8"
    )
    for required_concept in (
        "State Scopes",
        "Large-Context Break",
        "Cross-User Memory Break",
    ):
        if required_concept not in context_note:
            fail(f"context module lacks {required_concept!r}")

    rag_note = (ROOT / "docs/rag/rag-engineering.md").read_text(
        encoding="utf-8"
    )
    for required_concept in (
        "ACL Break",
        "Stale-Version Break",
        "Deletion-Lag Break",
    ):
        if required_concept not in rag_note:
            fail(f"RAG module lacks {required_concept!r}")

    evaluation_note = (
        ROOT / "docs/evaluation/evaluation-engineering.md"
    ).read_text(encoding="utf-8")
    for required_concept in (
        "Agents CLI Lifecycle",
        "Deliberate Breakage",
        "CI Semantics",
    ):
        if required_concept not in evaluation_note:
            fail(f"evaluation module lacks {required_concept!r}")

    state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    if "Next Actions" not in state or "Unresolved Questions" not in state:
        fail("PROJECT_STATE.md lacks continuation context")

    print("PASS: project structure and Phase 0-6 artifacts verified")


if __name__ == "__main__":
    main()
