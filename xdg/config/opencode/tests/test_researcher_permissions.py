import fnmatch
import json
import unittest
from pathlib import Path


class ResearcherPermissionsTest(unittest.TestCase):
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
