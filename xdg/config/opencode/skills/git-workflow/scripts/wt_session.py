#!/usr/bin/env -S uv run --script
"""Create a detached task worktree and record which session created it.

The record is a single write-once file in the worktree's Git administration
directory, so Git deletes it together with the worktree. It is supporting
evidence only; it never authorizes removal or integration.
"""

import argparse
import os
import re
import secrets
import subprocess
import sys
import time

MARKER = "session-owner"
MARKER_VERSION = "1"
MAX_MARKER_BYTES = 4096
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")
SESSION_RE = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")


class Failure(Exception):
    pass


def git(*args, cwd=None):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise Failure(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def current_session():
    found = []
    for var, tool in (
        ("OPENCODE_SESSION_ID", "opencode"),
        ("CLAUDE_CODE_SESSION_ID", "claude-code"),
    ):
        value = os.environ.get(var, "")
        if value:
            if not SESSION_RE.match(value):
                raise Failure(f"{var} is not a valid session ID")
            found.append((tool, value))
    if len(found) > 1:
        raise Failure("both OpenCode and Claude Code session IDs are set; refusing to guess")
    return found[0] if found else ("unknown", "unknown")


def admin_dir(worktree):
    return os.path.realpath(git("rev-parse", "--absolute-git-dir", cwd=worktree))


def verify_pointers(worktree, admin):
    dot_git = os.path.join(worktree, ".git")
    if os.path.isfile(dot_git) and not os.path.islink(dot_git):
        with open(dot_git, encoding="utf-8") as handle:
            line = handle.read().strip()
        if not line.startswith("gitdir: "):
            raise Failure(f"unexpected .git file in {worktree}")
        forward = os.path.realpath(line[len("gitdir: "):])
    else:
        forward = os.path.realpath(dot_git)
    if forward != admin:
        raise Failure(f".git of {worktree} does not point to {admin}")
    with open(os.path.join(admin, "gitdir"), encoding="utf-8") as handle:
        backward = os.path.realpath(handle.read().strip())
    if backward != os.path.realpath(dot_git):
        raise Failure(f"{admin}/gitdir does not point back to {worktree}")


def write_marker(admin, fields):
    body = "".join(f"{key}={value}\n" for key, value in fields.items())
    fd = os.open(
        os.path.join(admin, MARKER),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())


def read_marker(worktree):
    admin = admin_dir(worktree)
    try:
        fd = os.open(os.path.join(admin, MARKER), os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Failure(f"unsafe marker in {admin}: {error}") from error
    with os.fdopen(fd, "rb") as handle:
        data = handle.read(MAX_MARKER_BYTES + 1)
    if len(data) > MAX_MARKER_BYTES:
        raise Failure(f"marker in {admin} is too large")
    fields = {}
    for line in data.decode("utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if not sep or key in fields:
            raise Failure(f"malformed marker in {admin}")
        fields[key] = value
    if fields.get("version") != MARKER_VERSION:
        raise Failure(f"unsupported marker version in {admin}")
    if fields.get("path") != os.path.realpath(worktree):
        raise Failure(f"marker in {admin} names a different path: {fields.get('path')}")
    return fields


def repo_name():
    common = os.path.realpath(git("rev-parse", "--git-common-dir"))
    if os.path.basename(common) == ".git":
        common = os.path.dirname(common)
    return os.path.basename(common)


def cmd_whoami(_args):
    tool, session = current_session()
    print(f"tool={tool} session={session}")
    return 0 if session != "unknown" else 1


def cmd_create(args):
    if not NAME_RE.match(args.name):
        raise Failure("name must match [A-Za-z0-9][A-Za-z0-9._-]{0,80}")
    tool, session = current_session()
    base = git("rev-parse", "--verify", "--end-of-options", f"{args.base}^{{commit}}")
    state = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    path = os.path.join(
        os.path.realpath(state),
        repo_name(),
        "worktrees",
        f"{args.name}-{secrets.token_hex(4)}",
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    git("worktree", "add", "--detach", path, base)
    # A failure from here on preserves the worktree: it exists and is unrecorded.
    try:
        path = os.path.realpath(path)
        if git("rev-parse", "HEAD", cwd=path) != base:
            raise Failure("new worktree HEAD does not match the base OID")
        if subprocess.run(
            ["git", "symbolic-ref", "-q", "HEAD"], cwd=path, capture_output=True, check=False
        ).returncode == 0:
            raise Failure("new worktree HEAD is not detached")
        admin = admin_dir(path)
        verify_pointers(path, admin)
        write_marker(
            admin,
            {
                "version": MARKER_VERSION,
                "session": session,
                "tool": tool,
                "base": base,
                "path": path,
                "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
    except Failure as error:
        raise Failure(f"worktree {path} was created but is unrecorded and preserved: {error}") from error
    if session == "unknown":
        print("warning: no session ID found; recorded as unknown", file=sys.stderr)
    print(f"path={path}")
    print(f"base={base}")
    print(f"tool={tool} session={session}")
    return 0


def cmd_owner(args):
    path = os.path.realpath(args.path)
    top = os.path.realpath(git("rev-parse", "--show-toplevel", cwd=path))
    if top != path:
        raise Failure(f"{path} is not a worktree root")
    fields = read_marker(path)
    if fields is None:
        print("status=unrecorded")
        return 0
    tool, session = current_session()
    recorded = (fields.get("tool"), fields.get("session"))
    if "unknown" in recorded or session == "unknown":
        status = "unknown"
    elif recorded == (tool, session):
        status = "mine"
    else:
        status = "other"
    print(f"status={status}")
    print(f"session={fields.get('session')} tool={fields.get('tool')}")
    print(f"base={fields.get('base')} created={fields.get('created')}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="print the current session ID").set_defaults(func=cmd_whoami)
    create = sub.add_parser("create", help="create and record a detached worktree")
    create.add_argument("name")
    create.add_argument("--base", default="main")
    create.set_defaults(func=cmd_create)
    owner = sub.add_parser("owner", help="compare a worktree's record with this session")
    owner.add_argument("path", nargs="?", default=".")
    owner.set_defaults(func=cmd_owner)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Failure as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
