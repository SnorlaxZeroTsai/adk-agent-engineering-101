"""Typed architecture handlers used by rendering and behavior execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any
from typing import Protocol

from .contracts import TestSpec
from .errors import GardenError


class ArchitectureHandler(Protocol):
    kind: str

    def render_descriptor(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    def test_spec(self, implementation_root: Path) -> TestSpec:
        ...


@dataclass(frozen=True)
class _BaseHandler:
    kind: str

    def test_spec(self, implementation_root: Path) -> TestSpec:
        return TestSpec(
            command=(
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-q",
            ),
            working_directory="implementation",
        )


class SingleAgentHandler(_BaseHandler):
    def __init__(self) -> None:
        super().__init__("single-agent")

    def render_descriptor(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        architecture = blueprint["architecture"]
        return {
            "kind": self.kind,
            "root_agent": architecture["root_agent"],
            "model_slot": architecture["model_slot"],
            "tools": [
                {
                    "id": item["id"],
                    "effect": item["effect"],
                }
                for item in architecture["tools"]
            ],
        }


class WorkflowHandler(_BaseHandler):
    def __init__(self) -> None:
        super().__init__("workflow")

    def render_descriptor(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        architecture = blueprint["architecture"]
        return {
            "kind": self.kind,
            "entry_node": architecture["entry_node"],
            "node_ids": [item["id"] for item in architecture["nodes"]],
            "edge_count": len(architecture["edges"]),
            "terminal_nodes": architecture["terminal_nodes"],
            "retrieval_ids": [
                item["id"]
                for item in blueprint["runtime"]["retrieval_contracts"]
            ],
        }


class MultiAgentHandler(_BaseHandler):
    def __init__(self) -> None:
        super().__init__("multi-agent")

    def render_descriptor(
        self,
        blueprint: dict[str, Any],
    ) -> dict[str, Any]:
        architecture = blueprint["architecture"]
        return {
            "kind": self.kind,
            "coordinator": architecture["coordinator"],
            "agents": [
                {
                    "id": item["id"],
                    "mode": item["mode"],
                    "state_namespace": item["state_namespace"],
                }
                for item in architecture["agents"]
            ],
            "delegations": architecture["delegations"],
            "shared_state": architecture["shared_state"],
        }


class ArchitectureRegistry:
    """Dispatch architecture behavior without conditionals in the CLI."""

    def __init__(
        self,
        handlers: tuple[ArchitectureHandler, ...] | None = None,
    ) -> None:
        initial = handlers or (
            SingleAgentHandler(),
            WorkflowHandler(),
            MultiAgentHandler(),
        )
        self._handlers: dict[str, ArchitectureHandler] = {}
        for handler in initial:
            self.register(handler)

    def register(self, handler: ArchitectureHandler) -> None:
        if not handler.kind or handler.kind in self._handlers:
            raise GardenError(
                f"architecture handler already registered: {handler.kind}"
            )
        self._handlers[handler.kind] = handler

    def get(self, kind: str) -> ArchitectureHandler:
        try:
            return self._handlers[kind]
        except KeyError as error:
            raise GardenError(
                f"no typed architecture handler registered for {kind}"
            ) from error

    @property
    def kinds(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


def executable_command(spec: TestSpec) -> tuple[str, ...]:
    """Replace the portable command token only at the execution boundary."""

    if not spec.command or spec.command[0] != "python":
        raise GardenError("test command must use the controlled Python runtime")
    return (sys.executable, *spec.command[1:])
