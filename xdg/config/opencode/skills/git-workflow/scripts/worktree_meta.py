"""Shared helpers for worktree lifecycle tools.

A task worktree records a human-readable task label and structured metadata in
`branch.<branch>.description`:

    <task> client=<c> session=<id> base=<oid> pid=<pid>@<start-epoch> [parent=<branch>]

The `(client, session)` pair identifies the creating session and cleanup
responsibility. The exact branch selects one worktree when a session created
several. The task label is descriptive only and never authorizes removal.
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
OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PID_TOKEN_RE = re.compile(r"^(?:[2-9]|[1-9][0-9]+)@[0-9]+$")


def git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in INHERITED_GIT_ENV}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git(cwd: Path | str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, env=git_env(), capture_output=True, text=True, check=check
    )


def executable_hooks(
    repo: Path, names: set[str], *, worktree_root: Path | None = None, source_oid: str | None = None,
) -> tuple[str, ...]:
    configured = git(repo, "config", "--path", "--get", "core.hooksPath", check=False).stdout.strip()
    configured_path = Path(configured).expanduser() if configured else None

    def scan(directory: Path) -> set[str]:
        return {
            path.name for path in directory.iterdir()
            if path.name in names and path.is_file() and not path.name.endswith(".sample") and os.access(path, os.X_OK)
        } if directory.is_dir() else set()

    if configured_path is None:
        hook_dir = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "hooks").stdout.strip())
        return tuple(sorted(scan(hook_dir)))
    if configured_path.is_absolute():
        return tuple(sorted(scan(configured_path)))

    active = scan(repo / configured_path)
    if worktree_root is None:
        return tuple(sorted(active))
    prospective = worktree_root / configured_path
    active.update(scan(prospective))
    if source_oid is None:
        return tuple(sorted(active))

    root = worktree_root.resolve()
    prospective = prospective.resolve(strict=False)
    try:
        relative_root = prospective.relative_to(root)
    except ValueError:
        return tuple(sorted(active))
    relative_text = relative_root.as_posix()

    def source_mode(path: str) -> str | None:
        result = git(repo, "--literal-pathspecs", "ls-tree", "-z", source_oid, "--", path, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"cannot inspect source tree hook path {path}: {result.stderr.strip()}")
        for record in result.stdout.split("\0"):
            if not record:
                continue
            metadata, separator, entry_path = record.partition("\t")
            if not separator:
                raise RuntimeError("git ls-tree returned a malformed hook entry")
            if entry_path == path:
                return metadata.split(" ", 1)[0]
        return None

    prefix = "" if relative_text == "." else relative_text + "/"
    for name in names:
        expected = prefix + name
        parts = expected.split("/")
        for depth in range(1, len(parts) + 1):
            entry_path = "/".join(parts[:depth])
            mode = source_mode(entry_path)
            if mode is None:
                break
            if mode == "120000":
                active.add(name)
                break
            if depth == len(parts):
                if mode == "100755":
                    active.add(name)
                break
            if mode not in ("040000",):
                break
    return tuple(sorted(active))


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


def current_session_identity(env: dict[str, str] | None = None) -> tuple[str, str] | None:
    """Return the unique valid client/session identity exposed by this process."""
    env = os.environ if env is None else env
    present = [
        (client, env.get(name, ""))
        for client, name in SESSION_ENV.items()
        if env.get(name, "")
    ]
    if len(present) != 1:
        return None
    client, session = present[0]
    pattern = SESSION_RE.get(client)
    if pattern is None or not pattern.fullmatch(session):
        return None
    return client, session


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
    if not task.strip():
        raise ValueError("task text must not be empty")
    if any(token.partition("=")[0] in TRAILER_KEYS for token in task.split() if "=" in token):
        raise ValueError("task text must not contain owner metadata tokens")
    if client not in CLIENTS:
        raise ValueError(f"unknown client {client!r}")
    if session != UNKNOWN and (client not in SESSION_RE or not SESSION_RE[client].fullmatch(session)):
        raise ValueError(f"invalid session id for client {client!r}")
    if not OID_RE.fullmatch(base):
        raise ValueError("base must be a full Git object ID")
    if pid is not None and pid <= 1:
        raise ValueError("pid must be greater than 1")
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


def parse_owner_description(text: str) -> tuple[str, str, str] | None:
    """Return (task, client, session) only for a complete, unambiguous owner trailer."""
    task, trailer = parse_description(text)
    if not task or not {"client", "session", "base"}.issubset(trailer):
        return None
    if any(token.partition("=")[0] in TRAILER_KEYS for token in task.split() if "=" in token):
        return None

    tokens = text.strip().split()
    trailer_tokens = tokens[len(task.split()):]
    keys = [token.partition("=")[0] for token in trailer_tokens]
    expected = ["client", "session", "base"]
    if "pid" in trailer:
        expected.append("pid")
    if "parent" in trailer:
        expected.append("parent")
    if keys != expected:
        return None

    client = trailer["client"]
    session = trailer["session"]
    session_pattern = SESSION_RE.get(client)
    if session_pattern is None or not session_pattern.fullmatch(session):
        return None
    if not OID_RE.fullmatch(trailer["base"]):
        return None
    if "pid" in trailer and not PID_TOKEN_RE.fullmatch(trailer["pid"]):
        return None
    return task, client, session
