#!/usr/bin/env python3
"""Create a task worktree and record who created it.

Follows the git-workflow naming rule (`<slug>-<YYYYMMDD>-<NN>`, branch
`task/<slug>-<YYYYMMDD>-<NN>`), creates branch and worktree with one
`git worktree add -b`, then writes `branch.<branch>.description` as the task
text plus a trailer (client, session, base OID, agent pid, optional parent).
The session id is read only from the variable that belongs to `--client`; a
missing or malformed value is recorded as `unknown` with a warning.

Exit codes: 0 ok; 2 usage or precondition error; 3 worktree created but the
description could not be written (path and branch are still printed);
4 worktree created but its `.git` identity check failed (nothing is deleted).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worktree_meta as meta

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
ADD_ATTEMPTS = 5
CONFIG_RETRY_DELAYS = (0.2, 0.5, 1.0)


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
    refs = meta.git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes").stdout
    seen += refs.splitlines()
    listing = meta.git(repo, "worktree", "list", "--porcelain").stdout
    seen += [line.split(" ", 1)[1] for line in listing.splitlines() if line.startswith(("worktree ", "branch "))]
    for directory in (root, common / "worktrees"):
        if directory.is_dir():
            seen += [entry.name for entry in directory.iterdir()]
    numbers = [int(m.group(1)) for item in seen if (m := pattern.search(item.rstrip("/")))]
    return max(numbers, default=0)


def verify_identity(worktree: Path, common: Path) -> str | None:
    """Return an error text, or None when `.git` is a gitfile/symlink both sides agree on."""
    dot_git = worktree / ".git"
    if dot_git.is_symlink():
        admin = dot_git.resolve()
    elif dot_git.is_file():
        text = dot_git.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            return f"{dot_git} is not a gitfile"
        admin = Path(text.split(":", 1)[1].strip())
        if not admin.is_absolute():
            admin = (worktree / admin).resolve()
    else:
        return f"{dot_git} is neither a gitfile nor a symlink"
    if admin.parent.resolve() != (common / "worktrees").resolve():
        return f"{dot_git} points outside {common / 'worktrees'}: {admin}"
    back = admin / "gitdir"
    if not back.is_file() or Path(back.read_text(encoding="utf-8").strip()).parent.resolve() != worktree.resolve():
        return f"{back} does not point back to {dot_git}"
    return None


def write_description(repo: Path, branch: str, text: str) -> bool:
    for delay in (0.0, *CONFIG_RETRY_DELAYS):
        time.sleep(delay)
        if meta.git(repo, "config", f"branch.{branch}.description", text, check=False).returncode == 0:
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", required=True, help="2-4 lowercase ASCII words joined by hyphens")
    parser.add_argument("--client", required=True, choices=meta.CLIENTS)
    parser.add_argument("--task", required=True, help="single-line task text")
    parser.add_argument("--from", dest="source", default="main", help="local branch to branch from (default: main)")
    parser.add_argument("--parent", help="parent branch, for a revision or integration")
    parser.add_argument("--repo", default=".", help="any path inside the repository (default: cwd)")
    parser.add_argument("--worktrees-root", help="override <state>/<repo>/worktrees")
    parser.add_argument("--prefix", default="task", help="branch prefix (task, integration)")
    args = parser.parse_args(argv)

    if not SLUG_RE.match(args.slug):
        die("--slug must be 2-4 lowercase ASCII words of letters and digits joined by hyphens")
    if "\n" in args.task or "\r" in args.task or not args.task.strip():
        die("--task must be a non-empty single line")

    repo = Path(args.repo).resolve()
    common = common_dir(repo)
    main_worktree = common.parent if common.name == ".git" else common
    base = meta.git(repo, "rev-parse", "--verify", f"refs/heads/{args.source}", check=False)
    if base.returncode != 0:
        die(f"local branch {args.source!r} does not exist; pass --from")
    base_oid = base.stdout.strip()

    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    root = Path(args.worktrees_root) if args.worktrees_root else state / main_worktree.name / "worktrees"
    root.mkdir(parents=True, exist_ok=True)

    stem = f"{args.slug}-{datetime.now().astimezone().strftime('%Y%m%d')}"
    session, warning = meta.session_from_env(args.client)
    if warning:
        print(f"warning: {warning}", file=sys.stderr)

    last_error = ""
    for _ in range(ADD_ATTEMPTS):
        number = existing_numbers(repo, common, root, stem) + 1
        name = f"{stem}-{number:02d}"
        branch = f"{args.prefix}/{name}"
        path = root / name
        result = meta.git(repo, "worktree", "add", "-b", branch, str(path), base_oid, check=False)
        if result.returncode == 0:
            break
        last_error = result.stderr.strip()
    else:
        die(f"git worktree add failed {ADD_ATTEMPTS} times: {last_error}")

    print(f"worktree={path}\nbranch={branch}\nbase={base_oid}")
    problem = verify_identity(path, common)
    if problem:
        print(f"error: {problem}; worktree preserved", file=sys.stderr)
        return 4

    text = meta.format_description(
        args.task, args.client, session, base_oid, meta.agent_pid_from_env(args.client), args.parent
    )
    if not write_description(repo, branch, text):
        print(f"error: could not write branch.{branch}.description; set it by hand:\n{text}", file=sys.stderr)
        return 3
    print(f"description={text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
