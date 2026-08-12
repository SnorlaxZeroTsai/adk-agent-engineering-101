from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENT_SOURCE = ROOT / "agent_basics" / "agent.py"


def assigned_call(tree: ast.AST, target: str) -> ast.Call:
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
    raise AssertionError(f"No call assignment found for {target}")


class AgentSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = ast.parse(AGENT_SOURCE.read_text(encoding="utf-8"))

    def test_root_agent_uses_expected_configuration(self) -> None:
        call = assigned_call(self.tree, "root_agent")
        keywords = {
            keyword.arg: keyword.value
            for keyword in call.keywords
            if keyword.arg is not None
        }

        self.assertEqual(ast.unparse(call.func), "Agent")
        self.assertEqual(
            {
                "name",
                "model",
                "description",
                "instruction",
                "tools",
                "mode",
            },
            set(keywords),
        )

    def test_root_agent_exposes_only_read_only_tools(self) -> None:
        call = assigned_call(self.tree, "root_agent")
        tools_node = next(
            keyword.value
            for keyword in call.keywords
            if keyword.arg == "tools"
        )

        self.assertIsInstance(tools_node, ast.List)
        self.assertEqual(
            [ast.unparse(item) for item in tools_node.elts],
            ["get_order_status", "estimate_shipping"],
        )

    def test_app_wraps_the_root_agent(self) -> None:
        call = assigned_call(self.tree, "app")
        keywords = {
            keyword.arg: ast.unparse(keyword.value)
            for keyword in call.keywords
            if keyword.arg is not None
        }

        self.assertEqual(ast.unparse(call.func), "App")
        self.assertEqual(keywords["root_agent"], "root_agent")


if __name__ == "__main__":
    unittest.main()
