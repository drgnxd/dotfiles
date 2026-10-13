#!/usr/bin/env python3
"""Create a detached task worktree and record who created it.

Follows the git-workflow naming rule (`<slug>-<YYYYMMDD>-<NN>`), creates a
detached worktree at the resolved source commit, then writes task metadata into
that worktree's verified Git administrative directory.
The session id is read only from the variable that belongs to `--client`; a
missing or malformed value is recorded as `unknown` with a warning.

Exit codes: 0 ok; 2 usage or precondition error; 3 worktree created but the
owner metadata could not be written (worktree path and id are printed);
4 worktree created but its `.git` identity check failed (nothing is deleted).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worktree_meta as meta

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
ADD_ATTEMPTS = 5


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def common_dir(cwd: Path) -> Path:
    out = meta.git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(out)


def existing_numbers(repo: Path, common: Path, root: Path, stem: str) -> int:
    """Highest NN already used for `stem` anywhere Git or the filesystem knows it."""
    pattern = re.compile(rf"(?:^|/){re.escape(stem)}-(\d\d)$")
    seen: list[str] = []
    listing = meta.git(repo, "worktree", "list", "--porcelain").stdout
    seen += [line.split(" ", 1)[1] for line in listing.splitlines() if line.startswith("worktree ")]
    for directory in (root, common / "worktrees"):
        if directory.is_dir():
            seen += [entry.name for entry in directory.iterdir()]
    numbers = [int(m.group(1)) for item in seen if (m := pattern.search(item.rstrip("/")))]
    return max(numbers, default=0)


def verify_identity(worktree: Path, common: Path) -> str | None:
    """Return an error text, or None when `.git` is a gitfile/symlink both sides agree on."""
    try:
        meta.worktree_admin_dir(worktree, common)
    except (OSError, ValueError) as error:
        return str(error)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", required=True, help="2-4 lowercase ASCII words joined by hyphens")
    parser.add_argument("--client", required=True, choices=meta.CLIENTS)
    parser.add_argument("--task", required=True, help="single-line descriptive task label; owner metadata tokens are reserved")
    parser.add_argument("--from", dest="source", default="main", help="commit or ref to check out (default: main)")
    parser.add_argument("--parent", help="parent task or worktree ID, for a revision or integration")
    parser.add_argument("--repo", default=".", help="any path inside the repository (default: cwd)")
    parser.add_argument("--worktrees-root", help="override <state>/<repo>/worktrees")
    parser.add_argument("--allow-repository-hooks", action="store_true", help="run an inspected post-checkout hook normally")
    args = parser.parse_args(argv)

    if not SLUG_RE.match(args.slug):
        die("--slug must be 2-4 lowercase ASCII words of letters and digits joined by hyphens")
    if "\n" in args.task or "\r" in args.task or not args.task.strip():
        die("--task must be a non-empty single line")

    repo = Path(args.repo).resolve()
    common = common_dir(repo)
    configured_hooks = meta.git(repo, "config", "--path", "--get", "core.hooksPath", check=False).stdout.strip()
    configured_hook_path = Path(configured_hooks).expanduser() if configured_hooks else None
    if configured_hook_path is not None and not configured_hook_path.is_absolute() and ".." in configured_hook_path.parts:
        die("cannot safely inspect a relative core.hooksPath containing '..' before worktree creation; use an absolute path")
    main_worktree = common.parent if common.name == ".git" else common
    base = meta.git(repo, "rev-parse", "--verify", "--end-of-options", f"{args.source}^{{commit}}", check=False)
    if base.returncode != 0:
        die(f"source does not resolve to a commit: {args.source!r}")
    base_oid = base.stdout.strip()

    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    root = Path(args.worktrees_root) if args.worktrees_root else state / main_worktree.name / "worktrees"

    stem = f"{args.slug}-{datetime.now().astimezone().strftime('%Y%m%d')}"
    session, warning = meta.session_from_env(args.client)
    if warning:
        print(f"warning: {warning}", file=sys.stderr)
    try:
        description = meta.format_description(
            args.task, args.client, session, base_oid, meta.agent_pid_from_env(args.client), args.parent
        )
    except ValueError as error:
        die(str(error))

    root.mkdir(parents=True, exist_ok=True)

    last_error = ""
    for _ in range(ADD_ATTEMPTS):
        number = existing_numbers(repo, common, root, stem) + 1
        name = f"{stem}-{number:02d}"
        path = root / name
        hooks = set(meta.executable_hooks(
            repo, {"post-checkout", "reference-transaction"}, worktree_root=path, source_oid=base_oid,
        ))
        if "reference-transaction" in hooks:
            die("reference-transaction hooks are never run during task worktree creation")
        if "post-checkout" in hooks and not args.allow_repository_hooks:
            die("inspect post-checkout hooks, then pass --allow-repository-hooks to run them normally")
        result = meta.git(repo, "worktree", "add", "--detach", str(path), base_oid, check=False)
        if result.returncode == 0:
            break
        last_error = result.stderr.strip()
    else:
        die(f"git worktree add failed {ADD_ATTEMPTS} times: {last_error}")

    print(f"worktree={path}\nbase={base_oid}")
    problem = verify_identity(path, common)
    if problem:
        print(f"error: {problem}; worktree preserved", file=sys.stderr)
        return 4

    try:
        worktree_id = meta.write_worktree_owner(path, common, description)
    except (OSError, ValueError) as error:
        print(f"error: could not write worktree owner metadata: {error}; worktree preserved", file=sys.stderr)
        return 3
    print(f"worktree_id={worktree_id}")
    print(f"description={description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
