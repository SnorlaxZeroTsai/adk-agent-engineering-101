"""Pure Project Renderer and managed-file integrity checks."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .architecture import ArchitectureRegistry
from .canonical import canonical_bytes
from .canonical import digest_bytes
from .canonical import digest_json
from .canonical import load_json
from .canonical import write_json
from .contracts import ContractReport
from .contracts import ImplementationSelection
from .contracts import ManagedFile
from .contracts import RenderPlan
from .errors import GardenError
from .source import GitSourceReader


RENDERER_ID = "mini-agent-garden/1.0"


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise GardenError(f"managed path escapes project root: {relative}")
    return candidate


class ProjectRenderer:
    """Render only derived files; never resolve secret material or deploy."""

    def __init__(
        self,
        root: Path,
        architectures: ArchitectureRegistry,
    ) -> None:
        self.root = root.resolve()
        self.architectures = architectures
        self.source = GitSourceReader(self.root)

    def build_plan(
        self,
        blueprint: dict[str, Any],
        selection: ImplementationSelection,
        validation: ContractReport,
    ) -> RenderPlan:
        if not validation.passed:
            raise GardenError("cannot render a failing validation report")
        implementation_files, source_tree_digest = self.source.read_tree(
            selection
        )
        kind = blueprint["architecture"]["kind"]
        descriptor = self.architectures.get(kind).render_descriptor(
            blueprint
        )
        files: dict[str, bytes] = {
            "README.md": (
                "# Generated Agent Project\n\n"
                f"Blueprint: `{blueprint['id']}`\n\n"
                f"Architecture: `{kind}`\n\n"
                "Files listed in `garden-project.json` are renderer-owned.\n"
            ).encode("utf-8"),
            "contracts/blueprint.json": canonical_bytes(blueprint),
            "contracts/implementation-selection.json": canonical_bytes(
                {
                    **selection.as_dict(),
                    "selection_digest": selection.digest,
                }
            ),
            "generated/architecture.json": canonical_bytes(descriptor),
            "reports/validation-report.json": canonical_bytes(
                {
                    **validation.as_dict(),
                    "report_digest": validation.digest,
                }
            ),
        }
        for relative, value in implementation_files.items():
            files[f"implementation/{relative}"] = value
        managed = [
            ManagedFile(path=path, digest=digest_bytes(value)).as_dict()
            for path, value in sorted(files.items())
        ]
        manifest_core = {
            "schema_version": "1.0",
            "project_id": blueprint["id"],
            "blueprint_id": blueprint["id"],
            "blueprint_digest": digest_json(blueprint),
            "catalog_ref": blueprint["catalog_ref"],
            "selection_digest": selection.digest,
            "validation_report_digest": validation.digest,
            "architecture_kind": kind,
            "renderer_id": RENDERER_ID,
            "source_tree_digest": source_tree_digest,
            "managed_files": managed,
        }
        manifest = {
            **manifest_core,
            "project_digest": digest_json(manifest_core),
        }
        return RenderPlan(
            blueprint=blueprint,
            selection=selection,
            validation=validation,
            files=files,
            manifest=manifest,
        )

    def create(self, output: Path, plan: RenderPlan) -> dict[str, Any]:
        output = output.resolve()
        if output.exists():
            raise GardenError(f"output already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{output.name}.garden-",
                dir=output.parent,
            )
        )
        try:
            self._write_plan(staging, plan)
            os.replace(staging, output)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return plan.manifest

    def apply_upgrade(
        self,
        project_root: Path,
        plan: RenderPlan,
    ) -> dict[str, Any]:
        project_root = project_root.resolve()
        current = self.load_manifest(project_root)
        old_paths = {
            item["path"]
            for item in current.get("managed_files", [])
        }
        new_paths = set(plan.files)
        for relative in sorted(old_paths - new_paths, reverse=True):
            path = _safe_path(project_root, relative)
            if path.is_file():
                path.unlink()
        self._write_plan(project_root, plan)
        return plan.manifest

    def _write_plan(self, root: Path, plan: RenderPlan) -> None:
        root.mkdir(parents=True, exist_ok=True)
        for relative, value in sorted(plan.files.items()):
            path = _safe_path(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        write_json(root / "garden-project.json", plan.manifest)

    def load_manifest(self, project_root: Path) -> dict[str, Any]:
        path = project_root.resolve() / "garden-project.json"
        if not path.is_file():
            raise GardenError(f"not a Garden Project Instance: {project_root}")
        return load_json(path)

    def load_blueprint(self, project_root: Path) -> dict[str, Any]:
        return load_json(
            project_root.resolve() / "contracts" / "blueprint.json"
        )

    def verify(
        self,
        project_root: Path,
    ) -> tuple[dict[str, Any], ...]:
        root = project_root.resolve()
        manifest = self.load_manifest(root)
        issues = []
        for item in manifest.get("managed_files", []):
            relative = item.get("path")
            expected = item.get("digest")
            if not isinstance(relative, str):
                issues.append(
                    {
                        "code": "managed_path_invalid",
                        "path": "garden-project.json",
                    }
                )
                continue
            path = _safe_path(root, relative)
            if not path.is_file():
                issues.append(
                    {
                        "code": "managed_file_missing",
                        "path": relative,
                    }
                )
                continue
            observed = digest_bytes(path.read_bytes())
            if observed != expected:
                issues.append(
                    {
                        "code": "managed_file_digest_mismatch",
                        "path": relative,
                        "expected": expected,
                        "observed": observed,
                    }
                )
        core = {
            key: value
            for key, value in manifest.items()
            if key != "project_digest"
        }
        observed_project_digest = digest_json(core)
        if observed_project_digest != manifest.get("project_digest"):
            issues.append(
                {
                    "code": "project_manifest_digest_mismatch",
                    "path": "garden-project.json",
                    "expected": manifest.get("project_digest"),
                    "observed": observed_project_digest,
                }
            )
        return tuple(issues)
