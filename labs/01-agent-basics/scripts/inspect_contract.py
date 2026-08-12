#!/usr/bin/env python3
"""Inspect Agent source and tool signatures without importing Google ADK."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import sys
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_basics import tools  # noqa: E402
from experiments import broken_tools  # noqa: E402


def _assigned_call(tree: ast.AST, target: str) -> ast.Call:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(name, ast.Name) and name.id == target
            for name in node.targets
        ):
            continue
        if isinstance(node.value, ast.Call):
            return node.value
    raise ValueError(f"No call assignment found for {target}")


def _value_summary(value: ast.expr) -> object:
    if isinstance(value, ast.Constant):
        return value.value
    if isinstance(value, ast.List):
        return [ast.unparse(item) for item in value.elts]
    return ast.unparse(value)


def _agent_contract() -> dict[str, object]:
    source = (ROOT / "agent_basics" / "agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    call = _assigned_call(tree, "root_agent")
    return {
        "constructor": ast.unparse(call.func),
        "keywords": {
            keyword.arg: _value_summary(keyword.value)
            for keyword in call.keywords
            if keyword.arg is not None
        },
    }


def _tool_contract(function: Callable[..., object]) -> dict[str, str]:
    doc = inspect.getdoc(function) or ""
    return {
        "name": function.__name__,
        "signature": str(inspect.signature(function)),
        "summary": doc.splitlines()[0] if doc else "",
    }


def main() -> None:
    result = {
        "agent": _agent_contract(),
        "baseline_tools": [
            _tool_contract(tools.get_order_status),
            _tool_contract(tools.estimate_shipping),
        ],
        "broken_tools": [
            _tool_contract(broken_tools.handle_order_request),
            _tool_contract(broken_tools.get_order_status_or_raise),
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
