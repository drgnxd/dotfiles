import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("agent-inbox.5s.py")
SPEC = importlib.util.spec_from_file_location("agent_inbox_swiftbar", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SwiftBarTests(unittest.TestCase):
    def test_safe_text_removes_controls_bidi_and_swiftbar_delimiters(self):
        self.assertEqual(MODULE.safe_text("ok|\x1b[31m\u202etext\n"), "ok&#124;[31mtext")

    def test_render_maps_only_fixed_actions_and_valid_ids(self):
        entries = [{
            "text": "Question | safe",
            "id": "abcdefgh1234",
            "actions": [
                {"action": "answer-ui", "id": "abcdefgh1234"},
                {"action": "permission-reply", "decision": "allow", "id": "abcdefgh1234"},
                {"action": "permission-reply", "decision": "always", "id": "abcdefgh1234"},
                {"action": "shell", "id": "abcdefgh1234"},
            ],
        }, {"text": "bad", "id": "x; touch /tmp/no", "actions": []}]
        result = MODULE.render(entries)
        self.assertIn("Question &#124; safe", result)
        self.assertIn("--Reply…", result)
        self.assertIn("--Allow once", result)
        self.assertNotIn("touch", result)
        self.assertNotIn("always", result)
        self.assertNotIn("shell", result)

    def test_json_payload_maps_to_safe_menu(self):
        payload = '[{"text":"Question","id":"abcdefgh1234","actions":[{"action":"focus","id":"abcdefgh1234"}]}]'
        result = MODULE.render_json(payload)
        self.assertIn("Question", result)
        self.assertIn("--Focus session", result)

    @patch.object(MODULE.subprocess, "run")
    def test_focus_runs_fixed_helper_and_optional_app(self, mock_run):
        MODULE.run_action(["--action", "focus", "--id", "abcdefgh1234"])
        self.assertEqual(mock_run.call_args_list[0].args[0], ["agent-inbox", "focus", "abcdefgh1234"])
        self.assertEqual(mock_run.call_args_list[1].args[0], ["/usr/bin/open", "-a", "Alacritty"])
