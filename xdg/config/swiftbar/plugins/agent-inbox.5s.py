#!/usr/bin/env python3
"""Render safe agent-inbox entries as fixed SwiftBar actions."""

import html
import json
import os
import re
import subprocess
import sys
import unicodedata

ID = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
PLUGIN = __file__
ACTION_NAMES = {"answer-ui", "permission-reply", "focus", "ack"}
ENV_KEYS = ("PATH", "HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID")


def helper_env():
    return {**{key: os.environ[key] for key in ENV_KEYS if key in os.environ}, "AGENT_INBOX_CLIENT": "swiftbar"}


def safe_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = "".join(char for char in value if unicodedata.category(char) not in {"Cc", "Cf", "Cs"})
    return html.escape(" ".join(cleaned.split()), quote=True).replace("|", "&#124;")


def render(entries: object) -> str:
    lines = ["Agent inbox"]
    if not isinstance(entries, list):
        return "\n".join(lines)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        event_id = entry.get("id")
        if not isinstance(event_id, str) or not ID.fullmatch(event_id):
            continue
        label = safe_text(entry.get("text"))
        if not label:
            continue
        lines.extend(["---", label])
        actions = entry.get("actions")
        if not isinstance(actions, list):
            continue
        for action in actions:
            if not isinstance(action, dict) or action.get("id") != event_id:
                continue
            kind = action.get("action")
            if kind not in ACTION_NAMES:
                continue
            decision = action.get("answer", action.get("decision", action.get("response", action.get("value"))))
            if kind == "permission-reply" and decision not in {"allow", "deny"}:
                continue
            title = {
                "answer-ui": "Reply…",
                "permission-reply": "Allow once" if decision == "allow" else "Deny",
                "focus": "Focus session",
                "ack": "Acknowledge",
            }[kind]
            args = ["python3", PLUGIN, "--action", kind, "--id", event_id]
            if decision in {"allow", "deny"}:
                args.extend(["--decision", decision])
            lines.append(f"--{title} | bash=/usr/bin/env " + " ".join(f"param{i + 1}={html.escape(arg, quote=True)}" for i, arg in enumerate(args)))
    return "\n".join(lines)


def render_json(payload: str) -> str:
    return render(json.loads(payload))


def run_action(arguments: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=sorted(ACTION_NAMES), required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--decision", choices=["allow", "deny"])
    parsed = parser.parse_args(arguments)
    if not ID.fullmatch(parsed.id):
        return 2
    command = ["agent-inbox"]
    env = helper_env()
    if parsed.action == "answer-ui":
        command.extend(["answer-ui", parsed.id])
    elif parsed.action == "permission-reply" and parsed.decision:
        command.extend(["permission-reply", parsed.id, parsed.decision])
    elif parsed.action == "focus":
        command.extend(["focus", parsed.id])
        subprocess.run(command, check=False, env=env)
        subprocess.run(["/usr/bin/open", "-a", "Alacritty"], check=False, env=env)
        return 0
    elif parsed.action == "ack":
        command.extend(["ack", parsed.id])
    else:
        return 2
    subprocess.run(command, check=False, env=env)
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        return run_action(sys.argv[1:])
    try:
        result = subprocess.run(["agent-inbox", "swiftbar"], check=True, capture_output=True, text=True, timeout=3, env=helper_env())
        print(render_json(result.stdout))
        return 0
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        print("Agent inbox | color=gray")
        return 0


if __name__ == "__main__":
    sys.exit(main())
