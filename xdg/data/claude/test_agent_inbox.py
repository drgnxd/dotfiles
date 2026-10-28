import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
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

    @patch.object(HOOK.secrets, "token_urlsafe", return_value="local-random-id")
    def test_hook_generates_external_id_when_client_omits_it(self, token):
        value = HOOK.safe_request({"tool_name": "Read", "tool_input": {"path": "private"}})
        self.assertEqual(value, {"tool_name": "Read", "external_request_id": "local-random-id"})
        token.assert_called_once_with(24)

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
        request = json.loads(mock_run.call_args.kwargs["input"])
        self.assertEqual(request["tool_name"], "Bash")
        self.assertEqual(len(request["external_request_id"]), 32)
        self.assertNotIn("secret", output.getvalue())
        self.assertEqual(mock_run.call_args.kwargs["env"]["AGENT_INBOX_CLIENT"], "claude")
        self.assertNotIn("API_TOKEN", mock_run.call_args.kwargs["env"])

    @patch.object(HOOK.subprocess, "run")
    def test_completion_uses_minimal_environment(self, mock_run):
        with patch.dict(os.environ, {"API_TOKEN": "private"}, clear=False):
            self.assertEqual(HOOK.main(["complete"]), 0)
        self.assertEqual(mock_run.call_args.args[0], ["agent-inbox", "complete"])
        self.assertNotIn("API_TOKEN", mock_run.call_args.kwargs["env"])

    def test_config_merge_preserves_unrelated_credentials_and_unknown_fields(self):
        opaque_value = "opaque-user-value"
        result = CONFIG.merge_config({"other": {"credential": opaque_value}, "mcpServers": {"kept": {"x": 1}}}, "/nix/store/bin/agent-inbox")
        self.assertEqual(result["other"]["credential"], opaque_value)
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

    def test_config_update_initializes_absent_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            link = Path(directory, "legacy.json")
            link.symlink_to(target)
            CONFIG.update(target, link, "agent-inbox")
            value = json.loads(target.read_text())
            self.assertEqual(value["mcpServers"]["agent-inbox"]["args"], ["mcp"])
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)

    def test_config_update_does_not_print_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            link = Path(directory, "legacy.json")
            target.write_text('{"credential":"opaque"}')
            target.chmod(0o600)
            link.symlink_to(target)
            output = StringIO()
            with redirect_stdout(output):
                CONFIG.update(target, link, "agent-inbox")
            self.assertEqual(output.getvalue(), "")

    def test_config_update_refuses_an_existing_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            link = Path(directory, "legacy.json")
            lock = target.with_name("state.json.agent-inbox.lock")
            target.write_text('{"keep":true}')
            target.chmod(0o600)
            link.symlink_to(target)
            lock.write_text("other writer")
            lock.chmod(0o600)
            with self.assertRaises(FileExistsError):
                CONFIG.update(target, link, "agent-inbox")
            self.assertEqual(json.loads(target.read_text()), {"keep": True})
            self.assertEqual(lock.read_text(), "other writer")

    def test_config_update_fails_if_contents_change_during_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            link = Path(directory, "legacy.json")
            target.write_text('{"preserved":"before"}')
            target.chmod(0o600)
            link.symlink_to(target)
            real_mkstemp = CONFIG.tempfile.mkstemp

            def mutate_target(*args, **kwargs):
                result = real_mkstemp(*args, **kwargs)
                target.write_text('{"concurrent":"writer"}')
                target.chmod(0o600)
                return result

            with patch.object(CONFIG.tempfile, "mkstemp", side_effect=mutate_target), self.assertRaisesRegex(RuntimeError, "changed during MCP merge"):
                CONFIG.update(target, link, "agent-inbox")
            self.assertEqual(json.loads(target.read_text()), {"concurrent": "writer"})
            self.assertFalse(target.with_name("state.json.agent-inbox.lock").exists())

    def test_config_update_rejects_symlink_mismatch_and_unsafe_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "state.json")
            other = Path(directory, "other.json")
            link = Path(directory, "legacy.json")
            target.write_text("{}")
            other.write_text("{}")
            target.chmod(0o600)
            link.symlink_to(other)
            with self.assertRaisesRegex(ValueError, "symlink"):
                CONFIG.update(target, link, "agent-inbox")
            link.unlink()
            link.symlink_to(target)
            target.chmod(0o644)
            with self.assertRaisesRegex(ValueError, "unsafe owner, type, or mode"):
                CONFIG.update(target, link, "agent-inbox")
