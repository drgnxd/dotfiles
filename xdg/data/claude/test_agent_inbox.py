import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load(name):
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HOOK = load("agent_inbox_hook")
CONFIG = load("agent_inbox_config")


class ClaudeInboxTests(unittest.TestCase):
    def test_hook_whitelists_only_safe_values(self):
        value = HOOK.safe_request({"tool_name": "Read", "permission_request_id": "r-1", "tool_input": {"command": "private"}})
        self.assertEqual(value, {"tool_name": "Read", "external_request_id": "r-1"})

    @patch.object(HOOK.subprocess, "run")
    def test_hook_outputs_only_one_shot_decision(self, mock_run):
        mock_run.return_value.stdout = "allow\n"
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "secret"}}))), patch("sys.stdout", output):
            self.assertEqual(HOOK.main(), 0)
        self.assertEqual(json.loads(output.getvalue()), {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        })
        self.assertEqual(json.loads(mock_run.call_args.kwargs["input"]), {"tool_name": "Bash"})
        self.assertNotIn("secret", output.getvalue())

    def test_config_merge_preserves_unrelated_credentials_and_unknown_fields(self):
        secret = "opaque-user-value"
        result = CONFIG.merge_config({"other": {"credential": secret}, "mcpServers": {"kept": {"x": 1}}}, "/nix/store/bin/agent-inbox")
        self.assertEqual(result["other"]["credential"], secret)
        self.assertEqual(result["mcpServers"]["kept"], {"x": 1})
        self.assertEqual(result["mcpServers"]["agent-inbox"], {"type": "stdio", "command": "/nix/store/bin/agent-inbox", "args": ["mcp"]})

    def test_config_update_requires_safe_symlink_and_preserves_unknown_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            link = Path(directory, "legacy.json")
            target.write_text(json.dumps({"preserve": "opaque", "mcpServers": {"old": {}}}))
            target.chmod(0o600)
            link.symlink_to(target)
            CONFIG.update(target, link, "agent-inbox")
            self.assertEqual(json.loads(target.read_text())["preserve"], "opaque")
            self.assertEqual(json.loads(target.read_text())["mcpServers"]["old"], {})
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)
