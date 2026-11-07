#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Create a detached task worktree and record which session created it.

The record is a single write-once file in the worktree's Git administration
directory, so Git deletes it together with the worktree (`git worktree move`
keeps it but invalidates it, because it names the original path). It is
supporting evidence only; it never authorizes removal or integration.
"""

import argparse
import os
import re
import secrets
import stat
import subprocess
import sys
import time

MARKER = "session-owner"
MARKER_VERSION = "1"
MAX_MARKER_BYTES = 4096
FIELDS = ("version", "session", "tool", "base", "path", "created")
TOOLS = ("opencode", "claude-code", "unknown")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}\Z")
SESSION_RE = re.compile(r"[A-Za-z0-9_.-]{1,128}\Z")
OID_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
TIME_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")
# Inherited from a hook context or a user shell, these would redirect Git to another repository.
GIT_ENV_DROP = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_NAMESPACE", "GIT_PREFIX",
)
OWNER_EXIT = {"mine": 0, "other": 1, "unknown": 3, "unrecorded": 4}
ERROR_EXIT = 2


class Failure(Exception):
    pass


def git(*args, cwd=None, check=True):
    env = {k: v for k, v in os.environ.items() if k not in GIT_ENV_DROP}
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=env, capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise Failure(f"git {' '.join(args)}: {error}") from error
    if check and result.returncode != 0:
        raise Failure(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result


def current_session():
    found = []
    for var, tool in (
        ("OPENCODE_SESSION_ID", "opencode"),
        ("CLAUDE_CODE_SESSION_ID", "claude-code"),
    ):
        value = os.environ.get(var, "")
        if value:
            if not SESSION_RE.match(value) or value == "unknown":
                raise Failure(f"{var} is not a valid session ID")
            found.append((tool, value))
    if len(found) > 1:
        raise Failure("both OpenCode and Claude Code session IDs are set; refusing to guess")
    return found[0] if found else ("unknown", "unknown")


def state_base():
    value = os.environ.get("XDG_STATE_HOME", "")
    if not os.path.isabs(value):
        value = os.path.expanduser("~/.local/state")
    return os.path.realpath(value)


def resolve(base, raw):
    return os.path.realpath(raw if os.path.isabs(raw) else os.path.join(base, raw))


def admin_dir(worktree):
    return os.path.realpath(git("rev-parse", "--absolute-git-dir", cwd=worktree).stdout.strip())


def verify_pointers(worktree, admin):
    dot_git = os.path.join(worktree, ".git")
    if os.path.isfile(dot_git) and not os.path.islink(dot_git):
        with open(dot_git, encoding="utf-8") as handle:
            line = handle.read().strip()
        if not line.startswith("gitdir: "):
            raise Failure(f"unexpected .git file in {worktree}")
        forward = resolve(worktree, line[len("gitdir: "):])
    else:
        forward = os.path.realpath(dot_git)
    if forward != admin:
        raise Failure(f".git of {worktree} does not point to {admin}")
    with open(os.path.join(admin, "gitdir"), encoding="utf-8") as handle:
        raw = handle.read().strip()
    target = raw if os.path.isabs(raw) else os.path.join(admin, raw)
    if os.path.basename(target) != ".git" or os.path.realpath(os.path.dirname(target)) != os.path.realpath(worktree):
        raise Failure(f"{admin}/gitdir does not point back to {worktree}")


def write_marker(admin, fields):
    if any("\n" in str(value) for value in fields.values()):
        raise Failure("marker values must not contain newlines")
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
        fd = os.open(os.path.join(admin, MARKER), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise Failure(f"unsafe marker in {admin}: {error}") from error
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise Failure(f"unsafe marker in {admin}: not a regular file")
    with os.fdopen(fd, "rb") as handle:
        data = handle.read(MAX_MARKER_BYTES + 1)
    if len(data) > MAX_MARKER_BYTES:
        raise Failure(f"marker in {admin} is too large")
    fields = {}
    for line in data.decode("utf-8").splitlines():
        key, sep, value = line.partition("=")
        if not sep or key in fields:
            raise Failure(f"malformed marker in {admin}")
        fields[key] = value
    if tuple(sorted(fields)) != tuple(sorted(FIELDS)):
        raise Failure(f"marker in {admin} does not have exactly the expected fields")
    if fields["version"] != MARKER_VERSION:
        raise Failure(f"unsupported marker version in {admin}")
    known = fields["tool"] != "unknown"
    valid = (
        fields["tool"] in TOOLS
        and (known == (fields["session"] != "unknown"))
        and (not known or SESSION_RE.match(fields["session"]))
        and OID_RE.match(fields["base"])
        and TIME_RE.match(fields["created"])
    )
    if not valid:
        raise Failure(f"marker in {admin} has invalid values")
    if fields["path"] != os.path.realpath(worktree):
        raise Failure(f"marker in {admin} names a different path: {fields['path']}")
    return fields


def repo_name():
    common = os.path.realpath(git("rev-parse", "--git-common-dir").stdout.strip())
    if os.path.basename(common) == ".git":
        common = os.path.dirname(common)
    return os.path.basename(common)


def registered(path):
    listing = git("worktree", "list", "--porcelain").stdout.splitlines()
    return any(
        line.startswith("worktree ") and os.path.realpath(line[len("worktree "):]) == path
        for line in listing
    )


def cmd_whoami(_args):
    tool, session = current_session()
    print(f"tool={tool} session={session}")
    return 0 if session != "unknown" else 1


def cmd_create(args):
    if not NAME_RE.match(args.name):
        raise Failure("name must match [A-Za-z0-9][A-Za-z0-9._-]{0,80}")
    tool, session = current_session()
    base = git("rev-parse", "--verify", "--end-of-options", f"{args.base}^{{commit}}").stdout.strip()
    path = os.path.join(
        state_base(), repo_name(), "worktrees", f"{args.name}-{secrets.token_hex(4)}"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        git("worktree", "add", "--detach", path, base)
    except Failure as error:
        # Git keeps the worktree when only a post-checkout hook fails.
        if os.path.lexists(path) or registered(path):
            raise Failure(f"worktree {path} exists but is unrecorded and preserved; inspect before retrying: {error}") from error
        raise
    try:
        path = os.path.realpath(path)
        if git("rev-parse", "HEAD", cwd=path).stdout.strip() != base:
            raise Failure("new worktree HEAD does not match the base OID")
        if git("symbolic-ref", "-q", "HEAD", cwd=path, check=False).returncode == 0:
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
    except (Failure, OSError, UnicodeError) as error:
        raise Failure(f"worktree {path} exists but is unrecorded and preserved: {error}") from error
    if session == "unknown":
        print("warning: no session ID found; recorded as unknown", file=sys.stderr)
    print(f"path={path}")
    print(f"base={base}")
    print(f"tool={tool} session={session}")
    return 0


def cmd_owner(args):
    path = os.path.realpath(args.path)
    top = os.path.realpath(git("rev-parse", "--show-toplevel", cwd=path).stdout.strip())
    if top != path:
        raise Failure(f"{path} is not a worktree root")
    fields = read_marker(path)
    if fields is None:
        status = "unrecorded"
    else:
        tool, session = current_session()
        recorded = (fields["tool"], fields["session"])
        if "unknown" in recorded or session == "unknown":
            status = "unknown"
        elif recorded == (tool, session):
            status = "mine"
        else:
            status = "other"
    print(f"status={status}")
    if fields is not None:
        print(f"session={fields['session']} tool={fields['tool']}")
        print(f"base={fields['base']} created={fields['created']}")
    return OWNER_EXIT[status]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="print the current session ID").set_defaults(func=cmd_whoami)
    create = sub.add_parser("create", help="create and record a detached worktree")
    create.add_argument("name")
    create.add_argument("--base", default="refs/heads/main")
    create.set_defaults(func=cmd_create)
    owner = sub.add_parser(
        "owner",
        help="compare a worktree's record with this session "
        "(exit 0 mine, 1 other, 3 unknown, 4 unrecorded, 2 error)",
    )
    owner.add_argument("path", nargs="?", default=".")
    owner.set_defaults(func=cmd_owner)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (Failure, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return ERROR_EXIT


if __name__ == "__main__":
    sys.exit(main())
