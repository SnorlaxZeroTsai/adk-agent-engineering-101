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
    "docs/foundations/agent.md",
    "docs/foundations/tools.md",
    "docs/foundations/execution-model.md",
    "docs/workflows/deterministic-workflows.md",
    "docs/multi-agent/specialist-boundaries.md",
    "patterns/README.md",
    "patterns/deterministic-workflow.md",
    "patterns/bounded-specialist.md",
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
    if "Phase 4 State, context and memory | Next" not in roadmap:
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

    state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    if "Next Actions" not in state or "Unresolved Questions" not in state:
        fail("PROJECT_STATE.md lacks continuation context")

    print("PASS: project structure and Phase 0-3 artifacts verified")


if __name__ == "__main__":
    main()
