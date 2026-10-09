"""Shared helpers for worktree-create.py and worktree-audit.py.

A task worktree records its owner in `branch.<branch>.description` as the free
task text followed by a fixed trailer of `key=value` tokens:

    <task> client=<c> session=<id> base=<oid> pid=<pid>@<start-epoch> [parent=<branch>]

`client=` comes first so that an `--expect-owner "<task> client=<c>"` string
recorded before the trailer grew still matches as a substring.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

CLIENTS = ("claude", "opencode", "copilot")
UNKNOWN = "unknown"
TRAILER_KEYS = ("client", "session", "base", "pid", "parent")
SESSION_RE = {
    "claude": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    "opencode": re.compile(r"^ses_[A-Za-z0-9]{26}$"),
}
SESSION_ENV = {"claude": "CLAUDE_CODE_SESSION_ID", "opencode": "OPENCODE_SESSION_ID"}
PID_ENV = {"claude": "CLAUDE_PID", "opencode": "OPENCODE_PID"}
INHERITED_GIT_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX",
)
PID_START_TOLERANCE = 5


def git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in INHERITED_GIT_ENV}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git(cwd: Path | str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, env=git_env(), capture_output=True, text=True, check=check
    )


def session_from_env(client: str, env: dict[str, str] | None = None) -> tuple[str, str | None]:
    """Return (session id or "unknown", warning). Reads only the client's own variable."""
    env = os.environ if env is None else env
    name = SESSION_ENV.get(client)
    if name is None:
        return UNKNOWN, None
    value = env.get(name, "")
    if SESSION_RE[client].match(value):
        return value, None
    return UNKNOWN, f"{name} is unset or malformed; recording session=unknown"


def agent_pid_from_env(client: str, env: dict[str, str] | None = None) -> int | None:
    env = os.environ if env is None else env
    name = PID_ENV.get(client)
    value = env.get(name, "") if name else ""
    return int(value) if value.isdigit() and int(value) > 1 else None


def _parse_etime(text: str) -> int | None:
    match = re.fullmatch(r"(?:(?:(\d+)-)?(\d+):)?(\d+):(\d+)", text.strip())
    if not match:
        return None
    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


def process_start_epoch(pid: int, now: float | None = None) -> int | None:
    """Start time of a live process via `ps etime`, or None when it is not running."""
    result = subprocess.run(
        ["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True, check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    elapsed = _parse_etime(result.stdout) if result.returncode == 0 else None
    if elapsed is None:
        return None
    return int((time.time() if now is None else now) - elapsed)


def format_description(
    task: str, client: str, session: str, base: str, pid: int | None, parent: str | None
) -> str:
    if "\n" in task or "\r" in task:
        raise ValueError("task text must be a single line")
    parts = [task.strip(), f"client={client}", f"session={session}", f"base={base}"]
    if pid is not None:
        start = process_start_epoch(pid)
        if start is not None:
            parts.append(f"pid={pid}@{start}")
    if parent:
        parts.append(f"parent={parent}")
    return " ".join(parts)


def parse_description(text: str) -> tuple[str, dict[str, str]]:
    """Split a description into task text and the trailing key=value block."""
    tokens = text.strip().split(" ")
    trailer: dict[str, str] = {}
    while tokens:
        key, sep, value = tokens[-1].partition("=")
        if not sep or key not in TRAILER_KEYS or not value or key in trailer:
            break
        trailer[key] = value
        tokens.pop()
    return " ".join(tokens), trailer
