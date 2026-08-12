"""Upgrade planning across schema, Implementation, and rendered instance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import RenderPlan
from .contracts import UpgradePlan
from .errors import UpgradeReviewRequired
from .rendering import ProjectRenderer


class UpgradePlanner:
    def __init__(self, renderer: ProjectRenderer) -> None:
        self.renderer = renderer

    def plan(
        self,
        project_root: Path,
        target: RenderPlan,
        *,
        migration: dict[str, Any] | None = None,
    ) -> UpgradePlan:
        current = self.renderer.load_manifest(project_root)
        categories: list[str] = []
        if migration is not None:
            categories.append("blueprint-schema-migration")
        current_selection = current["selection_digest"]
        target_selection = target.manifest["selection_digest"]
        if current_selection != target_selection:
            categories.append("implementation-change")
        if current["blueprint_digest"] != target.manifest[
            "blueprint_digest"
        ]:
            categories.append("blueprint-composition-change")
        if current["renderer_id"] != target.manifest["renderer_id"]:
            categories.append("renderer-change")
        if (
            current["project_digest"] != target.manifest["project_digest"]
            and not categories
        ):
            categories.append("project-instance-regeneration")
        if not categories:
            categories.append("no-change")
        policy = target.blueprint["lifecycle"]["upgrade_policy"]
        requires_review = (
            "implementation-change" in categories
            or (
                "blueprint-composition-change" in categories
                and policy != "compatible-schema"
            )
        )
        return UpgradePlan(
            project_root=project_root.resolve(),
            categories=tuple(categories),
            requires_review=requires_review,
            migration=migration,
            current_manifest=current,
            target_plan=target,
        )

    def apply(
        self,
        plan: UpgradePlan,
        *,
        accept_review: bool = False,
    ) -> dict[str, Any]:
        if plan.requires_review and not accept_review:
            raise UpgradeReviewRequired(
                "upgrade changes Implementation or reviewed semantics"
            )
        manifest = self.renderer.apply_upgrade(
            plan.project_root,
            plan.target_plan,
        )
        return {
            "applied": True,
            "plan": plan.as_dict(),
            "project_digest": manifest["project_digest"],
        }
