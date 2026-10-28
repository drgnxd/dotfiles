#!/usr/bin/env python3
"""Bridge Claude's permission hook to the safe one-shot inbox protocol."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys

ENV_KEYS = ("PATH", "HOME", "XDG_STATE_HOME", "ZELLIJ_SESSION_NAME", "ZELLIJ_PANE_ID")


def helper_env() -> dict[str, str]:
    env = {key: os.environ[key] for key in ENV_KEYS if key in os.environ}
    env["AGENT_INBOX_CLIENT"] = "claude"
    return env

def safe_request(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    name = value.get("tool_name")
    if not isinstance(name, str) or not name or len(name) > 128:
        return None
    result = {"tool_name": name}
    request_id = value.get("permission_request_id", value.get("request_id"))
    if not isinstance(request_id, str) or not request_id or len(request_id) > 256:
        request_id = secrets.token_urlsafe(24)
    result["external_request_id"] = request_id
    return result


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments == ["complete"]:
        try:
            subprocess.run(["agent-inbox", "complete"], env=helper_env(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=True)
        except (OSError, subprocess.SubprocessError):
            pass
        return 0
    try:
        request = safe_request(json.load(sys.stdin))
    except (json.JSONDecodeError, OSError):
        request = None
    if request is None:
        print("{}")
        return 0
    try:
        result = subprocess.run(
            ["agent-inbox", "permission-request"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=605,
            check=True,
            env=helper_env(),
        )
    except (OSError, subprocess.SubprocessError):
        print("{}")
        return 0
    decision = result.stdout.strip()
    if decision not in {"allow", "deny"}:
        print("{}")
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": decision},
    }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
