"""Application service composing the six Phase 12 authority boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .architecture import ArchitectureRegistry
from .behavior import BehaviorGate
from .behavior import LocalDeploymentController
from .catalog import CatalogRegistry
from .contracts import RenderPlan
from .errors import GardenError
from .rendering import ProjectRenderer
from .storage import AppendOnlyLedger
from .upgrade import UpgradePlanner
from .validation import ContractValidator


def find_repository_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (
            candidate
            / "agent-garden"
            / "mvp-architecture.json"
        ).is_file():
            return candidate
    raise GardenError("repository root was not found")


class MiniAgentGarden:
    """Thin orchestration facade; component classes retain all authority."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        architectures: ArchitectureRegistry | None = None,
        behavior_runner: Any | None = None,
        contract_validator: Any | None = None,
    ) -> None:
        self.root = (root or find_repository_root()).resolve()
        self.architectures = architectures or ArchitectureRegistry()
        self.catalog = CatalogRegistry(self.root)
        self.validator = contract_validator or ContractValidator(self.root)
        self.renderer = ProjectRenderer(
            self.root,
            self.architectures,
        )
        self.deployment = LocalDeploymentController(self.renderer)
        self.behavior = BehaviorGate(
            self.renderer,
            self.architectures,
            behavior_runner,
        )
        self.upgrades = UpgradePlanner(self.renderer)

    def list(
        self,
        *,
        architecture: str | None = None,
        tag: str | None = None,
    ) -> dict[str, Any]:
        entries = self.catalog.list(
            architecture=architecture,
            tag=tag,
        )
        return {
            "count": len(entries),
            "entries": entries,
        }

    def inspect(
        self,
        reference: str | Path | dict[str, Any],
    ) -> dict[str, Any]:
        return self.catalog.inspect(reference)

    def validate(
        self,
        reference: str | Path | dict[str, Any],
    ) -> dict[str, Any]:
        blueprint = self.catalog.load_blueprint(reference)
        return self.validator.validate(blueprint).as_dict()

    def _render_plan(
        self,
        blueprint: dict[str, Any],
    ) -> RenderPlan:
        selection = self.catalog.resolve(blueprint)
        validation = self.validator.require_valid(blueprint)
        return self.renderer.build_plan(
            blueprint,
            selection,
            validation,
        )

    def create(
        self,
        reference: str | Path | dict[str, Any],
        output: Path,
    ) -> dict[str, Any]:
        blueprint = self.catalog.load_blueprint(reference)
        plan = self._render_plan(blueprint)
        manifest = self.renderer.create(output, plan)
        return {
            "created": True,
            "output": str(output.resolve()),
            "manifest": manifest,
        }

    def test(self, project_root: Path) -> dict[str, Any]:
        candidate = self.deployment.stage(project_root)
        return self.behavior.evaluate(candidate)

    def upgrade(
        self,
        project_root: Path,
        reference: str | Path | dict[str, Any],
        *,
        apply: bool = False,
        accept_review: bool = False,
    ) -> dict[str, Any]:
        raw = self.catalog.load_blueprint(reference)
        blueprint, migration = self.validator.migrate_legacy(raw)
        target = self._render_plan(blueprint)
        plan = self.upgrades.plan(
            project_root,
            target,
            migration=migration,
        )
        if not apply:
            return {
                "applied": False,
                "plan": plan.as_dict(),
            }
        return self.upgrades.apply(
            plan,
            accept_review=accept_review,
        )

    def release_ledger(self, path: Path) -> AppendOnlyLedger:
        return AppendOnlyLedger(path)
