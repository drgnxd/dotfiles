"""Read-only task metadata validation used by the worktree guard."""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

CLIENTS = ("claude", "opencode", "copilot")
UNKNOWN = "unknown"
TRAILER_KEYS = ("client", "session", "base", "pid", "parent")
SESSION_RE = {
    "claude": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
    "opencode": re.compile(r"^ses_[A-Za-z0-9]{26}$"),
}
OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PID_TOKEN_RE = re.compile(r"^(?:[2-9]|[1-9][0-9]+)@[0-9]+$")
TASK_METADATA_FILE = "agent-task"
WTCTL_METADATA_FILE = "agent-task.json"
WTCTL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}-[0-9]{8}-[0-9a-f]{8}$")


def git_env() -> dict[str, str]:
    inherited = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX",
    }
    env = {key: value for key, value in os.environ.items() if key not in inherited}
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def parse_description(text: str) -> tuple[str, dict[str, str]]:
    tokens = text.strip().split(" ")
    trailer: dict[str, str] = {}
    while tokens:
        key, separator, value = tokens[-1].partition("=")
        if not separator or key not in TRAILER_KEYS or not value or key in trailer:
            break
        trailer[key] = value
        tokens.pop()
    return " ".join(tokens), trailer


def parse_owner_description(text: str) -> tuple[str, str, str] | None:
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
    client, session = trailer["client"], trailer["session"]
    session_pattern = SESSION_RE.get(client)
    if session_pattern is None or not session_pattern.fullmatch(session):
        return None
    if not OID_RE.fullmatch(trailer["base"]):
        return None
    if "pid" in trailer and not PID_TOKEN_RE.fullmatch(trailer["pid"]):
        return None
    return task, client, session


def worktree_admin_dir(worktree: Path, common_dir: Path) -> Path:
    dot_git = worktree / ".git"
    if dot_git.is_symlink():
        admin = dot_git.resolve()
    elif dot_git.is_file():
        text = dot_git.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            raise ValueError(f"{dot_git} is not a Git worktree pointer")
        pointer = Path(text.split(":", 1)[1].strip())
        admin = pointer if pointer.is_absolute() else worktree / pointer
        admin = admin.resolve()
    else:
        raise ValueError(f"{dot_git} is neither a gitfile nor a symlink")
    expected_root = (common_dir / "worktrees").resolve()
    if admin.parent.resolve() != expected_root:
        raise ValueError(f"{dot_git} points outside {expected_root}: {admin}")
    back = admin / "gitdir"
    if not back.is_file():
        raise ValueError(f"{back} is missing")
    back_pointer = Path(back.read_text(encoding="utf-8").strip())
    if not back_pointer.is_absolute():
        back_pointer = admin / back_pointer
    if back_pointer.name != ".git" or back_pointer.parent.resolve() != worktree.resolve():
        raise ValueError(f"{back} does not point back to {dot_git}")
    return admin


def read_worktree_owner(
    worktree: Path, common_dir: Path
) -> tuple[str, str, tuple[str, str, str, str]] | None:
    admin = worktree_admin_dir(worktree, common_dir)
    owner_file = admin / TASK_METADATA_FILE
    try:
        mode = owner_file.lstat().st_mode
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(mode):
        raise ValueError(f"{owner_file} is not a regular file")
    description = owner_file.read_text(encoding="utf-8").strip()
    task, trailer = parse_description(description)
    client, session = trailer.get("client", ""), trailer.get("session", "")
    parsed = parse_owner_description(description)
    if parsed is None:
        tokens = description.split()
        trailer_tokens = tokens[len(task.split()):]
        keys = [token.partition("=")[0] for token in trailer_tokens]
        expected = ["client", "session", "base"]
        if "pid" in trailer:
            expected.append("pid")
        if "parent" in trailer:
            expected.append("parent")
        unknown_session = (
            task
            and client in CLIENTS
            and session == UNKNOWN
            and keys == expected
            and not any(token.partition("=")[0] in TRAILER_KEYS for token in task.split() if "=" in token)
        )
        if not unknown_session:
            raise ValueError(f"{owner_file} contains invalid task owner metadata")
    else:
        task, client, session = parsed
    base = trailer.get("base", "")
    if not OID_RE.fullmatch(base):
        raise ValueError(f"{owner_file} contains an invalid base OID")
    return admin.name, description, (task, client, session, base)


def read_wtctl_marker(worktree: Path, common_dir: Path) -> dict | None:
    admin = worktree_admin_dir(worktree, common_dir)
    marker = admin / WTCTL_METADATA_FILE
    try:
        if not stat.S_ISREG(marker.lstat().st_mode):
            return None
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    # Mirror wtctl's parser so the guard never trusts a marker wtctl would reject.
    def is_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    if not isinstance(data, dict) or data.get("tool") != "wtctl":
        return None
    if not is_int(data.get("schema")) or data.get("schema") != 1:
        return None
    owner = data.get("owner")
    if not isinstance(owner, dict):
        return None
    pid = owner.get("pid")
    if not is_int(pid) or not 1 < pid <= 2**31 - 1:
        return None
    if not isinstance(owner.get("start"), str) or not isinstance(owner.get("client"), str):
        return None
    base = data.get("base")
    if not isinstance(base, str) or not OID_RE.fullmatch(base):
        return None
    task_id, recorded = data.get("task_id"), data.get("worktree")
    if not isinstance(task_id, str) or not WTCTL_ID_RE.fullmatch(task_id) or not isinstance(recorded, str):
        return None
    if not Path(recorded).is_absolute() or Path(recorded).resolve() != worktree.resolve():
        return None
    return data
