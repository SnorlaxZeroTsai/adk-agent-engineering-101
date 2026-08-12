#!/usr/bin/env python3
"""Verify the current learning-project milestone with stdlib only."""

from __future__ import annotations

import json
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
    "docs/learning-notes/phase-7-safety-hitl.md",
    "docs/learning-notes/phase-8-production.md",
    "docs/learning-notes/phase-9-pattern-catalog.md",
    "docs/foundations/agent.md",
    "docs/foundations/tools.md",
    "docs/foundations/execution-model.md",
    "docs/workflows/deterministic-workflows.md",
    "docs/multi-agent/specialist-boundaries.md",
    "docs/context/data-lifecycle.md",
    "docs/rag/rag-engineering.md",
    "docs/evaluation/evaluation-engineering.md",
    "docs/safety/safety-and-hitl.md",
    "docs/production/production-engineering.md",
    "docs/patterns/README.md",
    "docs/patterns/pattern-catalog.md",
    "patterns/README.md",
    "patterns/catalog.json",
    "patterns/schema/pattern.schema.json",
    "patterns/schema/catalog.schema.json",
    "patterns/deterministic-workflow.md",
    "patterns/bounded-specialist.md",
    "patterns/data-lifecycle-placement.md",
    "patterns/evidence-preserving-rag.md",
    "patterns/behavior-contract-gate.md",
    "patterns/durable-approval-boundary.md",
    "patterns/replaceable-production-envelope.md",
    "patterns/manifests/deterministic-workflow.json",
    "patterns/manifests/bounded-specialist.json",
    "patterns/manifests/data-lifecycle-placement.json",
    "patterns/manifests/evidence-preserving-rag.json",
    "patterns/manifests/behavior-contract-gate.json",
    "patterns/manifests/durable-approval-boundary.json",
    "patterns/manifests/replaceable-production-envelope.json",
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
    "labs/07-safety-hitl/README.md",
    "labs/07-safety-hitl/OBSERVATIONS.md",
    "labs/07-safety-hitl/safety_hitl_lab/domain.py",
    "labs/07-safety-hitl/safety_hitl_lab/policy.py",
    "labs/07-safety-hitl/safety_hitl_lab/runtime.py",
    "labs/07-safety-hitl/tests/test_domain.py",
    "labs/07-safety-hitl/runtime_tests/test_safety_hitl.py",
    "labs/07-safety-hitl/scripts/run_safety_hitl_traces.py",
    "labs/08-production-engineering/README.md",
    "labs/08-production-engineering/OBSERVATIONS.md",
    "labs/08-production-engineering/production_lab/contracts.py",
    "labs/08-production-engineering/production_lab/rendering.py",
    "labs/08-production-engineering/production_lab/policy.py",
    "labs/08-production-engineering/production_lab/release.py",
    "labs/08-production-engineering/production_lab/fixtures.py",
    "labs/08-production-engineering/production_lab/gate.py",
    "labs/08-production-engineering/tests/test_production_contract.py",
    "labs/08-production-engineering/scripts/run_production_gate.py",
    "labs/08-production-engineering/scripts/run_production_traces.py",
    "labs/09-pattern-catalog/README.md",
    "labs/09-pattern-catalog/OBSERVATIONS.md",
    "labs/09-pattern-catalog/pattern_catalog/contracts.py",
    "labs/09-pattern-catalog/pattern_catalog/loader.py",
    "labs/09-pattern-catalog/pattern_catalog/validation.py",
    "labs/09-pattern-catalog/pattern_catalog/fixtures.py",
    "labs/09-pattern-catalog/pattern_catalog/gate.py",
    "labs/09-pattern-catalog/fixtures/invalid_cases.json",
    "labs/09-pattern-catalog/tests/test_pattern_catalog.py",
    "labs/09-pattern-catalog/scripts/run_pattern_gate.py",
    "labs/09-pattern-catalog/scripts/run_pattern_traces.py",
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
    if "Phase 10 Agent Garden reverse engineering | Next" not in roadmap:
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

    safety_note = (ROOT / "docs/safety/safety-and-hitl.md").read_text(
        encoding="utf-8"
    )
    for required_concept in (
        "Coverage Matrix",
        "Approval Envelope",
        "Replay Behavior",
        "Credential Boundary",
    ):
        if required_concept not in safety_note:
            fail(f"safety/HITL module lacks {required_concept!r}")

    production_note = (
        ROOT / "docs/production/production-engineering.md"
    ).read_text(encoding="utf-8")
    for required_concept in (
        "Replaceable Ownership",
        "Configuration and Secret Boundary",
        "Telemetry Privacy",
        "Release and Rollback",
    ):
        if required_concept not in production_note:
            fail(f"production module lacks {required_concept!r}")

    pattern_note = (
        ROOT / "docs/patterns/pattern-catalog.md"
    ).read_text(encoding="utf-8")
    for required_concept in (
        "Maturity and Portability",
        "Evidence Linkage",
        "Decision Boundaries",
        "Invalid Catalog",
    ):
        if required_concept not in pattern_note:
            fail(f"pattern catalog module lacks {required_concept!r}")

    catalog = json.loads(
        (ROOT / "patterns/catalog.json").read_text(encoding="utf-8")
    )
    pattern_entries = catalog.get("patterns")
    if not isinstance(pattern_entries, list) or len(pattern_entries) != 7:
        fail("pattern catalog must index exactly seven Phase 9 patterns")
    if len(catalog.get("decision_boundaries", [])) != 5:
        fail("pattern catalog must retain five decision boundaries")

    state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    if "Next Actions" not in state or "Unresolved Questions" not in state:
        fail("PROJECT_STATE.md lacks continuation context")

    print("PASS: project structure and Phase 0-9 artifacts verified")


if __name__ == "__main__":
    main()
