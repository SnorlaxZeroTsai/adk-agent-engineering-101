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
    "docs/foundations/agent.md",
    "patterns/README.md",
    "labs/README.md",
    "labs/01-agent-basics/README.md",
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

    state = (ROOT / "PROJECT_STATE.md").read_text(encoding="utf-8")
    if "Next Actions" not in state or "Unresolved Questions" not in state:
        fail("PROJECT_STATE.md lacks continuation context")

    print("PASS: project structure, source lock and Phase 0 artifacts verified")


if __name__ == "__main__":
    main()
