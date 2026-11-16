import fnmatch
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).parent.parent
SPEC = importlib.util.spec_from_file_location("validate_opencode_setup", BASE / "validate_opencode_setup.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ResearcherPermissionsTest(unittest.TestCase):
    def test_search_guard_validation(self):
        config = json.loads((BASE / "opencode.json").read_text())
        self.assertEqual(config["permission"]["research_search_*"], "deny")
        for mcp in ({"research_search": {}}, {"servers": {"research_search": {}}}):
            with self.subTest(mcp=mcp):
                mutated = {**config, "mcp": mcp}
                errors = []
                with patch.object(Path, "read_text", return_value=json.dumps(mutated)):
                    validator.validate_config(errors)
                self.assertIn("research_search must not be configured in shared MCP servers", errors)

        config["permission"]["research_search_*"] = "allow"
        errors = []
        with patch.object(Path, "read_text", return_value=json.dumps(config)):
            validator.validate_config(errors)
        self.assertIn("research_search_* must be denied by default", errors)

    def test_code_mode_and_nested_tool_permissions(self):
        config = json.loads((Path(__file__).parent.parent / "opencode.json").read_text())
        researcher = config["agent"]["researcher"]
        permissions = researcher["permission"]

        def decision(tool):
            matches = [
                value
                for pattern, value in permissions.items()
                if fnmatch.fnmatchcase(tool, pattern)
            ]
            return matches[-1] if matches else None

        # Code Mode's built-in fetch is a network capability, not a nested MCP tool.
        self.assertTrue(researcher["tools"]["execute"])
        self.assertEqual(decision("execute"), "allow")
        for tool in (
            "playwright_browser_navigate",
            "playwright_browser_snapshot",
            "playwright_browser_click",
        ):
            self.assertTrue(researcher["tools"][tool])
            self.assertEqual(decision(tool), "allow")
        for tool in (
            "bash",
            "edit",
            "playwright_browser_evaluate",
            "playwright_browser_file_upload",
        ):
            self.assertEqual(decision(tool), "deny")
        self.assertEqual(config["agent"]["main"]["permission"]["playwright_*"], "deny")


class AgentTopologyTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((BASE / "opencode.json").read_text())
        self.agents = self.config["agent"]

    def test_default_agent_is_a_defined_primary(self):
        default = self.config["default_agent"]
        self.assertIn(default, self.agents)
        self.assertEqual(self.agents[default]["mode"], "primary")

    def test_main_delegates_only_to_defined_subagents(self):
        delegates = {k: v for k, v in self.agents["main"]["permission"]["task"].items() if k != "*"}
        self.assertEqual(self.agents["main"]["permission"]["task"]["*"], "deny")
        for name in delegates:
            with self.subTest(agent=name):
                self.assertIn(name, self.agents)
                self.assertEqual(self.agents[name]["mode"], "subagent")

    def test_subagents_cannot_delegate(self):
        for name, agent in self.agents.items():
            if agent.get("mode") != "subagent":
                continue
            with self.subTest(agent=name):
                task = agent.get("permission", {}).get("task")
                catch_all = agent.get("permission", {}).get("*")
                self.assertTrue(task == {"*": "deny"} or task == "deny" or catch_all == "deny")

    def test_prompt_files_exist_for_every_prompted_agent(self):
        for name, agent in self.agents.items():
            prompt = agent.get("prompt")
            if prompt is None:
                continue
            with self.subTest(agent=name):
                relative = prompt.removeprefix("{file:").removesuffix("}")
                self.assertTrue((BASE / relative).is_file(), relative)

    def test_retired_agent_name_is_not_referenced(self):
        for path in [BASE / "opencode.json", BASE / "global_rules.md", *(BASE / "prompts").glob("*.md")]:
            with self.subTest(path=path.name):
                self.assertNotIn('"manager"', path.read_text())

    def test_read_only_reviewers_and_producer_isolation(self):
        for name in ("strategist", "reviewer"):
            permission = self.agents[name]["permission"]
            with self.subTest(agent=name):
                self.assertEqual(permission["*"], "deny")
                self.assertEqual({k for k, v in permission.items() if v == "allow"}, {"read", "glob", "grep"})
        producer = self.agents["producer"]["permission"]
        for tool in ("webfetch", "websearch", "codesearch", "playwright_*"):
            self.assertEqual(producer[tool], "deny")
        self.assertEqual(producer["task"], {"*": "deny"})


if __name__ == "__main__":
    unittest.main()
