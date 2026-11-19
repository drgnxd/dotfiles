import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).parent.parent
SPEC = importlib.util.spec_from_file_location("validate_opencode_setup", BASE / "validate_opencode_setup.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

CONFIG_PATH = BASE / "opencode.json"
ORIGINAL = CONFIG_PATH.read_text(encoding="utf-8")
BASELINE = json.loads(ORIGINAL)


def errors_for(mutate=None, *, text=None):
    config = copy.deepcopy(BASELINE)
    if mutate:
        mutate(config)
    served = json.dumps(config) if text is None else text
    real_read_text = Path.read_text

    def read_text(self, *args, **kwargs):
        return served if self == CONFIG_PATH else real_read_text(self, *args, **kwargs)

    errors: list[str] = []
    with patch.object(Path, "read_text", read_text):
        validator.validate_config(errors)
    return errors


class ValidatorDetectionTest(unittest.TestCase):
    def assertDetects(self, mutate, expected):
        errors = errors_for(mutate)
        self.assertTrue(any(expected in error for error in errors), (expected, errors))

    def test_current_config_is_clean(self):
        self.assertEqual(errors_for(), [])

    def test_permission_and_tool_regressions_are_detected(self):
        cases = (
            (lambda c: c["agent"]["reviewer"]["permission"].pop("external_directory"), "reviewer must deny external directories"),
            (lambda c: c["agent"]["reviewer"]["permission"].update(edit="allow"), "reviewer must allow only read-only review tools"),
            (lambda c: c["agent"]["researcher"]["permission"].update(bash="allow"), "researcher must preserve Code Mode"),
            (lambda c: c["agent"]["researcher"]["tools"].update(bash=True), "researcher must expose only"),
            (lambda c: c["agent"]["browser-operator"]["tools"].update(playwright_browser_type=True), "browser-operator must expose only"),
            (lambda c: c["agent"]["producer"]["permission"].update(webfetch="allow"), "producer must deny webfetch"),
            (lambda c: c["agent"]["producer"]["permission"].pop("task"), "producer must not delegate"),
            (lambda c: c["agent"]["pdf-reader"]["permission"].update(bash="allow"), "pdf-reader must read only PDF paths"),
            (lambda c: c["agent"]["main"]["permission"]["task"].update(general="allow"), "main must be the only routed primary"),
            (lambda c: c["agent"]["main"]["permission"].pop("playwright_*"), "main must not use Playwright directly"),
            (lambda c: c["agent"]["strategist"]["permission"].update(edit="allow"), "strategist must be read-only"),
            (lambda c: c["agent"]["build"].clear(), "built-in build must be disabled"),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                self.assertDetects(mutate, expected)

    def test_exposure_outside_the_researcher_is_detected(self):
        for tool, expected in (
            ("playwright_browser_click", "click tool"),
            ("playwright_browser_press_key", "press-key tool"),
            ("playwright_browser_type", "form and type tools"),
        ):
            with self.subTest(tool=tool):
                self.assertDetects(lambda c, t=tool: c["agent"]["producer"]["permission"].update({f"{t}*": "allow"}), expected)
        self.assertDetects(lambda c: c["agent"]["producer"]["permission"].update(fetch_pdf="allow"), "only researcher may request fetch_pdf")

    def test_routing_drift_is_detected(self):
        self.assertDetects(lambda c: c["agent"]["main"].update(variant="high"), "main must use Luna Medium")
        self.assertDetects(lambda c: c["agent"]["producer"].update(model="openai/gpt-6-luna"), "producer model/variant mismatch")
        self.assertDetects(lambda c: c["agent"]["reviewer"].update(color="#000000"), "reviewer color mismatch")
        self.assertDetects(lambda c: c["agent"].update(extra={"mode": "subagent"}), "approved route set")
        self.assertDetects(lambda c: c.update(default_agent="build"), "default_agent must be main")
        self.assertDetects(lambda c: c.update(enabled_providers=["openai", "other"]), "only the openai provider")

    def test_structurally_broken_config_is_reported_not_a_traceback(self):
        for mutate in (
            lambda c: c.update(permission="deny"),
            lambda c: c["agent"].update(researcher="oops"),
            lambda c: c.update(experimental=[]),
        ):
            with self.subTest():
                errors = errors_for(mutate)
                self.assertTrue(errors)
        self.assertEqual(errors_for(text="[]"), ["opencode.json must be an object whose agent entry is an object"])
        self.assertEqual(errors_for(text='{"agent": []}'), ["opencode.json must be an object whose agent entry is an object"])
        self.assertTrue(errors_for(text="{broken")[0].startswith("Invalid JSON"))


if __name__ == "__main__":
    unittest.main()
