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
        self.assertEqual(config["agent"]["manager"]["permission"]["playwright_*"], "deny")

if __name__ == "__main__":
    unittest.main()
