#!/usr/bin/env python3
"""Safely remove a linked Git worktree, including one whose `.git` git-annex turned into a symlink.

git-annex replaces a linked worktree's `.git` pointer file with a symlink, and
`git worktree remove` refuses such a worktree
(https://git-annex.branchable.com/bugs/git_worktree_remove_fails/). The
documented workaround is to put the pointer file back and then remove, without
running another git-annex command in between. This script does that after
verifying the worktree holds nothing that would be lost; it never forces
anything and restores the symlink if Git still refuses.

Residual risk: `git worktree remove` runs its own `git status`, which can start
the git-annex clean filter. If that turns `.git` back into a symlink, Git
refuses and the symlink is restored; nothing is deleted.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

DEFAULT_LOCK_NAME = "main-integration.lock"
IN_PROGRESS = (
    "rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD",
    "REVERT_HEAD", "BISECT_LOG", "BISECT_START", "sequencer",
)
INHERITED_GIT_ENV = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX",
)


class RemovalError(RuntimeError):
    """A user-actionable refusal; nothing was changed unless the message says so."""


@dataclass(frozen=True)
class Target:
    worktree: Path
    admin_dir: Path
    common_dir: Path
    main_worktree: Path
    branch_ref: str | None
    uses_annex: bool
    symlink_target: str | None
    description: str | None

    @property
    def owner_line(self) -> str:
        if not self.description:
            return "owner: none (no branch description; legacy or detached worktree)"
        one_line = "".join(c if c.isprintable() else c.encode("unicode_escape").decode() for c in self.description)
        return f"owner: {one_line}"


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in INHERITED_GIT_ENV}
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=env)
    except OSError as error:
        raise RemovalError(f"cannot run git in {cwd}: {error}") from error


def git_out(cwd: Path, *args: str) -> str:
    result = run_git(cwd, *args)
    if result.returncode != 0:
        raise RemovalError(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout.strip()


def list_worktrees(cwd: Path) -> list[dict]:
    entries: list[dict] = []
    for line in git_out(cwd, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            entries.append({"path": Path(line[9:]).resolve(), "branch": None, "locked": False, "prunable": False})
        elif not entries:
            continue
        elif line.startswith("branch "):
            entries[-1]["branch"] = line[7:]
        elif line == "locked" or line.startswith("locked "):
            entries[-1]["locked"] = True
        elif line == "prunable" or line.startswith("prunable "):
            entries[-1]["prunable"] = True
    return entries


def read_pointer(text: str, relative_to: Path) -> Path:
    path = Path(text)
    return path if path.is_absolute() else relative_to / path


def check_dotgit(worktree: Path, admin_dir: Path) -> str | None:
    """Return the symlink target for a matching symlink, None for a matching gitfile."""
    dotgit = worktree / ".git"
    if dotgit.is_symlink():
        if dotgit.resolve() != admin_dir:
            raise RemovalError(f"{dotgit} is a symlink that does not resolve to {admin_dir}")
        return os.readlink(dotgit)
    if dotgit.is_file():
        text = dotgit.read_text().strip()
        if not text.startswith("gitdir: ") or read_pointer(text.removeprefix("gitdir: "), worktree).resolve() != admin_dir:
            raise RemovalError(f"{dotgit} does not name {admin_dir}")
        return None
    raise RemovalError(f"{dotgit} is neither a gitfile nor a symlink")


def locate(worktree_arg: str) -> tuple[Path, Path]:
    worktree = Path(worktree_arg).resolve()
    if not worktree.is_dir():
        raise RemovalError(f"{worktree} is not a directory")
    common_dir = Path(git_out(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    return worktree, common_dir


def inspect(worktree: Path) -> Target:
    if Path(git_out(worktree, "rev-parse", "--show-toplevel")).resolve() != worktree:
        raise RemovalError(f"{worktree} is not the root of a worktree")
    git_dir = Path(git_out(worktree, "rev-parse", "--path-format=absolute", "--git-dir")).resolve()
    common_dir = Path(git_out(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    if git_dir == common_dir:
        raise RemovalError(f"{worktree} is a main worktree, not a linked one")
    entries = list_worktrees(worktree)
    mine = [e for e in entries if e["path"] == worktree]
    if len(mine) != 1:
        raise RemovalError(f"{worktree} is not registered exactly once in {common_dir}")
    if mine[0]["locked"] or mine[0]["prunable"]:
        raise RemovalError(f"{worktree} is locked or prunable; resolve that first")
    back = read_pointer((git_dir / "gitdir").read_text().strip(), git_dir)
    if back.name != ".git" or back.parent.resolve() != worktree:
        raise RemovalError(f"{git_dir / 'gitdir'} does not point back to {worktree / '.git'}")
    claimants = []
    for admin in (common_dir / "worktrees").glob("*/gitdir"):
        pointer = read_pointer(admin.read_text().strip(), admin.parent)
        if pointer.parent.resolve() == worktree:
            claimants.append(admin.parent)
    if len(claimants) != 1:
        raise RemovalError(f"{worktree} is claimed by {len(claimants)} admin directories")
    symlink_target = check_dotgit(worktree, git_dir)
    config = run_git(worktree, "config", "--get", "filter.annex.process").stdout.strip()
    uses_annex = bool(config) or (common_dir / "annex").exists()
    if uses_annex and shutil.which("git-annex") is None:
        raise RemovalError("this repository uses git-annex but git-annex is not on PATH")
    branch_ref = run_git(worktree, "symbolic-ref", "-q", "HEAD").stdout.strip() or None
    description = None
    if branch_ref and branch_ref.startswith("refs/heads/"):
        description = run_git(worktree, "config", "--get", f"branch.{branch_ref.removeprefix('refs/heads/')}.description").stdout.strip() or None
    return Target(worktree, git_dir, common_dir, entries[0]["path"], branch_ref, uses_annex, symlink_target, description)


def processes_inside(worktree: Path) -> list[str]:
    lsof = shutil.which("lsof")
    if lsof is None:
        print("warning: lsof not found; skipping the process check", file=sys.stderr)
        return []
    result = subprocess.run([lsof, "-d", "cwd", "-Fpn"], capture_output=True, text=True, check=False)
    pid, hits = "?", []
    for line in result.stdout.splitlines():
        if line.startswith("p"):
            pid = line[1:]
        elif line.startswith("n"):
            path = Path(line[1:])
            if path == worktree or worktree in path.parents:
                hits.append(pid)
    return hits


def resolve_base(target: Target, base: str) -> str:
    if base.startswith("-"):
        raise RemovalError(f"invalid --base {base!r}")
    return git_out(target.worktree, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}")


def verify_safe(target: Target, base: str, *, allow_unreferenced_reflog: bool, expect_owner: str | None = None) -> None:
    wt = target.worktree
    if expect_owner is not None and (not target.description or expect_owner not in target.description):
        raise RemovalError(f"owner mismatch: expected {expect_owner!r} in the branch description; {target.owner_line}")
    busy = [name for name in IN_PROGRESS if (target.admin_dir / name).exists()]
    refs_dir = target.admin_dir / "refs"
    if refs_dir.is_dir() and any(p.is_file() for p in refs_dir.rglob("*")):
        busy.append("refs/ (per-worktree refs)")
    if busy:
        raise RemovalError(f"per-worktree state would be lost: {', '.join(busy)}")
    if (target.admin_dir / "modules").exists() or any(
        line.startswith("160000 ") for line in git_out(wt, "ls-files", "--stage").splitlines()
    ):
        raise RemovalError("worktree contains submodules; remove it manually")
    status = git_out(wt, "status", "--porcelain", "--ignored=matching", "--untracked-files=all", "--ignore-submodules=none")
    if status:
        entries = status.splitlines()
        raise RemovalError(f"worktree is not clean ({len(entries)} entries):\n  " + "\n  ".join(entries[:10]))
    hidden = [line for line in git_out(wt, "ls-files", "-v").splitlines() if line[:1].islower() or line[:1] == "S"]
    if hidden:
        raise RemovalError("assume-unchanged/skip-worktree entries can hide edits:\n  " + "\n  ".join(hidden[:10]))
    base_oid = resolve_base(target, base)
    ancestry = run_git(wt, "merge-base", "--is-ancestor", "HEAD", base_oid)
    if ancestry.returncode == 1:
        raise RemovalError(f"HEAD is not contained in {base}; integrate it first")
    if ancestry.returncode != 0:
        raise RemovalError(f"cannot compare HEAD with {base}: {ancestry.stderr.strip()}")
    if not allow_unreferenced_reflog:
        for oid in dict.fromkeys(git_out(wt, "reflog", "show", "--format=%H", "HEAD").splitlines()):
            held = run_git(wt, "for-each-ref", "--contains", oid, "--count=1", "--format=%(refname)")
            if held.returncode != 0 or not held.stdout.strip():
                raise RemovalError(
                    f"commit {oid[:12]} is only in this worktree's HEAD reflog and would become unreachable; "
                    "pass --allow-unreferenced-reflog to discard it"
                )
    users = processes_inside(wt)
    if users:
        raise RemovalError(f"processes still have their cwd inside the worktree (pids: {', '.join(users)})")


def raise_interrupt(signum: int, frame: object) -> None:
    raise KeyboardInterrupt


@contextmanager
def exclusive_lock(common_dir: Path, name: str) -> Iterator[None]:
    lock = common_dir / name
    token = secrets.token_hex(16)
    try:
        lock.mkdir()
    except FileExistsError:
        raise RemovalError(f"lock {lock} is held by another actor (release your own lock first); not removing it") from None
    try:
        (lock / "owner").write_text(f"{token}\n{os.getpid()}\n{socket.gethostname()}\n")
    except OSError as error:
        lock.rmdir()
        raise RemovalError(f"cannot record lock ownership: {error}") from error
    previous = {sig: signal.signal(sig, raise_interrupt) for sig in (signal.SIGTERM, signal.SIGHUP)}
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        release_lock(lock, token)


def release_lock(lock: Path, token: str) -> None:
    try:
        owner = (lock / "owner").read_text().split("\n", 1)[0]
        if owner != token:
            print(f"warning: {lock} is no longer ours; leaving it in place", file=sys.stderr)
            return
        released = lock.with_name(f"{lock.name}.released.{token}")
        os.rename(lock, released)
        shutil.rmtree(released)
    except OSError as error:
        print(f"warning: could not release {lock}: {error}", file=sys.stderr)


def replace_dotgit(worktree: Path, *, gitfile: Path | None = None, symlink: str | None = None) -> None:
    tmp = worktree / f".git.normalize.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    try:
        if gitfile is not None:
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(fd, "w") as handle:
                handle.write(f"gitdir: {gitfile}\n")
        else:
            assert symlink is not None
            os.symlink(symlink, tmp)
        os.replace(tmp, worktree / ".git")
    except BaseException:
        if tmp.is_symlink() or tmp.exists():
            tmp.unlink()
        raise


def rollback(target: Target, original: str | None, cause: BaseException) -> None:
    if original is None:
        return
    dotgit = target.worktree / ".git"
    if not target.worktree.exists():
        print(f"warning: {target.worktree} is already gone after a partial removal; inspect {target.admin_dir}", file=sys.stderr)
    elif dotgit.is_file():
        try:
            replace_dotgit(target.worktree, symlink=original)
        except (OSError, RemovalError) as error:
            print(f"warning: could not restore the symlink ({error}); it was -> {original}", file=sys.stderr)


def delete_branch(target: Target, head: str, base_oid: str) -> None:
    ref = target.branch_ref
    if ref is None:
        return
    held = [str(e["path"]) for e in list_worktrees(target.main_worktree) if e["branch"] == ref]
    if held:
        raise RemovalError(f"worktree removed, but {ref} is checked out in {', '.join(held)}; branch kept")
    if run_git(target.main_worktree, "rev-parse", "--verify", ref).stdout.strip() != head:
        raise RemovalError(f"worktree removed, but {ref} moved after verification; branch kept")
    if run_git(target.main_worktree, "merge-base", "--is-ancestor", head, base_oid).returncode != 0:
        raise RemovalError(f"worktree removed, but {ref} is not contained in the base; branch kept")
    result = run_git(target.main_worktree, "update-ref", "-d", ref, head)
    if result.returncode != 0:
        raise RemovalError(f"worktree removed, but deleting {ref} failed: {result.stderr.strip()}")
    # `update-ref -d` leaves branch.<name>.* behind in the shared config; `git branch -D` would drop it.
    # Best effort: the worktree and ref are already gone, so a busy or read-only config only warns.
    section = f"branch.{ref.removeprefix('refs/heads/')}"
    result = run_git(target.main_worktree, "config", "--file", str(target.common_dir / "config"), "--remove-section", section)
    if result.returncode != 0 and "no such section" not in result.stderr:
        print(f"warning: {ref} removed, but config section {section} was not: {result.stderr.strip()}", file=sys.stderr)


def remove(
    worktree_arg: str, base: str, *, delete_branch_too: bool, lock_name: str, allow_unreferenced_reflog: bool,
    expect_owner: str | None = None,
) -> Target:
    worktree, common_dir = locate(worktree_arg)
    with exclusive_lock(common_dir, lock_name):
        target = inspect(worktree)
        print(target.owner_line, file=sys.stderr)
        if target.uses_annex:
            result = run_git(worktree, "annex", "restage")
            if result.returncode != 0:
                raise RemovalError(f"git annex restage failed: {result.stderr.strip()}")
            target = inspect(worktree)
        verify_safe(target, base, allow_unreferenced_reflog=allow_unreferenced_reflog, expect_owner=expect_owner)
        base_oid = resolve_base(target, base)
        head = git_out(worktree, "rev-parse", "HEAD")
        if target.symlink_target is not None:
            if check_dotgit(worktree, target.admin_dir) != target.symlink_target:
                raise RemovalError(".git changed since inspection")
            replace_dotgit(worktree, gitfile=target.admin_dir)
        try:
            if check_dotgit(worktree, target.admin_dir) is not None:
                raise RemovalError(".git became a symlink again before removal")
            if git_out(worktree, "rev-parse", "HEAD") != head:
                raise RemovalError("HEAD changed during removal")
            result = run_git(target.main_worktree, "worktree", "remove", str(worktree))
            if result.returncode != 0:
                raise RemovalError(f"git worktree remove refused: {result.stderr.strip()}")
        except BaseException as cause:
            rollback(target, target.symlink_target, cause)
            raise
        if delete_branch_too:
            delete_branch(target, head, base_oid)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely remove a linked Git worktree (git-annex aware).")
    parser.add_argument("worktree", help="path of the linked worktree to remove")
    parser.add_argument("--base", default="main", help="ref that must already contain HEAD (default: main)")
    parser.add_argument("--delete-branch", action="store_true", help="also delete the worktree's branch when it is fully contained in --base")
    parser.add_argument("--allow-unreferenced-reflog", action="store_true", help="accept commits that only this worktree's HEAD reflog references")
    parser.add_argument("--expect-owner", metavar="TEXT", help="refuse unless the branch description contains TEXT (use the task text you recorded)")
    parser.add_argument("--dry-run", action="store_true", help="run the checks without the lock or restage; change nothing")
    parser.add_argument("--lock-name", default=DEFAULT_LOCK_NAME, help="lock directory created under the common git dir")
    args = parser.parse_args(argv)
    try:
        if args.dry_run:
            worktree, _ = locate(args.worktree)
            target = inspect(worktree)
            print(target.owner_line, file=sys.stderr)
            verify_safe(target, args.base, allow_unreferenced_reflog=args.allow_unreferenced_reflog, expect_owner=args.expect_owner)
            kind = f"symlink -> {target.symlink_target}" if target.symlink_target else "gitfile"
            print(f"dry-run ok: {target.worktree} (.git is a {kind}; {target.branch_ref}) would be removed")
            return 0
        target = remove(
            args.worktree, args.base, delete_branch_too=args.delete_branch,
            lock_name=args.lock_name, allow_unreferenced_reflog=args.allow_unreferenced_reflog,
            expect_owner=args.expect_owner,
        )
    except RemovalError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    suffix = f" and {target.branch_ref}" if args.delete_branch and target.branch_ref else ""
    print(f"removed {target.worktree}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
