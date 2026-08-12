"""Local candidate staging and deterministic behavior-report generation."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import Any
from typing import Callable

from .architecture import ArchitectureRegistry
from .architecture import executable_command
from .canonical import digest_json
from .canonical import load_json
from .canonical import write_json
from .contracts import Candidate
from .errors import ProjectIntegrityError
from .rendering import ProjectRenderer
from .storage import ContentAddressedStore


Runner = Callable[
    [tuple[str, ...], Path],
    subprocess.CompletedProcess[str],
]


def _default_runner(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )


class LocalDeploymentController:
    """Build a local immutable candidate without cloud credentials."""

    def __init__(self, renderer: ProjectRenderer) -> None:
        self.renderer = renderer

    def stage(self, project_root: Path) -> Candidate:
        project_root = project_root.resolve()
        issues = self.renderer.verify(project_root)
        if issues:
            codes = sorted({item["code"] for item in issues})
            raise ProjectIntegrityError(
                "candidate integrity failed: " + ", ".join(codes)
            )
        manifest = self.renderer.load_manifest(project_root)
        payload = {
            "schema_version": "1.0",
            "project_id": manifest["project_id"],
            "project_digest": manifest["project_digest"],
            "blueprint_id": manifest["blueprint_id"],
            "blueprint_digest": manifest["blueprint_digest"],
            "selection_digest": manifest["selection_digest"],
            "architecture_kind": manifest["architecture_kind"],
            "target": "local",
            "status": "staged",
        }
        digest = digest_json(payload)
        store = ContentAddressedStore(
            project_root / ".garden" / "candidates"
        )
        stored_digest, _ = store.put(payload)
        if stored_digest != digest:
            raise ProjectIntegrityError("candidate digest changed on write")
        write_json(
            project_root / ".garden" / "latest-candidate.json",
            {
                "candidate_digest": digest,
                "status": "staged",
            },
        )
        return Candidate(
            project_root=project_root,
            candidate_digest=digest,
            payload=payload,
        )


class BehaviorGate:
    """Execute code-owned test commands against one exact local candidate."""

    def __init__(
        self,
        renderer: ProjectRenderer,
        architectures: ArchitectureRegistry,
        runner: Runner | None = None,
    ) -> None:
        self.renderer = renderer
        self.architectures = architectures
        self.runner = runner or _default_runner

    def evaluate(self, candidate: Candidate) -> dict[str, Any]:
        project_root = candidate.project_root
        if digest_json(candidate.payload) != candidate.candidate_digest:
            raise ProjectIntegrityError("candidate digest is invalid")
        issues = self.renderer.verify(project_root)
        if issues:
            raise ProjectIntegrityError(
                "candidate changed after staging"
            )
        manifest = self.renderer.load_manifest(project_root)
        if manifest["project_digest"] != candidate.payload["project_digest"]:
            raise ProjectIntegrityError("candidate no longer matches project")
        blueprint = load_json(
            project_root / "contracts" / "blueprint.json"
        )
        handler = self.architectures.get(
            manifest["architecture_kind"]
        )
        spec = handler.test_spec(project_root / "implementation")
        command = executable_command(spec)
        cwd = project_root / spec.working_directory
        result = self.runner(command, cwd)
        combined = result.stdout + "\n" + result.stderr
        match = re.search(r"Ran (\d+) tests?", combined)
        test_count = int(match.group(1)) if match else 0
        passed = result.returncode == 0 and test_count > 0
        core = {
            "schema_version": "1.0",
            "project_id": manifest["project_id"],
            "blueprint_id": manifest["blueprint_id"],
            "blueprint_digest": manifest["blueprint_digest"],
            "candidate_digest": candidate.candidate_digest,
            "architecture_kind": manifest["architecture_kind"],
            "blocking_metrics": blueprint["evaluation"][
                "blocking_metrics"
            ],
            "test_command": list(spec.command),
            "test_count": test_count,
            "exit_code": result.returncode,
            "status": "passed" if passed else "failed",
            "passed": passed,
        }
        report_digest = digest_json(core)
        report = {
            **core,
            "report_digest": report_digest,
        }
        store = ContentAddressedStore(
            project_root / ".garden" / "behavior-reports"
        )
        stored_digest, _ = store.put(core)
        if stored_digest != report_digest:
            raise ProjectIntegrityError(
                "behavior report digest changed on write"
            )
        write_json(
            project_root / ".garden" / "latest-behavior-report.json",
            report,
        )
        return report
