#!/usr/bin/env python3
"""Safely remove a linked Git worktree, including one whose `.git` git-annex turned into a symlink.

git-annex replaces a linked worktree's `.git` pointer file with a symlink, and
`git worktree remove` refuses such a worktree
(https://git-annex.branchable.com/bugs/git_worktree_remove_fails/). The
documented workaround is to put the pointer file back and then remove, without
running another git-annex command in between. This script does that after
verifying the worktree holds nothing that would be lost; it never forces
anything and restores the symlink if Git still refuses.

The root ignored `cultura.db` symlink is removable only when it resolves to the
regular `cultura.db` in the registered `main` worktree. The script unlinks that
symlink itself before Git removes the worktree; it never opens or removes the
database target. The caller must exclude all writers for the full operation;
the script lock coordinates cooperating removals only.

The `worktree-task finish` workflow passes `--discard-generated-artifacts` by
default. Direct low-level removal refuses recognized cache/build paths unless
that flag is passed or `--preserve-generated-artifacts` explicitly retains
them. A root `.direnv` path is separately quarantined by direct calls, and is
discarded only with `--discard-direnv-cache` or `--discard-generated-artifacts`
when its Nix-direnv `use flake` layout is verified. The generated-artifact flag
selects root `.pytest_cache` and `.ruff_cache`, `__pycache__` directories, root
`target` and `rust/target` build directories, the root `result` symlink, the
verified `.direnv` cache, and a root `.pre-commit-config.yaml` carrying the
git-hooks.nix generated-file marker. Unknown `.direnv` layouts and all other
ignored or untracked paths remain quarantined or refuse removal. Recognized
cache/build roots select all contents beneath them, so independent user data
must not be stored inside those paths.
`--preserve-generated-artifacts` opts out and quarantines recognized
cache/build paths and the marked generated config, retaining all selected
contents and links in the private state quarantine. The individual `--discard-*`
options remain available for partial cleanup. Generated paths are quarantined
first and purged only after Git confirms worktree removal.
The manifest records cache moves, Git removal, and per-entry purge progress.
Interrupted purges can be resumed with `--purge-preserved-quarantine` after the
repository identity, saved signatures, open handles, and main ancestry are
rechecked. Legacy `.direnv` transactions without a stored signature require an
explicit `--discard-unverified-direnv` override. Changed or unrecognized
quarantine entries remain preserved for inspection.

After the final status check, the script normalizes a verified Annex `.git`
symlink to a gitfile immediately before `git worktree remove`. Git validates
that pointer before its own cleanliness check, which may run Annex filters.
If Git refuses, the script restores the verified pointer form and preserves the
worktree.

Cleanup ownership is the creating `(client, session_id)` pair in the detached
worktree's owner file inside its verified Git admin directory. The active client
session is read from its own environment variable; `--expect-worktree-id` selects
the exact detached worktree. Legacy branch-backed worktrees can still use
`--expect-branch`. Task text is descriptive only, and unknown or malformed
session metadata fails closed. The session check prevents cooperative
cross-session mistakes; it is not an authentication boundary against a process
that can alter its environment.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worktree_meta as meta

DEFAULT_LOCK_NAME = "main-integration.lock"
DIR_ENV_NAME = ".direnv"
PRECOMMIT_CONFIG_NAME = ".pre-commit-config.yaml"
NIX_STORE_ROOT = Path("/nix/store")
MAX_PRECOMMIT_CONFIG_SIZE = 16 * 1024 * 1024
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
    main_branch_worktree: Path | None
    branch_ref: str | None
    worktree_id: str | None
    uses_annex: bool
    symlink_target: str | None
    description: str | None

    @property
    def owner_line(self) -> str:
        branch = self.branch_ref.removeprefix("refs/heads/") if self.branch_ref else "detached"
        owner = meta.parse_owner_description(self.description or "")
        if owner is None:
            suffix = f"; worktree_id={self.worktree_id}" if self.worktree_id else ""
            return f"owner: unknown; branch={branch}{suffix}"
        task, client, session = owner
        one_line = "".join(c if c.isprintable() else c.encode("unicode_escape").decode() for c in task)
        suffix = f"; worktree_id={self.worktree_id}" if self.worktree_id else ""
        return f"owner: client={client} session={session}; branch={branch}{suffix}; task={one_line}"


@dataclass(frozen=True)
class CanonicalDatabaseLink:
    link_text: str
    target: Path
    target_identity: tuple[int, int]


@dataclass(frozen=True)
class DirenvArtifact:
    path: Path
    identity: tuple[int, int]
    signature: tuple[tuple[object, ...], ...]
    discardable: bool
    discard_reason: str | None


@dataclass(frozen=True)
class GeneratedCacheArtifact:
    path: Path
    worktree: Path
    identity: tuple[int, int]
    signature: tuple[tuple[object, ...], ...]
    preserve: bool = False


@dataclass(frozen=True)
class RemovalPlan:
    database_link: CanonicalDatabaseLink | None
    direnv: DirenvArtifact | None
    discard_direnv_cache: bool
    generated_caches: tuple[GeneratedCacheArtifact, ...]


@dataclass
class RemovalTransaction:
    operation_dir: Path
    manifest_path: Path
    manifest: dict[str, object]


@dataclass(frozen=True)
class RemovalOutcome:
    target: Target
    preserved_direnv: Path | None = None
    discarded_direnv: bool = False
    preserved_generated_caches: tuple[Path, ...] = ()
    discarded_generated_caches: tuple[str, ...] = ()


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in INHERITED_GIT_ENV}
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=env)
    except OSError as error:
        raise RemovalError(f"cannot run git in {cwd}: {error}") from error


def run_git_bytes(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k not in INHERITED_GIT_ENV}
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=False, check=False, env=env)
    except OSError as error:
        raise RemovalError(f"cannot run git in {cwd}: {error}") from error


def git_out(cwd: Path, *args: str) -> str:
    result = run_git(cwd, *args)
    if result.returncode != 0:
        raise RemovalError(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout.strip()


def parse_status_z(output: bytes) -> list[tuple[bytes, bytes]]:
    fields = output.split(b"\0")
    entries: list[tuple[bytes, bytes]] = []
    index = 0
    while index < len(fields) - 1:
        record = fields[index]
        index += 1
        if not record:
            continue
        if len(record) < 3 or record[2:3] != b" ":
            raise RemovalError("git status returned an invalid porcelain record")
        status, path = record[:2], record[3:]
        entries.append((status, path))
        if b"R" in status or b"C" in status:
            index += 1
    return entries


def status_entries(worktree: Path) -> list[tuple[bytes, bytes]]:
    result = run_git_bytes(
        worktree, "status", "--porcelain=v1", "--ignored=matching", "--untracked-files=all",
        "--ignore-submodules=none", "-z",
    )
    if result.returncode != 0:
        error = result.stderr.decode("utf-8", "replace").strip()
        raise RemovalError(f"git status failed in {worktree}: {error}")
    return parse_status_z(result.stdout)


def status_description(status: bytes, path: bytes) -> str:
    return f"{status.decode('ascii', 'replace')} {path!r}"


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


def registered_main_worktree(entries: list[dict]) -> Path | None:
    matches = [entry["path"] for entry in entries if entry["branch"] == "refs/heads/main"]
    return matches[0] if len(matches) == 1 else None


def worktree_command_root(entries: list[dict], target: Path) -> Path:
    main = registered_main_worktree(entries)
    if main is not None and main != target:
        return main
    alternatives = [entry["path"] for entry in entries if entry["path"] != target]
    if not alternatives:
        raise RemovalError("no other registered worktree is available for Git administration")
    return alternatives[0]


def canonical_database_target(worktree: Path, main_worktree: Path | None) -> tuple[Path, tuple[int, int]] | None:
    if main_worktree is None:
        return None
    db = main_worktree / "cultura.db"
    try:
        metadata = db.lstat()
        target = db.resolve(strict=True)
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or target != db or worktree == target or worktree in target.parents:
        return None
    return target, (metadata.st_dev, metadata.st_ino)


def canonical_database_link(worktree: Path, main_worktree: Path | None) -> CanonicalDatabaseLink | None:
    expected = canonical_database_target(worktree, main_worktree)
    if expected is None:
        return None
    link = worktree / "cultura.db"
    try:
        metadata = link.lstat()
        link_text = os.readlink(link)
        target = link.resolve(strict=True)
    except OSError:
        return None
    expected_target, target_identity = expected
    if not stat.S_ISLNK(metadata.st_mode) or target != expected_target:
        return None
    return CanonicalDatabaseLink(link_text, expected_target, target_identity)


def database_link_unchanged(target: Target, expected: CanonicalDatabaseLink) -> bool:
    if canonical_database_link(target.worktree, target.main_branch_worktree) != expected:
        return False
    return canonical_database_target(target.worktree, target.main_branch_worktree) == (
        expected.target, expected.target_identity,
    )


def decode_mount_field(value: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


def parse_linux_mountinfo(contents: str) -> tuple[Path, ...] | None:
    values: list[Path] = []
    for line in contents.splitlines():
        fields = line.split()
        if not fields:
            continue
        if len(fields) < 5:
            return None
        values.append(Path(decode_mount_field(fields[4])).resolve())
    return tuple(values)


def parse_darwin_mount_output(contents: str) -> tuple[Path, ...] | None:
    values: list[Path] = []
    for line in contents.splitlines():
        before, separator, remainder = line.rpartition(" on ")
        if not separator or not before:
            return None
        mount_path, options_separator, _ = remainder.rpartition(" (")
        if not options_separator or not mount_path:
            return None
        values.append(Path(decode_mount_field(mount_path)).resolve())
    return tuple(values)


def mount_points() -> tuple[Path, ...] | None:
    try:
        if sys.platform.startswith("linux"):
            return parse_linux_mountinfo(Path("/proc/self/mountinfo").read_text())
        elif sys.platform == "darwin":
            result = subprocess.run(["mount"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return None
            return parse_darwin_mount_output(result.stdout)
        else:
            return None
    except (OSError, IndexError, ValueError):
        return None


def is_mountpoint(path: Path, mounts: tuple[Path, ...] | None) -> bool | None:
    try:
        if os.path.ismount(path):
            return True
        if mounts is None:
            return None
        resolved = path.resolve(strict=True)
        return resolved in mounts
    except OSError:
        return None


def direnv_tree_signature(root: Path) -> tuple[tuple[object, ...], ...]:
    entries: list[tuple[object, ...]] = []

    def visit(path: Path, relative: str) -> None:
        try:
            info = path.lstat()
        except OSError as error:
            raise RemovalError(f"cannot inspect {path}: {error}") from error
        if stat.S_ISLNK(info.st_mode):
            kind = "symlink"
            link = os.readlink(path)
        elif stat.S_ISDIR(info.st_mode):
            kind = "directory"
            link = ""
        elif stat.S_ISREG(info.st_mode):
            kind = "file"
            link = ""
        else:
            kind = "special"
            link = ""
        size = 0 if kind == "directory" else info.st_size
        mtime_ns = 0 if kind == "directory" else info.st_mtime_ns
        entries.append((relative, kind, info.st_dev, info.st_ino, info.st_mode, size, mtime_ns, link))
        if kind == "directory":
            try:
                children = sorted(os.scandir(path), key=lambda entry: entry.name)
            except OSError as error:
                raise RemovalError(f"cannot inspect {path}: {error}") from error
            for child in children:
                child_relative = f"{relative}/{child.name}" if relative else child.name
                visit(Path(child.path), child_relative)

    visit(root, ".")
    return tuple(entries)


def generated_cache_candidates(
    status: list[tuple[bytes, bytes]], *, caches: bool = True, build_outputs: bool = False,
    include_generated_config: bool = False,
) -> tuple[bytes, ...]:
    candidates: set[bytes] = set()
    for _, path in status:
        if include_generated_config and path == PRECOMMIT_CONFIG_NAME.encode():
            candidates.add(path)
            continue
        parts = path.rstrip(b"/").split(b"/")
        if not parts or parts[0] == b".direnv":
            continue
        if caches and parts[0] in (b".pytest_cache", b".ruff_cache"):
            candidates.add(parts[0])
            continue
        if build_outputs and (
            parts[0] == b"result" or parts[0] == b"target" or parts[:2] == [b"rust", b"target"]
        ):
            candidates.add(
                b"result" if parts[0] == b"result" else b"target" if parts[0] == b"target" else b"rust/target"
            )
            continue
        if not caches:
            continue
        for index, part in enumerate(parts):
            if part == b"__pycache__":
                candidates.add(b"/".join(parts[:index + 1]))
                break

    roots: list[bytes] = []
    for candidate in sorted(candidates, key=lambda value: (value.count(b"/"), value)):
        if not any(candidate.startswith(root + b"/") for root in roots):
            roots.append(candidate)
    return tuple(roots)


def generated_cache_signature(root: Path, worktree: Path) -> tuple[tuple[object, ...], ...]:
    try:
        relative = root.relative_to(worktree)
        worktree_info = worktree.lstat()
        root_info = root.lstat()
    except (OSError, ValueError) as error:
        raise RemovalError(f"cannot inspect generated cache path {root}: {error}") from error
    if not relative.parts or relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise RemovalError(f"generated cache path is not a safe worktree-relative path: {root}")
    if stat.S_ISLNK(worktree_info.st_mode) or not stat.S_ISDIR(worktree_info.st_mode):
        raise RemovalError(f"worktree root is not a real directory: {worktree}")
    relative_text = str(relative)
    result_link = relative_text == "result"
    if not (result_link or relative_text in (".pytest_cache", ".ruff_cache", "target", "rust/target")
            or relative_text == PRECOMMIT_CONFIG_NAME or relative.parts[-1] == "__pycache__"):
        raise RemovalError(f"unrecognized generated artifact path: {root}")

    cursor = worktree
    for component in relative.parts[:-1] if result_link or relative_text == PRECOMMIT_CONFIG_NAME else relative.parts:
        cursor = cursor / component
        try:
            info = cursor.lstat()
        except OSError as error:
            raise RemovalError(f"cannot inspect generated artifact path component {cursor}: {error}") from error
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise RemovalError(f"generated artifact path contains a non-directory or symlink component: {cursor}")

    if result_link:
        if not stat.S_ISLNK(root_info.st_mode):
            raise RemovalError(f"root result is not a symlink: {root}")
        return direnv_tree_signature(root)
    if relative_text == PRECOMMIT_CONFIG_NAME:
        return generated_precommit_config_signature(root, worktree_info.st_dev)
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise RemovalError(f"generated artifact root is not a real directory: {root}")
    if root_info.st_dev != worktree_info.st_dev:
        raise RemovalError(f"generated artifact is on a different filesystem from the worktree: {root}")
    return generated_cache_tree_signature(root, worktree_info.st_dev)


def generated_precommit_config_signature(path: Path, expected_device: int) -> tuple[tuple[object, ...], ...]:
    try:
        link_info = path.lstat()
    except OSError as error:
        raise RemovalError(f"cannot inspect generated pre-commit config {path}: {error}") from error
    if stat.S_ISLNK(link_info.st_mode):
        if link_info.st_dev != expected_device:
            raise RemovalError(f"generated pre-commit config link is on a different filesystem: {path}")
        try:
            target = Path(os.readlink(path))
            store_root = NIX_STORE_ROOT.resolve(strict=True)
            target_parent = target.parent.resolve(strict=True) if target.is_absolute() else None
            resolved_target = target.resolve(strict=True) if target.is_absolute() else None
        except OSError as error:
            raise RemovalError(f"cannot inspect generated pre-commit config target {path}: {error}") from error
        if (
            not target.is_absolute()
            or target_parent != store_root
            or not target.name.endswith("-pre-commit-config.json")
            or resolved_target != target
        ):
            raise RemovalError(f"{path} is not a symlink to a Nix-store git-hooks.nix config")
        generated_precommit_file_signature(target, expected_device=None)
        signature = direnv_tree_signature(path)
        if len(signature) != 1:
            raise RemovalError(f"generated pre-commit config link changed while signing: {path}")
        relative, kind, device, inode, mode, _, _, link_text = signature[0]
        if (
            relative != "."
            or kind != "symlink"
            or (device, inode, mode) != (link_info.st_dev, link_info.st_ino, link_info.st_mode)
            or link_text != os.readlink(path)
            or link_text != str(target)
        ):
            raise RemovalError(f"generated pre-commit config link changed while signing: {path}")
        return signature
    return generated_precommit_file_signature(path, expected_device=expected_device)


def generated_precommit_file_signature(path: Path, expected_device: int | None) -> tuple[tuple[object, ...], ...]:
    fd = -1
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise RemovalError(f"generated pre-commit config is not a regular file: {path}")
        if expected_device is not None and info.st_dev != expected_device:
            raise RemovalError(f"generated pre-commit config is on a different filesystem: {path}")
        if info.st_size > MAX_PRECOMMIT_CONFIG_SIZE:
            raise RemovalError(f"generated pre-commit config exceeds the size limit: {path}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags)
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
            or (expected_device is not None and opened.st_dev != expected_device)
            or opened.st_size > MAX_PRECOMMIT_CONFIG_SIZE
        ):
            raise RemovalError(f"generated pre-commit config changed while opening: {path}")
        contents = bytearray()
        while len(contents) <= MAX_PRECOMMIT_CONFIG_SIZE:
            chunk = os.read(fd, min(1024 * 1024, MAX_PRECOMMIT_CONFIG_SIZE + 1 - len(contents)))
            if not chunk:
                break
            contents.extend(chunk)
        if len(contents) > MAX_PRECOMMIT_CONFIG_SIZE:
            raise RemovalError(f"generated pre-commit config exceeds the size limit: {path}")
        after_read = os.fstat(fd)
        if (
            (after_read.st_dev, after_read.st_ino, after_read.st_size, after_read.st_mtime_ns)
            != (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
            or len(contents) != after_read.st_size
        ):
            raise RemovalError(f"generated pre-commit config changed while reading: {path}")
        lines = bytes(contents).splitlines()
        if len(lines) < 2 or lines[0] != b"# DO NOT MODIFY" or lines[1] != b"# This file was generated by git-hooks.nix":
            raise RemovalError(f"{path} is not the generated git-hooks.nix file")
        digest = hashlib.sha256(contents).hexdigest()
        info = after_read
    except OSError as error:
        raise RemovalError(f"cannot inspect generated pre-commit config {path}: {error}") from error
    finally:
        if fd >= 0:
            os.close(fd)
    return ((".", "file", info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, digest),)


def generated_cache_tree_signature(root: Path, expected_device: int) -> tuple[tuple[object, ...], ...]:
    root_info = root.lstat()
    if stat.S_ISLNK(root_info.st_mode):
        if root_info.st_dev != expected_device:
            raise RemovalError(f"unrecognized generated artifact symlink: {root}")
        target = Path(os.readlink(root))
        try:
            is_precommit_config = (
                target.is_absolute()
                and target.parent.resolve(strict=True) == NIX_STORE_ROOT.resolve(strict=True)
                and target.name.endswith("-pre-commit-config.json")
            )
        except OSError as error:
            raise RemovalError(f"cannot inspect generated config symlink target {root}: {error}") from error
        if is_precommit_config:
            return generated_precommit_config_signature(root, expected_device)
        signature = direnv_tree_signature(root)
        if len(signature) != 1 or signature[0][1] != "symlink":
            raise RemovalError(f"result symlink changed during inspection: {root}")
        return signature
    if stat.S_ISREG(root_info.st_mode):
        return generated_precommit_config_signature(root, expected_device)
    if not stat.S_ISDIR(root_info.st_mode):
        raise RemovalError(f"generated artifact root is not a real directory: {root}")
    mounts = mount_points()
    if mounts is None:
        raise RemovalError("cannot inspect mount points; refusing generated-artifact removal")
    if root_info.st_dev != expected_device or is_mountpoint(root, mounts) is not False:
        raise RemovalError(f"generated artifact is on a different filesystem or is a mount point: {root}")
    signature = direnv_tree_signature(root)
    for entry_relative, kind, device, *_ in signature:
        try:
            str(entry_relative).encode("utf-8")
        except UnicodeEncodeError as error:
            raise RemovalError(f"generated artifact contains a non-UTF-8 path: {root}") from error
        components = str(entry_relative).split("/")
        if ".git" in components:
            raise RemovalError(f"generated artifact contains a nested Git repository: {root / str(entry_relative)}")
        if kind not in ("directory", "file"):
            raise RemovalError(f"generated artifact contains a symlink or special file: {root / str(entry_relative)}")
        if device != expected_device:
            raise RemovalError(f"generated artifact crosses a filesystem boundary: {root / str(entry_relative)}")
        if kind == "directory":
            entry_path = root if entry_relative == "." else root / str(entry_relative)
            if is_mountpoint(entry_path, mounts) is not False:
                raise RemovalError(f"generated artifact contains a mount point: {entry_path}")
    return signature


def inspect_generated_caches(
    target: Target, status: list[tuple[bytes, bytes]], *, caches: bool, build_outputs: bool,
    include_generated_config: bool = False, preserve: bool = False, discard_build_outputs: bool = False,
) -> tuple[GeneratedCacheArtifact, ...]:
    artifacts: list[GeneratedCacheArtifact] = []
    for relative_bytes in generated_cache_candidates(
        status, caches=caches, build_outputs=build_outputs, include_generated_config=include_generated_config,
    ):
        relative = os.fsdecode(relative_bytes)
        path = target.worktree / relative
        matching = [
            (item_status, item_path) for item_status, item_path in status
            if item_path == relative_bytes or item_path.startswith(relative_bytes + b"/")
        ]
        if not matching or any(item_status not in (b"!!", b"??") for item_status, _ in matching):
            raise RemovalError(f"generated artifact is not exclusively ignored or untracked: {path}")
        tracked = run_git_bytes(target.worktree, "ls-files", "--stage", "--", relative)
        if tracked.returncode != 0:
            raise RemovalError(f"cannot check tracked files under generated artifact {path}: {tracked.stderr.decode(errors='replace').strip()}")
        if tracked.stdout:
            raise RemovalError(f"generated artifact contains tracked files: {path}")

        signature = generated_cache_signature(path, target.worktree)
        if not any(entry[0] == "." for entry in signature):
            raise RemovalError(f"generated cache disappeared during inspection: {path}")
        root = next(entry for entry in signature if entry[0] == ".")
        is_build_output = relative_bytes in (b"result", b"target", b"rust/target")
        artifacts.append(GeneratedCacheArtifact(
            path, target.worktree, (int(root[2]), int(root[3])), signature,
            preserve and not (discard_build_outputs and is_build_output),
        ))

    paths = tuple(
        artifact.path if entry[0] == "." else artifact.path / str(entry[0])
        for artifact in artifacts for entry in artifact.signature if entry[1] != "symlink"
    )
    if paths:
        open_pids = lsof_open_paths(paths)
        if open_pids is None:
            raise RemovalError("could not verify open handles to generated caches; refusing removal")
        if open_pids:
            raise RemovalError(f"processes still have generated cache files open (pids: {', '.join(sorted(open_pids))})")
    return tuple(artifacts)


def path_is_beneath(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return path != root
    except ValueError:
        return False


def nix_store_symlink(path: Path, expected_leaf: str | None = None) -> Path | None:
    try:
        link_text = os.readlink(path)
        if not Path(link_text).is_absolute():
            return None
        target = Path(link_text).resolve(strict=True)
        store = NIX_STORE_ROOT.resolve(strict=True)
    except OSError:
        return None
    if not path_is_beneath(target, store):
        return None
    if expected_leaf is not None and target.name != expected_leaf:
        return None
    return target


def nix_direnv_cache_signature(root: Path) -> tuple[tuple[object, ...], ...] | None:
    """Return a signature only for the supported nix-direnv `use flake` cache layout."""
    try:
        root_info = root.lstat()
    except OSError:
        return None
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        return None
    mounts = mount_points()
    if mounts is None or is_mountpoint(root, mounts) is not False:
        return None

    try:
        root_entries = {entry.name: Path(entry.path) for entry in os.scandir(root)}
    except OSError:
        return None
    if "bin" not in root_entries or "flake-inputs" not in root_entries:
        return None
    bin_dir, inputs_dir = root_entries["bin"], root_entries["flake-inputs"]
    try:
        bin_info, inputs_info = bin_dir.lstat(), inputs_dir.lstat()
    except OSError:
        return None
    if not stat.S_ISDIR(bin_info.st_mode) or stat.S_ISLNK(bin_info.st_mode):
        return None
    if not stat.S_ISDIR(inputs_info.st_mode) or stat.S_ISLNK(inputs_info.st_mode):
        return None
    if bin_info.st_dev != root_info.st_dev or inputs_info.st_dev != root_info.st_dev:
        return None
    if is_mountpoint(bin_dir, mounts) is not False or is_mountpoint(inputs_dir, mounts) is not False:
        return None

    try:
        bin_children = sorted(os.scandir(bin_dir), key=lambda entry: entry.name)
        input_children = sorted(os.scandir(inputs_dir), key=lambda entry: entry.name)
    except OSError:
        return None
    if len(bin_children) != 1 or bin_children[0].name != "nix-direnv-reload":
        return None
    reload_path = Path(bin_children[0].path)
    try:
        reload_info = reload_path.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(reload_info.st_mode) or not (reload_info.st_mode & 0o111):
        return None

    for entry in input_children:
        if not re.fullmatch(r"[a-z0-9]{32,64}-source", entry.name):
            return None
        source_link = Path(entry.path)
        try:
            if not stat.S_ISLNK(source_link.lstat().st_mode):
                return None
        except OSError:
            return None
        if nix_store_symlink(source_link, entry.name) is None:
            return None

    profiles: set[str] = set()
    expected_root_names = {"bin", "flake-inputs"}
    for name, path in root_entries.items():
        match = re.fullmatch(r"flake-profile-([a-z0-9]{32,64})", name)
        if match is None:
            if name in expected_root_names:
                continue
            if re.fullmatch(r"flake-profile-[a-z0-9]{32,64}\.rc", name):
                continue
            return None
        profile_hash = match.group(1)
        try:
            if not stat.S_ISLNK(path.lstat().st_mode):
                return None
        except OSError:
            return None
        target = nix_store_symlink(path)
        if target is None or not target.name.endswith("-nix-shell-env"):
            return None
        profiles.add(profile_hash)

    if not profiles:
        return None
    for profile_hash in profiles:
        rc = root / f"flake-profile-{profile_hash}.rc"
        try:
            if not stat.S_ISREG(rc.lstat().st_mode):
                return None
        except OSError:
            return None
    for name in root_entries:
        if name.startswith("flake-profile-"):
            suffix = name.removeprefix("flake-profile-")
            profile_hash = suffix.removesuffix(".rc")
            if profile_hash not in profiles:
                return None

    try:
        signature = direnv_tree_signature(root)
    except RemovalError:
        return None
    for relative, kind, device, *_ in signature:
        if kind == "directory":
            path = root if relative == "." else root / str(relative)
            if device != root_info.st_dev or is_mountpoint(path, mounts) is not False:
                return None
    return signature


def direnv_root_signature(path: Path) -> tuple[tuple[object, ...], ...]:
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            kind, link = "symlink", os.readlink(path)
        elif stat.S_ISDIR(info.st_mode):
            kind, link = "directory", ""
        elif stat.S_ISREG(info.st_mode):
            kind, link = "file", ""
        else:
            kind, link = "special", ""
    except OSError as error:
        raise RemovalError(f"cannot inspect {path}: {error}") from error
    return ((".", kind, info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, link),)


def inspect_direnv(worktree: Path) -> DirenvArtifact | None:
    path = worktree / DIR_ENV_NAME
    if not os.path.lexists(path):
        return None
    root_signature = direnv_root_signature(path)
    root_record = root_signature[0]
    signature = nix_direnv_cache_signature(path)
    discard_reason = None if signature is not None else "layout is not a verified Nix-direnv use-flake cache"
    return DirenvArtifact(
        path,
        (int(root_record[2]), int(root_record[3])),
        signature if signature is not None else root_signature,
        signature is not None,
        discard_reason,
    )


def path_is_direnv_entry(path: bytes) -> bool:
    return path in (b".direnv", b".direnv/") or path.startswith(b".direnv/")


def state_quarantine_root(target: Target) -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))).expanduser()
    if not state_home.is_absolute():
        raise RemovalError("XDG_STATE_HOME must be an absolute path for worktree quarantine")
    root = state_home / target.main_worktree.name / "worktrees" / ".removal-quarantine"
    resolved = root.resolve(strict=False)
    if resolved == target.worktree or target.worktree in resolved.parents:
        raise RemovalError(f"quarantine root would be inside the worktree: {root}")
    if resolved == target.main_worktree or target.main_worktree in resolved.parents:
        raise RemovalError(f"quarantine root would be inside the repository: {root}")
    return root


def unresolved_transaction(target: Target) -> Path | None:
    root = state_quarantine_root(target)
    if not os.path.lexists(root):
        return None
    root_info = root.lstat()
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        raise RemovalError(f"quarantine root is not a real directory: {root}")
    for operation_dir in root.iterdir():
        operation_info = operation_dir.lstat()
        if not stat.S_ISDIR(operation_info.st_mode) or stat.S_ISLNK(operation_info.st_mode):
            raise RemovalError(f"unexpected quarantine entry; inspect before removal: {operation_dir}")
        manifest_path = operation_dir / "manifest.json"
        try:
            manifest_info = manifest_path.lstat()
            if not stat.S_ISREG(manifest_info.st_mode) or stat.S_ISLNK(manifest_info.st_mode):
                return manifest_path
            data = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            return manifest_path
        if Path(str(data.get("worktree", ""))).resolve() != target.worktree:
            continue
        if data.get("phase") != "completed_preserved":
            return manifest_path
    return None


def create_transaction(target: Target, head: str, plan: RemovalPlan) -> RemovalTransaction:
    db_link, direnv = plan.database_link, plan.direnv
    root = state_quarantine_root(target)
    root_existed = os.path.lexists(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root_info = root.lstat()
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        raise RemovalError(f"quarantine root is not a real directory: {root}")
    if root_info.st_uid != os.getuid() or root_info.st_mode & 0o077:
        raise RemovalError(f"quarantine root is not private to the current user: {root}")
    if not root_existed:
        fsync_directory(root.parent)
    if direnv is not None and root_info.st_dev != direnv.identity[0]:
        raise RemovalError(f"quarantine root is on a different filesystem from {direnv.path}")
    for cache in plan.generated_caches:
        if root_info.st_dev != cache.identity[0]:
            raise RemovalError(f"quarantine root is on a different filesystem from {cache.path}")
    operation_id = secrets.token_hex(16)
    operation_dir = root / operation_id
    operation_dir.mkdir(mode=0o700)
    fsync_directory(root)
    worktree_info, admin_info = target.worktree.stat(), target.admin_dir.stat()
    generated_caches = []
    for index, cache in enumerate(plan.generated_caches):
        relative = cache.path.relative_to(target.worktree)
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            raise RemovalError(f"generated artifact is not beneath the worktree: {cache.path}")
        generated_caches.append({
            "path": str(relative),
            "identity": list(cache.identity),
            "signature": [list(entry) for entry in cache.signature],
            "quarantine_path": str(operation_dir / f"generated-cache-{index:03d}"),
            "preserve": cache.preserve,
            "purge_state": "planned",
        })
    manifest: dict[str, object] = {
        "schema_version": 1,
        "operation_id": operation_id,
        "phase": "prepared",
        "worktree": str(target.worktree),
        "worktree_identity": [worktree_info.st_dev, worktree_info.st_ino],
        "admin_dir": str(target.admin_dir),
        "admin_identity": [admin_info.st_dev, admin_info.st_ino],
        "common_dir": str(target.common_dir),
        "branch_ref": target.branch_ref,
        "head": head,
        "original_dotgit_symlink": target.symlink_target,
        "database_link": None if db_link is None else {
            "link_text": db_link.link_text,
            "target": str(db_link.target),
            "target_identity": list(db_link.target_identity),
        },
        "direnv": None if direnv is None else {
            "path": str(direnv.path),
            "identity": list(direnv.identity),
            "signature": [list(entry) for entry in direnv.signature],
            "discard_requested": plan.discard_direnv_cache,
            "discardable": direnv.discardable,
            "discard_reason": direnv.discard_reason,
            "quarantine_path": str(operation_dir / DIR_ENV_NAME),
        },
        "generated_caches": generated_caches,
    }
    transaction = RemovalTransaction(operation_dir, operation_dir / "manifest.json", manifest)
    try:
        write_manifest(transaction, "prepared", create=True)
    except BaseException:
        try:
            operation_dir.rmdir()
            fsync_directory(root)
        except OSError:
            pass
        raise
    return transaction


def no_replace_rename(source: Path, destination: Path) -> None:
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        function = getattr(libc, "renamex_np", None)
        if function is None:
            raise RemovalError("renamex_np is unavailable; refusing a non-atomic no-overwrite rename")
        function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(os.fsencode(source), os.fsencode(destination), 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        function = getattr(libc, "renameat2", None)
        if function is None:
            raise RemovalError("renameat2 is unavailable; refusing a non-atomic no-overwrite rename")
        function.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise RemovalError(f"atomic no-overwrite rename is unsupported on {sys.platform}")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_manifest(transaction: RemovalTransaction, phase: str, *, create: bool = False) -> None:
    transaction.manifest["phase"] = phase
    temp = transaction.operation_dir / f"manifest.{secrets.token_hex(8)}.tmp"
    payload = (json.dumps(transaction.manifest, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if create:
            no_replace_rename(temp, transaction.manifest_path)
        else:
            current = transaction.manifest_path.lstat()
            if not stat.S_ISREG(current.st_mode) or stat.S_ISLNK(current.st_mode):
                raise RemovalError(f"transaction manifest changed type: {transaction.manifest_path}")
            os.replace(temp, transaction.manifest_path)
        fsync_directory(transaction.operation_dir)
    finally:
        if os.path.lexists(temp):
            temp.unlink()


def write_post_removal_manifest(transaction: RemovalTransaction, phase: str) -> None:
    try:
        write_manifest(transaction, phase)
    except (OSError, RemovalError) as error:
        try:
            write_manifest(transaction, "recovery_required")
        except (OSError, RemovalError) as recovery_error:
            print(f"warning: could not record recovery phase: {recovery_error}", file=sys.stderr)
        print(
            f"warning: worktree was removed; inspect transaction {transaction.manifest_path} "
            f"after failure advancing to {phase}: {error}",
            file=sys.stderr,
        )
        raise


def transact_direnv_move(transaction: RemovalTransaction, artifact: DirenvArtifact) -> Path:
    source = artifact.path
    destination = Path(str(transaction.manifest["direnv"]["quarantine_path"]))  # type: ignore[index]
    if not os.path.lexists(source):
        raise RemovalError(f".direnv disappeared after inspection: {source}")
    if os.lstat(source).st_dev != artifact.identity[0] or os.lstat(source).st_ino != artifact.identity[1]:
        raise RemovalError(f".direnv changed after inspection: {source}")
    write_manifest(transaction, "direnv_move_started")
    no_replace_rename(source, destination)
    fsync_directory(source.parent)
    fsync_directory(destination.parent)
    moved = direnv_root_signature(destination)
    if (int(moved[0][2]), int(moved[0][3])) != artifact.identity:
        raise RemovalError(f".direnv identity changed during quarantine: {destination}")
    write_manifest(transaction, "direnv_quarantined")
    return destination


def generated_cache_record(transaction: RemovalTransaction, index: int) -> dict[str, object]:
    records = transaction.manifest.get("generated_caches")
    if not isinstance(records, list) or index >= len(records) or not isinstance(records[index], dict):
        raise RemovalError("generated-cache transaction manifest is malformed")
    record = records[index]
    expected_name = f"generated-cache-{index:03d}"
    destination = Path(str(record.get("quarantine_path", "")))
    if destination.parent != transaction.operation_dir or destination.name != expected_name:
        raise RemovalError("generated-cache quarantine path in manifest is invalid")
    return record


def generated_cache_tree_paths(root: Path, signature: tuple[tuple[object, ...], ...]) -> tuple[Path, ...]:
    return tuple(
        root if entry[0] == "." else root / str(entry[0])
        for entry in signature if entry[1] != "symlink"
    )


def generated_cache_open_pids(root: Path, signature: tuple[tuple[object, ...], ...]) -> set[str] | None:
    paths = generated_cache_tree_paths(root, signature)
    return lsof_open_paths(paths) if paths else set()


def transact_generated_cache_move(
    transaction: RemovalTransaction, artifact: GeneratedCacheArtifact, index: int,
) -> Path:
    record = generated_cache_record(transaction, index)
    source = artifact.path
    destination = Path(str(record["quarantine_path"]))
    try:
        source_info = source.lstat()
    except OSError as error:
        raise RemovalError(f"generated cache disappeared after inspection: {source}: {error}") from error
    if (source_info.st_dev, source_info.st_ino) != artifact.identity:
        raise RemovalError(f"generated cache changed after inspection: {source}")
    if generated_cache_signature(source, artifact.worktree) != artifact.signature:
        raise RemovalError(f"generated artifact changed after inspection: {source}")
    open_pids = generated_cache_open_pids(source, artifact.signature)
    if open_pids is None:
        raise RemovalError(f"could not verify open handles to generated cache: {source}")
    if open_pids:
        raise RemovalError(f"processes opened generated cache during removal (pids: {', '.join(sorted(open_pids))}): {source}")

    record["purge_state"] = "move_started"
    write_manifest(transaction, f"generated_cache_{index}_move_started")
    source_info = source.lstat()
    if (source_info.st_dev, source_info.st_ino) != artifact.identity:
        raise RemovalError(f"generated cache changed before quarantine: {source}")
    if generated_cache_signature(source, artifact.worktree) != artifact.signature:
        raise RemovalError(f"generated artifact changed before quarantine: {source}")
    open_pids = generated_cache_open_pids(source, artifact.signature)
    if open_pids is None:
        raise RemovalError(f"could not verify open handles before quarantining generated cache: {source}")
    if open_pids:
        raise RemovalError(f"processes opened generated cache before quarantine (pids: {', '.join(sorted(open_pids))}): {source}")
    no_replace_rename(source, destination)
    fsync_directory(source.parent)
    fsync_directory(destination.parent)
    moved = destination.lstat()
    if (moved.st_dev, moved.st_ino) != artifact.identity:
        raise RemovalError(f"generated cache identity changed during quarantine: {destination}")
    moved_signature = generated_cache_tree_signature(destination, artifact.identity[0])
    if moved_signature != artifact.signature:
        raise RemovalError(f"generated artifact changed during quarantine: {destination}")
    record["purge_state"] = "quarantined"
    write_manifest(transaction, f"generated_cache_{index}_quarantined")
    return destination


def restore_generated_cache(transaction: RemovalTransaction, artifact: GeneratedCacheArtifact, index: int) -> bool:
    try:
        record = generated_cache_record(transaction, index)
        source = artifact.path
        quarantined = Path(str(record["quarantine_path"]))
        root_kind = next(entry[1] for entry in artifact.signature if entry[0] == ".")

        def matches_root_kind(info: os.stat_result) -> bool:
            if root_kind == "symlink":
                return stat.S_ISLNK(info.st_mode)
            if root_kind == "file":
                return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            return stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)

        source_exists = os.path.lexists(source)
        quarantine_exists = os.path.lexists(quarantined)
        if not quarantine_exists:
            if not source_exists:
                print(f"warning: both original and quarantined generated cache are missing: {source}", file=sys.stderr)
                return False
            info = source.lstat()
            if (info.st_dev, info.st_ino) != artifact.identity or not matches_root_kind(info):
                print(f"warning: generated artifact path was replaced; preserving it: {source}", file=sys.stderr)
                return False
            return True
        if source_exists:
            print(f"warning: generated cache restore path is occupied; preserving {quarantined}", file=sys.stderr)
            return False
        info = quarantined.lstat()
        if (info.st_dev, info.st_ino) != artifact.identity or not matches_root_kind(info):
            print(f"warning: generated artifact quarantine identity changed; preserving {quarantined}", file=sys.stderr)
            return False
        relative = source.relative_to(artifact.worktree)
        worktree_info = artifact.worktree.lstat()
        if stat.S_ISLNK(worktree_info.st_mode) or not stat.S_ISDIR(worktree_info.st_mode):
            print(f"warning: worktree root changed; preserving {quarantined}", file=sys.stderr)
            return False
        cursor = artifact.worktree
        for component in relative.parts[:-1]:
            cursor = cursor / component
            parent_info = cursor.lstat()
            if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
                print(f"warning: generated cache restore parent changed; preserving {quarantined}", file=sys.stderr)
                return False
        no_replace_rename(quarantined, source)
        fsync_directory(source.parent)
        restored = source.lstat()
        if (restored.st_dev, restored.st_ino) != artifact.identity:
            print(f"warning: restored generated cache identity changed: {source}", file=sys.stderr)
            return False
        return True
    except (OSError, RemovalError) as error:
        print(f"warning: could not restore generated cache {artifact.path}: {error}", file=sys.stderr)
        return False


def purge_generated_cache(
    root: Path, expected_signature: tuple[tuple[object, ...], ...], expected_device: int,
) -> str | None:
    try:
        current = generated_cache_tree_signature(root, expected_device)
    except (OSError, RemovalError) as error:
        return f"could not validate generated artifact after worktree removal ({error}); preserved in quarantine"
    if current != expected_signature:
        return "generated artifact changed after inspection; preserved in quarantine"
    open_pids = generated_cache_open_pids(root, expected_signature)
    if open_pids is None:
        return "could not verify open handles to generated artifact; preserved in quarantine"
    if open_pids:
        return f"processes still have generated artifact paths open (pids: {', '.join(sorted(open_pids))}); preserved in quarantine"

    for removed_entries, (relative, kind, device, inode, mode, size, mtime_ns, link_text) in enumerate(sorted(
        expected_signature, key=lambda entry: str(entry[0]).count("/"), reverse=True,
    )):
        path = root if relative == "." else root / str(relative)
        try:
            info = path.lstat()
        except OSError as error:
            return f"generated cache purge stopped after {removed_entries} entries ({path}: {error})"
        current_entry = (
            info.st_dev, info.st_ino, info.st_mode,
            0 if kind == "directory" else info.st_size,
            0 if kind == "directory" else info.st_mtime_ns,
            os.readlink(path) if stat.S_ISLNK(info.st_mode) else (
                hashlib.sha256(path.read_bytes()).hexdigest() if kind == "file" and link_text else ""
            ),
        )
        expected_entry = (device, inode, mode, size, mtime_ns, link_text)
        if current_entry != expected_entry:
            return f"generated artifact purge stopped after {removed_entries} entries; entry changed: {path}"
        try:
            if kind == "directory":
                path.rmdir()
            elif kind in ("file", "symlink"):
                path.unlink()
            else:
                return f"generated artifact contains an unsupported entry ({path}); preserved in quarantine"
        except OSError as error:
            return f"generated artifact purge stopped after {removed_entries} entries ({path}: {error})"
    try:
        fsync_directory(root.parent)
    except OSError as error:
        return f"generated artifact was removed but quarantine sync failed ({error})"
    return None


def lsof_open_paths(paths: tuple[Path, ...]) -> set[str] | None:
    lsof = shutil.which("lsof")
    if lsof is None:
        return None
    existing = [str(path) for path in paths if os.path.lexists(path)]
    if not existing:
        return set()
    pids: set[str] = set()
    for offset in range(0, len(existing), 64):
        result = subprocess.run(
            [lsof, "-Fpn", *existing[offset:offset + 64]], capture_output=True, text=True, check=False,
        )
        if result.returncode not in (0, 1) or result.stderr.strip():
            return None
        pid: str | None = None
        for line in result.stdout.splitlines():
            if line.startswith("p"):
                pid = line[1:]
            elif line.startswith("n") and pid is not None:
                pids.add(pid)
    return pids


def purge_direnv_cache(root: Path, expected_signature: tuple[tuple[object, ...], ...]) -> str | None:
    current = nix_direnv_cache_signature(root)
    if current is None:
        return "Nix-direnv cache changed after inspection; preserved in quarantine"
    if current != expected_signature:
        for expected, observed in zip(expected_signature, current):
            if expected != observed:
                return f"Nix-direnv cache changed after inspection at {observed[0]}; preserved in quarantine"
        return "Nix-direnv cache entries changed after inspection; preserved in quarantine"
    paths = tuple(root / str(entry[0]) if entry[0] != "." else root
                  for entry in expected_signature if entry[1] in ("directory", "file"))
    open_pids = lsof_open_paths(paths)
    if open_pids is None:
        return "could not verify open handles to Nix-direnv cache; preserved in quarantine"
    if open_pids:
        return f"processes still have Nix-direnv cache files open (pids: {', '.join(sorted(open_pids))}); preserved in quarantine"

    # Remove only the previously validated tree, deepest-first. Symlinks are unlinked, never followed.
    for relative, kind, device, inode, mode, size, mtime_ns, link_text in sorted(
        expected_signature, key=lambda entry: str(entry[0]).count("/"), reverse=True,
    ):
        if relative == ".":
            continue
        path = root / str(relative)
        try:
            info = path.lstat()
        except OSError as error:
            return f"Nix-direnv cache changed during purge ({path}: {error}); preserved in quarantine"
        current_link = os.readlink(path) if stat.S_ISLNK(info.st_mode) else ""
        current_size = 0 if kind == "directory" else info.st_size
        current_mtime_ns = 0 if kind == "directory" else info.st_mtime_ns
        current_entry = (info.st_dev, info.st_ino, info.st_mode, current_size, current_mtime_ns, current_link)
        expected_entry = (device, inode, mode, size, mtime_ns, link_text)
        if current_entry != expected_entry:
            differing = [name for name, actual, expected in zip(
                ("device", "inode", "mode", "size", "mtime", "symlink"), current_entry, expected_entry,
            ) if actual != expected]
            return f"Nix-direnv cache changed during purge ({path}: {','.join(differing)}); preserved in quarantine"
        try:
            if kind == "directory":
                path.rmdir()
            else:
                path.unlink()
        except OSError as error:
            return f"could not remove validated Nix-direnv cache entry {path}: {error}; preserved in quarantine"
    try:
        root.rmdir()
    except OSError as error:
        return f"could not remove Nix-direnv cache root {root}: {error}; preserved in quarantine"
    fsync_directory(root.parent)
    return None


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
    worktree_id = None
    if branch_ref and branch_ref.startswith("refs/heads/"):
        description = run_git(worktree, "config", "--get", f"branch.{branch_ref.removeprefix('refs/heads/')}.description").stdout.strip() or None
    else:
        try:
            record = meta.read_worktree_owner(worktree, common_dir)
        except (OSError, ValueError) as error:
            raise RemovalError(f"detached worktree owner metadata is invalid: {error}") from error
        if record is not None:
            worktree_id, description, _ = record
    return Target(
        worktree, git_dir, common_dir, worktree_command_root(entries, worktree), registered_main_worktree(entries),
        branch_ref, worktree_id, uses_annex, symlink_target, description,
    )


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


def verify_owner(target: Target, expect_branch: str | None, expect_worktree_id: str | None = None) -> None:
    if bool(expect_branch) == bool(expect_worktree_id):
        raise RemovalError("provide exactly one of --expect-branch or --expect-worktree-id")
    if expect_branch:
        if target.branch_ref is None or not target.branch_ref.startswith("refs/heads/"):
            raise RemovalError("target worktree is not on a local branch")
        branch = target.branch_ref.removeprefix("refs/heads/")
        if expect_branch != branch:
            raise RemovalError(f"branch mismatch: expected {expect_branch!r}; target is {branch!r}")
    else:
        if target.branch_ref is not None:
            raise RemovalError("target worktree is branch-backed; use --expect-branch")
        if target.worktree_id != expect_worktree_id:
            raise RemovalError(f"worktree ID mismatch: expected {expect_worktree_id!r}; target is {target.worktree_id!r}")
    owner = meta.parse_owner_description(target.description or "")
    if owner is None:
        raise RemovalError("target worktree has missing, unknown, or invalid session-owner metadata")
    _, owner_client, owner_session = owner
    current = meta.current_session_identity()
    if current is None:
        raise RemovalError("current client session is missing, ambiguous, or invalid; refusing worktree removal")
    if current != (owner_client, owner_session):
        raise RemovalError("target worktree belongs to a different client session")


def verify_safe(
    target: Target, base: str, *, allow_unreferenced_reflog: bool, expect_branch: str | None,
    expect_worktree_id: str | None = None,
    discard_direnv_cache: bool = False, discard_generated_caches: bool = False,
    discard_generated_build_outputs: bool = False, discard_generated_artifacts: bool = False,
    preserve_generated_artifacts: bool = False,
) -> RemovalPlan:
    wt = target.worktree
    verify_owner(target, expect_branch, expect_worktree_id)
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
    status = status_entries(wt)
    db_link: CanonicalDatabaseLink | None = None
    direnv_status: list[tuple[bytes, bytes]] = []
    generated_caches = (
        inspect_generated_caches(
            target, status,
            caches=discard_generated_caches or discard_generated_artifacts or preserve_generated_artifacts,
            build_outputs=discard_generated_build_outputs or discard_generated_artifacts or preserve_generated_artifacts,
            include_generated_config=discard_generated_artifacts or preserve_generated_artifacts,
            preserve=preserve_generated_artifacts,
            discard_build_outputs=discard_generated_build_outputs or discard_generated_artifacts,
        ) if discard_generated_caches or discard_generated_build_outputs or discard_generated_artifacts or preserve_generated_artifacts else ()
    )
    generated_cache_roots = tuple(os.fsencode(cache.path.relative_to(wt)) for cache in generated_caches)
    remaining: list[str] = []
    for item_status, path in status:
        if item_status == b"!!" and path == b"cultura.db" and db_link is None:
            candidate = canonical_database_link(wt, target.main_branch_worktree)
            if candidate is not None:
                db_link = candidate
                continue
        if path_is_direnv_entry(path) and item_status in (b"!!", b"??"):
            direnv_status.append((item_status, path))
            continue
        normalized_path = path.rstrip(b"/")
        if item_status in (b"!!", b"??") and any(
            normalized_path == root or normalized_path.startswith(root + b"/")
            for root in generated_cache_roots
        ):
            continue
        remaining.append(status_description(item_status, path))
    if remaining:
        raise RemovalError(f"worktree is not clean ({len(remaining)} entries):\n  " + "\n  ".join(remaining[:10]))
    direnv: DirenvArtifact | None = None
    if direnv_status:
        tracked_direnv = git_out(wt, "ls-files", "--stage", "--", ".direnv")
        if tracked_direnv:
            raise RemovalError(".direnv contains tracked files; refusing to quarantine or discard them")
        direnv = inspect_direnv(wt)
        if direnv is None:
            raise RemovalError("Git reports .direnv state, but the root path is missing; re-inspect the worktree")
    discard_direnv = discard_direnv_cache or discard_generated_artifacts
    discard_cache = bool(discard_direnv and direnv is not None and direnv.discardable)
    if discard_direnv and direnv is not None and not direnv.discardable:
        print(
            f"warning: {direnv.discard_reason}; .direnv will be preserved in quarantine",
            file=sys.stderr,
        )
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
    return RemovalPlan(db_link, direnv, discard_cache, generated_caches)


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


def rollback(target: Target, original: str | None, cause: BaseException) -> bool:
    if not target.worktree.exists():
        print(f"warning: {target.worktree} is already gone after a partial removal; inspect {target.admin_dir}", file=sys.stderr)
        return False
    try:
        current = check_dotgit(target.worktree, target.admin_dir)
        if current == original:
            return True
        if original is not None and current is None:
            replace_dotgit(target.worktree, symlink=original)
            return check_dotgit(target.worktree, target.admin_dir) == original
        if original is None and current is not None:
            replace_dotgit(target.worktree, gitfile=target.admin_dir)
            return check_dotgit(target.worktree, target.admin_dir) is None
        print(
            f"warning: .git identity changed during removal; preserving it and inspect {target.admin_dir}",
            file=sys.stderr,
        )
        return False
    except (OSError, RemovalError) as error:
        print(f"warning: could not restore .git after {cause}: {error}", file=sys.stderr)
        return False


def restore_database_symlink(target: Target, original: CanonicalDatabaseLink) -> bool:
    link = target.worktree / "cultura.db"
    if os.path.lexists(link):
        if link.is_symlink() and os.readlink(link) == original.link_text:
            return database_link_unchanged(target, original)
        print(
            "warning: cultura.db path is occupied; preserving it. "
            f"The original link was -> {original.link_text} (resolved: {original.target})",
            file=sys.stderr,
        )
        return False
    try:
        os.symlink(original.link_text, link)
        if not database_link_unchanged(target, original):
            print("warning: restored cultura.db link no longer resolves to the original canonical database", file=sys.stderr)
            return False
        return True
    except OSError as error:
        print(
            "warning: could not restore cultura.db symlink "
            f"({error}); original link was -> {original.link_text} (resolved: {original.target})",
            file=sys.stderr,
        )
        return False


def transaction_worktree_intact(target: Target, transaction: RemovalTransaction) -> bool:
    try:
        worktree_info = target.worktree.lstat()
        admin_info = target.admin_dir.lstat()
    except OSError:
        return False
    if not stat.S_ISDIR(worktree_info.st_mode) or stat.S_ISLNK(worktree_info.st_mode):
        return False
    if not stat.S_ISDIR(admin_info.st_mode) or stat.S_ISLNK(admin_info.st_mode):
        return False
    expected_worktree = transaction.manifest["worktree_identity"]
    expected_admin = transaction.manifest["admin_identity"]
    if [worktree_info.st_dev, worktree_info.st_ino] != expected_worktree:
        return False
    if [admin_info.st_dev, admin_info.st_ino] != expected_admin:
        return False
    try:
        back = read_pointer((target.admin_dir / "gitdir").read_text().strip(), target.admin_dir)
        if back.parent.resolve() != target.worktree:
            return False
        check_dotgit(target.worktree, target.admin_dir)
        if git_out(target.worktree, "rev-parse", "HEAD") != transaction.manifest["head"]:
            return False
    except (OSError, RemovalError):
        return False
    return True


def restore_direnv(transaction: RemovalTransaction, artifact: DirenvArtifact) -> bool:
    destination = artifact.path
    quarantined = Path(str(transaction.manifest["direnv"]["quarantine_path"]))  # type: ignore[index]
    if not os.path.lexists(quarantined):
        if os.path.lexists(destination):
            identity = os.lstat(destination)
            return (identity.st_dev, identity.st_ino) == artifact.identity
        print(f"warning: .direnv quarantine is missing; inspect {transaction.manifest_path}", file=sys.stderr)
        return False
    if os.path.lexists(destination):
        identity = os.lstat(destination)
        if (identity.st_dev, identity.st_ino) == artifact.identity:
            if not os.path.lexists(quarantined):
                return True
            print(
                f"warning: both original and quarantined .direnv paths exist; preserving {quarantined}",
                file=sys.stderr,
            )
            return False
        print(
            f"warning: .direnv path is occupied; preserving both it and {quarantined}",
            file=sys.stderr,
        )
        return False
    try:
        no_replace_rename(quarantined, destination)
        fsync_directory(destination.parent)
        return True
    except (OSError, RemovalError) as error:
        print(f"warning: could not restore .direnv from {quarantined}: {error}", file=sys.stderr)
        return False


def transaction_cleanup(transaction: RemovalTransaction) -> None:
    manifest = transaction.manifest_path
    try:
        unexpected = [path for path in transaction.operation_dir.iterdir() if path != manifest]
    except OSError as error:
        raise RemovalError(f"cannot inspect quarantine transaction {transaction.operation_dir}: {error}") from error
    if unexpected:
        raise RemovalError(
            "quarantine transaction contains unexpected entries; preserving it: "
            + ", ".join(str(path) for path in unexpected[:5])
        )
    if os.path.lexists(manifest):
        info = manifest.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise RemovalError(f"transaction manifest changed type: {manifest}")
        manifest.unlink()
    transaction.operation_dir.rmdir()
    fsync_directory(transaction.operation_dir.parent)


def known_generated_artifact_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or ".direnv" in parts:
        return False
    path = Path(value)
    if path.is_absolute():
        return False
    text = path.as_posix()
    return (
        text in (PRECOMMIT_CONFIG_NAME, ".pytest_cache", ".ruff_cache", "target", "rust/target", "result")
        or path.name == "__pycache__"
    )


def purgeable_transaction_phase(phase: object) -> bool:
    if phase in {
        "completed_preserved", "purging_preserved", "caches_purged",
        "worktree_remove_started", "worktree_removed", "direnv_cache_purge_started",
        "direnv_cache_purged",
    }:
        return True
    return isinstance(phase, str) and re.fullmatch(
        r"generated_cache_\d+_(?:move_started|quarantined|retained|purge_started|purged)", phase,
    ) is not None


def parse_quarantine_signature(raw: object, label: str) -> tuple[tuple[object, ...], ...]:
    if not isinstance(raw, list):
        raise RemovalError(f"quarantine signature is malformed: {label}")
    signature: list[tuple[object, ...]] = []
    for entry in raw:
        if (
            not isinstance(entry, list) or len(entry) != 8
            or not isinstance(entry[0], str)
            or entry[1] not in ("directory", "file", "symlink")
            or any(not isinstance(value, int) or isinstance(value, bool) for value in entry[2:7])
            or not isinstance(entry[7], str)
        ):
            raise RemovalError(f"quarantine signature is malformed: {label}")
        relative = entry[0]
        if (
            relative != "."
            and (relative.startswith("/") or "\\" in relative
                 or any(part in ("", ".", "..") for part in relative.removeprefix("./").split("/")))
        ):
            raise RemovalError(f"quarantine signature contains an unsafe path: {label}")
        signature.append(tuple(entry))
    if not signature or signature[0][0] != ".":
        raise RemovalError(f"quarantine signature has no root entry: {label}")
    return tuple(signature)


def signature_order(signature: tuple[tuple[object, ...], ...]) -> tuple[tuple[object, ...], ...]:
    return tuple(sorted(signature, key=lambda entry: str(entry[0]).count("/"), reverse=True))


def verify_signature_entry(root: Path, entry: tuple[object, ...]) -> bool:
    relative, kind, device, inode, mode, size, mtime_ns, link_text = entry
    path = root if relative == "." else root / str(relative)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if (info.st_dev, info.st_ino, info.st_mode) != (device, inode, mode):
        return False
    current_size = 0 if kind == "directory" else info.st_size
    current_mtime = 0 if kind == "directory" else info.st_mtime_ns
    if kind == "symlink":
        current_link = os.readlink(path)
    elif kind == "file" and link_text:
        current_link = hashlib.sha256(path.read_bytes()).hexdigest()
    elif kind in ("directory", "file"):
        current_link = ""
    else:
        return False
    return (current_size, current_mtime, current_link) == (size, mtime_ns, link_text)


def verify_purge_progress(
    root: Path, signature: tuple[tuple[object, ...], ...], record: dict[str, object],
) -> None:
    entries = signature_order(signature)
    cursor = record.get("purge_cursor", 0)
    pending = record.get("purge_pending")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or not 0 <= cursor <= len(entries):
        raise RemovalError(f"invalid purge cursor in quarantine manifest: {root}")
    if pending is not None and (cursor >= len(entries) or pending != entries[cursor][0]):
        raise RemovalError(f"invalid pending purge entry in quarantine manifest: {root}")
    for index, entry in enumerate(entries):
        path = root if entry[0] == "." else root / str(entry[0])
        exists = os.path.lexists(path)
        if index < cursor:
            if exists:
                raise RemovalError(f"already-purged entry reappeared in quarantine: {path}")
        elif index == cursor and pending == entry[0]:
            if exists and not verify_signature_entry(root, entry):
                raise RemovalError(f"pending generated artifact changed in quarantine: {path}")
        elif not exists or not verify_signature_entry(root, entry):
            raise RemovalError(f"generated artifact changed during an interrupted purge: {path}")
    expected_paths = {
        str(entry[0]) for index, entry in enumerate(entries)
        if index >= cursor
        and not (index == cursor and pending == entry[0] and not os.path.lexists(root if entry[0] == "." else root / str(entry[0])))
    }
    observed_paths = {str(entry[0]) for entry in direnv_tree_signature(root)}
    if observed_paths != expected_paths:
        extras = sorted(observed_paths - expected_paths)
        missing = sorted(expected_paths - observed_paths)
        details = []
        if extras:
            details.append("unrecognized entries: " + ", ".join(extras[:5]))
        if missing:
            details.append("missing signed entries: " + ", ".join(missing[:5]))
        raise RemovalError(f"quarantine contents changed during an interrupted purge ({'; '.join(details)}): {root}")


def verify_purge_root_missing(
    signature: tuple[tuple[object, ...], ...], record: dict[str, object], label: str,
) -> None:
    entries = signature_order(signature)
    if not entries or entries[-1][0] != ".":
        raise RemovalError(f"purge signature has no final root entry: {label}")
    cursor = record.get("purge_cursor", 0)
    pending = record.get("purge_pending")
    if not isinstance(cursor, int) or isinstance(cursor, bool):
        raise RemovalError(f"invalid purge cursor for missing root: {label}")
    root_index = len(entries) - 1
    if not (
        (pending == "." and cursor == root_index)
        or (pending is None and cursor == len(entries))
    ):
        raise RemovalError(f"quarantine root disappeared before its signed purge step: {label}")


def purge_signature_tree(
    root: Path, signature: tuple[tuple[object, ...], ...], record: dict[str, object],
    transaction: RemovalTransaction,
) -> str | None:
    entries = signature_order(signature)
    open_paths = tuple(
        root if entry[0] == "." else root / str(entry[0])
        for entry in entries if entry[1] != "symlink"
    )
    open_pids = lsof_open_paths(open_paths) if open_paths else set()
    if open_pids is None:
        return f"could not verify open handles to generated artifact: {root}"
    if open_pids:
        return f"processes still have generated artifact paths open (pids: {', '.join(sorted(open_pids))}): {root}"
    cursor = record.get("purge_cursor", 0)
    pending = record.get("purge_pending")
    if not isinstance(cursor, int) or isinstance(cursor, bool) or not 0 <= cursor <= len(entries):
        return f"invalid purge cursor for {root}"
    if pending is not None and (cursor >= len(entries) or pending != entries[cursor][0]):
        return f"invalid pending purge entry for {root}"
    for index in range(cursor, len(entries)):
        relative, kind = entries[index][0], entries[index][1]
        path = root if relative == "." else root / str(relative)
        if index == cursor and pending == relative and not os.path.lexists(path):
            record["purge_cursor"] = index + 1
            record.pop("purge_pending", None)
            write_manifest(transaction, "purging_preserved")
            continue
        if not verify_signature_entry(root, entries[index]):
            return f"generated artifact changed or a purge entry disappeared: {path}"
        record["purge_state"] = "purging"
        record["purge_cursor"] = index
        record["purge_pending"] = relative
        write_manifest(transaction, "purging_preserved")
        try:
            if kind == "directory":
                path.rmdir()
            elif kind in ("file", "symlink"):
                path.unlink()
            else:
                return f"unsupported entry in generated artifact: {path}"
            fsync_directory(path.parent)
        except OSError as error:
            record["purge_warning"] = f"could not purge {path}: {error}"
            write_manifest(transaction, "purging_preserved")
            return str(record["purge_warning"])
        record["purge_cursor"] = index + 1
        record.pop("purge_pending", None)
        record.pop("purge_warning", None)
        write_manifest(transaction, "purging_preserved")
    record["purge_state"] = "purged"
    for key in ("purge_cursor", "purge_pending", "purge_warning"):
        record.pop(key, None)
    write_manifest(transaction, "purging_preserved")
    return None


def load_preserved_transaction(
    repo_arg: str, operation_id: str, *, discard_unverified_direnv: bool = False,
) -> tuple[Path, RemovalTransaction, list[tuple[int, GeneratedCacheArtifact | None]], DirenvArtifact | None]:
    if not re.fullmatch(r"[0-9a-f]{32}", operation_id):
        raise RemovalError("quarantine operation ID must be 32 lowercase hexadecimal characters")
    repo = Path(git_out(Path(repo_arg).expanduser().resolve(), "rev-parse", "--show-toplevel")).resolve()
    entries = list_worktrees(repo)
    main = registered_main_worktree(entries)
    if main is None:
        raise RemovalError("repository does not have exactly one registered main worktree")
    common = Path(git_out(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    state_home = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))).expanduser()
    if not state_home.is_absolute():
        raise RemovalError("XDG_STATE_HOME must be absolute for quarantine cleanup")
    root = state_home / main.name / "worktrees" / ".removal-quarantine"
    operation = root / operation_id
    if not os.path.lexists(root) or not os.path.lexists(operation):
        raise RemovalError(f"preserved quarantine transaction not found: {operation}")
    root_info, operation_info = root.lstat(), operation.lstat()
    if (
        not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode)
        or root_info.st_uid != os.getuid() or root_info.st_mode & 0o077
    ):
        raise RemovalError(f"quarantine root is not a private directory owned by the current user: {root}")
    if (
        not stat.S_ISDIR(operation_info.st_mode) or stat.S_ISLNK(operation_info.st_mode)
        or operation_info.st_uid != os.getuid() or operation_info.st_mode & 0o077
        or operation_info.st_dev != root_info.st_dev
    ):
        raise RemovalError(f"quarantine operation is not a private directory on the expected filesystem: {operation}")
    manifest_path = operation / "manifest.json"
    manifest_info = manifest_path.lstat()
    if (
        not stat.S_ISREG(manifest_info.st_mode) or stat.S_ISLNK(manifest_info.st_mode)
        or manifest_info.st_uid != os.getuid() or manifest_info.st_mode & 0o077
    ):
        raise RemovalError(f"quarantine manifest is not a regular file owned by the current user: {manifest_path}")
    if manifest_info.st_size > 64 * 1024 * 1024:
        raise RemovalError(f"quarantine manifest exceeds the size limit: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RemovalError(f"cannot read quarantine manifest {manifest_path}: {error}") from error
    if "generated_caches" not in manifest:
        manifest["generated_caches"] = []
    if (
        manifest.get("schema_version") != 1
        or manifest.get("operation_id") != operation_id
        or manifest.get("common_dir") != str(common)
        or not purgeable_transaction_phase(manifest.get("phase"))
    ):
        raise RemovalError(f"quarantine manifest is not a completed preserved transaction for this repository: {manifest_path}")
    worktree = Path(str(manifest.get("worktree", ""))).expanduser()
    if not worktree.is_absolute() or os.path.lexists(worktree):
        raise RemovalError(f"original worktree still exists or its path is invalid: {worktree}")
    if any(entry["path"] == worktree.resolve(strict=False) for entry in entries):
        raise RemovalError(f"original worktree is still registered: {worktree}")
    head = manifest.get("head")
    if not isinstance(head, str) or not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise RemovalError("quarantine manifest has no valid HEAD object ID")
    if run_git(main, "merge-base", "--is-ancestor", head, "main").returncode != 0:
        raise RemovalError("original worktree HEAD is not contained in the current main branch")
    branch_ref = manifest.get("branch_ref")
    if branch_ref is not None and (not isinstance(branch_ref, str) or not branch_ref.startswith("refs/heads/")):
        raise RemovalError("quarantine manifest has an invalid local branch ref")
    if isinstance(branch_ref, str):
        branch = run_git(main, "rev-parse", "--verify", branch_ref)
        if branch.returncode == 0 and branch.stdout.strip() != head:
            raise RemovalError(f"original worktree branch moved after removal: {branch_ref}")

    transaction = RemovalTransaction(operation, manifest_path, manifest)
    records = manifest.get("generated_caches")
    if not isinstance(records, list):
        raise RemovalError("quarantine manifest has an invalid generated-cache list")
    expected_entries = {"manifest.json"}
    artifacts: list[tuple[int, GeneratedCacheArtifact | None]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not known_generated_artifact_path(record.get("path")):
            raise RemovalError("quarantine manifest contains an unrecognized generated-artifact path")
        cache_record = generated_cache_record(transaction, index)
        archive = Path(str(cache_record["quarantine_path"]))
        state = cache_record.get("purge_state")
        if state == "purged":
            if os.path.lexists(archive):
                raise RemovalError(f"manifest marks an artifact purged but its quarantine path remains: {archive}")
            continue
        if state not in (None, "planned", "move_started", "quarantined", "started", "retained", "preserved", "purging"):
            raise RemovalError(f"generated artifact is not a retained quarantine entry: {archive}")
        identity = cache_record.get("identity")
        raw_signature = cache_record.get("signature")
        if (
            not isinstance(identity, list) or len(identity) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) for value in identity)
            or not isinstance(raw_signature, list)
        ):
            raise RemovalError(f"generated artifact identity/signature is malformed: {archive}")
        signature = parse_quarantine_signature(raw_signature, str(archive))
        root_entry = next((entry for entry in signature if entry[0] == "."), None)
        if root_entry is None or (root_entry[2], root_entry[3]) != tuple(identity):
            raise RemovalError(f"generated artifact root identity disagrees with its signature: {archive}")
        if not os.path.lexists(archive):
            if state == "purging":
                verify_purge_root_missing(signature, cache_record, str(archive))
                artifacts.append((index, None))
                continue
            raise RemovalError(f"retained generated artifact is missing: {archive}")
        artifact_info = archive.lstat()
        if (artifact_info.st_dev, artifact_info.st_ino) != tuple(identity):
            raise RemovalError(f"generated artifact identity changed in quarantine: {archive}")
        if state == "purging":
            verify_purge_progress(archive, signature, cache_record)
        elif generated_cache_tree_signature(archive, int(identity[0])) != signature:
            raise RemovalError(f"generated artifact contents changed in quarantine: {archive}")
        open_pids = generated_cache_open_pids(archive, signature)
        if open_pids is None or open_pids:
            detail = "could not inspect open handles" if open_pids is None else f"open by pids {', '.join(sorted(open_pids))}"
            raise RemovalError(f"generated artifact cannot be purged while {detail}: {archive}")
        expected_entries.add(archive.name)
        artifacts.append((index, GeneratedCacheArtifact(
            archive, worktree, (int(identity[0]), int(identity[1])), signature, False,
        )))

    direnv_record = manifest.get("direnv")
    direnv: DirenvArtifact | None = None
    if direnv_record is not None:
        if not isinstance(direnv_record, dict):
            raise RemovalError("quarantine manifest has an invalid .direnv record")
        archive = operation / DIR_ENV_NAME
        if direnv_record.get("quarantine_path") != str(archive):
            raise RemovalError(".direnv quarantine path in manifest is invalid")
        state = direnv_record.get("purge_state")
        if state == "purged":
            if os.path.lexists(archive):
                raise RemovalError(f"manifest marks .direnv purged but its quarantine path remains: {archive}")
        elif state == "purging" and not os.path.lexists(archive):
            identity = direnv_record.get("identity")
            signature = parse_quarantine_signature(direnv_record.get("signature"), str(archive))
            root_entry = next((entry for entry in signature if entry[0] == "."), None)
            if (
                not isinstance(identity, list) or len(identity) != 2
                or any(not isinstance(value, int) or isinstance(value, bool) for value in identity)
                or root_entry is None or (root_entry[2], root_entry[3]) != tuple(identity)
            ):
                raise RemovalError(f".direnv root identity disagrees with its signature: {archive}")
            verify_purge_root_missing(signature, direnv_record, str(archive))
            expected_entries.discard(DIR_ENV_NAME)
        else:
            if state not in (None, "started", "retained", "preserved", "purging") or not direnv_record.get("discardable"):
                raise RemovalError("quarantined .direnv is not a verified disposable Nix-direnv cache")
            identity = direnv_record.get("identity")
            if (
                not isinstance(identity, list) or len(identity) != 2
                or any(not isinstance(value, int) or isinstance(value, bool) for value in identity)
                or not os.path.lexists(archive)
            ):
                raise RemovalError(f"verified .direnv quarantine is missing or malformed: {archive}")
            info = archive.lstat()
            if (info.st_dev, info.st_ino) != tuple(identity):
                raise RemovalError(f".direnv identity changed in quarantine: {archive}")
            raw_signature = direnv_record.get("signature")
            if state == "purging":
                signature = parse_quarantine_signature(raw_signature, str(archive))
                verify_purge_progress(archive, signature, direnv_record)
            else:
                observed_signature = nix_direnv_cache_signature(archive)
                if observed_signature is None:
                    raise RemovalError(f".direnv no longer matches the verified Nix-direnv layout: {archive}")
                if raw_signature is None:
                    if not discard_unverified_direnv:
                        raise RemovalError(
                            "preserved .direnv has no saved content signature; explicit "
                            "--discard-unverified-direnv is required for this legacy transaction"
                        )
                    signature = observed_signature
                else:
                    signature = parse_quarantine_signature(raw_signature, str(archive))
                    if observed_signature != signature:
                        raise RemovalError(f".direnv content changed since quarantine: {archive}")
            open_paths = tuple(
                archive / str(entry[0]) if entry[0] != "." else archive
                for entry in signature if entry[1] in ("directory", "file")
            )
            open_pids = lsof_open_paths(open_paths)
            if open_pids is None or open_pids:
                detail = "could not inspect open handles" if open_pids is None else f"open by pids {', '.join(sorted(open_pids))}"
                raise RemovalError(f".direnv cannot be purged while {detail}: {archive}")
            direnv = DirenvArtifact(archive, (int(identity[0]), int(identity[1])), signature, True, None)
            expected_entries.add(DIR_ENV_NAME)

    unexpected = sorted(entry.name for entry in operation.iterdir() if entry.name not in expected_entries)
    if unexpected:
        raise RemovalError("quarantine contains unrecognized entries; preserving it: " + ", ".join(unexpected[:10]))
    return common, transaction, artifacts, direnv


def purge_preserved_quarantine(
    repo_arg: str, operation_id: str, *, dry_run: bool, lock_name: str,
    discard_unverified_direnv: bool = False,
) -> None:
    common, transaction, artifacts, direnv = load_preserved_transaction(
        repo_arg, operation_id, discard_unverified_direnv=discard_unverified_direnv,
    )
    direnv_record = transaction.manifest.get("direnv")
    paths = ([".direnv"] if isinstance(direnv_record, dict) and direnv_record.get("purge_state") != "purged" else []) + [
        str(transaction.manifest["generated_caches"][index]["path"])  # type: ignore[index]
        for index, _ in artifacts
    ]
    if dry_run:
        print(f"dry-run ok: would purge preserved generated artifacts from {transaction.operation_dir}: {', '.join(paths) or 'none'}")
        return
    with exclusive_lock(common, lock_name):
        common, transaction, artifacts, direnv = load_preserved_transaction(
            repo_arg, operation_id, discard_unverified_direnv=discard_unverified_direnv,
        )
        direnv_record = transaction.manifest.get("direnv")
        if isinstance(direnv_record, dict) and direnv_record.get("purge_state") == "purging" and direnv is None:
            direnv_record["purge_state"] = "purged"
            direnv_record.pop("purge_cursor", None)
            direnv_record.pop("purge_pending", None)
            direnv_record.pop("purge_warning", None)
            write_manifest(transaction, "purging_preserved")
        elif direnv is not None:
            record = transaction.manifest["direnv"]
            assert isinstance(record, dict)
            record["purge_state"] = "purging"
            record.setdefault("signature", [list(entry) for entry in direnv.signature])
            write_manifest(transaction, "purging_preserved")
            reason = purge_signature_tree(direnv.path, direnv.signature, record, transaction)
            if reason is not None:
                record["purge_warning"] = reason
                write_manifest(transaction, "purging_preserved")
                raise RemovalError(f"preserved .direnv remains in quarantine: {reason}")
            record["purge_state"] = "purged"
            record.pop("purge_cursor", None)
            record.pop("purge_pending", None)
            record.pop("purge_warning", None)
            write_manifest(transaction, "purging_preserved")

        records = transaction.manifest["generated_caches"]
        assert isinstance(records, list)
        for index, artifact in artifacts:
            record = records[index]
            assert isinstance(record, dict)
            if artifact is None:
                record["purge_state"] = "purged"
                record.pop("purge_cursor", None)
                record.pop("purge_pending", None)
                record.pop("purge_warning", None)
                write_manifest(transaction, "purging_preserved")
                continue
            record["purge_state"] = "purging"
            write_manifest(transaction, "purging_preserved")
            reason = purge_signature_tree(artifact.path, artifact.signature, record, transaction)
            if reason is not None:
                record["purge_warning"] = reason
                write_manifest(transaction, "purging_preserved")
                raise RemovalError(f"preserved generated artifact remains in quarantine: {reason}")
            record["purge_state"] = "purged"
            record.pop("purge_cursor", None)
            record.pop("purge_pending", None)
            record.pop("purge_warning", None)
            write_manifest(transaction, "purging_preserved")
        write_manifest(transaction, "caches_purged")
        transaction_cleanup(transaction)
    print(f"purged preserved generated artifacts from {transaction.operation_dir}: {', '.join(paths) or 'none'}")


def show_status_entries(entries: list[tuple[bytes, bytes]]) -> str:
    return "\n  ".join(status_description(status, path) for status, path in entries[:10])


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
    expect_branch: str | None, expect_worktree_id: str | None = None,
    discard_direnv_cache: bool = False, discard_generated_caches: bool = False,
    discard_generated_build_outputs: bool = False, discard_generated_artifacts: bool = False,
    preserve_generated_artifacts: bool = False,
) -> RemovalOutcome:
    worktree, common_dir = locate(worktree_arg)
    with exclusive_lock(common_dir, lock_name):
        target = inspect(worktree)
        print(target.owner_line, file=sys.stderr)
        pending = unresolved_transaction(target)
        if pending is not None:
            raise RemovalError(f"an interrupted removal transaction needs inspection first: {pending}")
        verify_owner(target, expect_branch, expect_worktree_id)
        if target.uses_annex:
            result = run_git(worktree, "annex", "restage")
            if result.returncode != 0:
                raise RemovalError(f"git annex restage failed: {result.stderr.strip()}")
            target = inspect(worktree)
        plan = verify_safe(
            target, base, allow_unreferenced_reflog=allow_unreferenced_reflog,
            expect_branch=expect_branch, expect_worktree_id=expect_worktree_id,
            discard_direnv_cache=discard_direnv_cache, discard_generated_caches=discard_generated_caches,
            discard_generated_build_outputs=discard_generated_build_outputs,
            discard_generated_artifacts=discard_generated_artifacts,
            preserve_generated_artifacts=preserve_generated_artifacts,
        )
        base_oid = resolve_base(target, base)
        head = git_out(worktree, "rev-parse", "HEAD")
        transaction = create_transaction(target, head, plan) if plan.database_link or plan.direnv or plan.generated_caches else None
        direnv_moved = False
        db_link_removed = False
        git_removed = False
        dotgit_symlink_before_normalization = target.symlink_target
        try:
            if plan.direnv is not None and transaction is not None:
                transact_direnv_move(transaction, plan.direnv)
                direnv_moved = True
            if transaction is not None:
                for index, cache in enumerate(plan.generated_caches):
                    transact_generated_cache_move(transaction, cache, index)
            check_dotgit(worktree, target.admin_dir)
            if git_out(worktree, "rev-parse", "HEAD") != head:
                raise RemovalError("HEAD changed during removal")
            if plan.database_link is not None:
                if not database_link_unchanged(target, plan.database_link):
                    raise RemovalError("cultura.db symlink or canonical main database changed during removal")
                (worktree / "cultura.db").unlink()
                db_link_removed = True
                if transaction is not None:
                    write_manifest(transaction, "database_symlink_unlinked")
                remaining = status_entries(worktree)
                if remaining:
                    raise RemovalError(
                        f"worktree changed after removing its canonical DB symlink:\n  {show_status_entries(remaining)}"
                    )
                if canonical_database_target(worktree, target.main_branch_worktree) != (
                    plan.database_link.target, plan.database_link.target_identity,
                ):
                    raise RemovalError("canonical main database changed during worktree removal")
            elif status_entries(worktree):
                raise RemovalError(
                    "worktree changed after removing generated state:\n  "
                    + show_status_entries(status_entries(worktree))
                )
            # Annex filters can restore the symlink during status; normalize only after that check.
            dotgit_symlink_before_normalization = check_dotgit(worktree, target.admin_dir)
            if dotgit_symlink_before_normalization is not None:
                if target.symlink_target is None and not target.uses_annex:
                    raise RemovalError(".git changed from a gitfile to a symlink during removal")
                replace_dotgit(worktree, gitfile=target.admin_dir)
                if transaction is not None:
                    transaction.manifest["original_dotgit_symlink"] = dotgit_symlink_before_normalization
                    write_manifest(transaction, "dotgit_normalized")
            if check_dotgit(worktree, target.admin_dir) is not None:
                raise RemovalError(".git is not a gitfile immediately before worktree removal")
            if transaction is not None:
                write_manifest(transaction, "worktree_remove_started")
            result = run_git(target.main_worktree, "worktree", "remove", str(worktree))
            if result.returncode != 0:
                raise RemovalError(f"git worktree remove refused: {result.stderr.strip()}")
            git_removed = True
            registered = [entry for entry in list_worktrees(target.main_worktree) if entry["path"] == worktree]
            if worktree.exists() or registered:
                raise RemovalError(
                    "git worktree remove returned success but the worktree path or registration remains; "
                    "inspect before retrying"
                )
            if transaction is not None:
                write_manifest(transaction, "worktree_removed")
        except BaseException as cause:
            if not direnv_moved and transaction is not None and plan.direnv is not None:
                archive = Path(str(transaction.manifest["direnv"]["quarantine_path"]))  # type: ignore[index]
                direnv_moved = os.path.lexists(archive) and not os.path.lexists(plan.direnv.path)
            if transaction is not None and git_removed:
                try:
                    write_manifest(transaction, "recovery_required")
                except (OSError, RemovalError) as error:
                    print(f"warning: could not record partial removal state: {error}", file=sys.stderr)
                print(f"warning: inspect interrupted removal manifest {transaction.manifest_path}", file=sys.stderr)
                raise
            intact = transaction is None or transaction_worktree_intact(target, transaction)
            if not intact:
                print("warning: worktree/admin identity changed; refusing automatic rollback", file=sys.stderr)
            dotgit_ok = rollback(target, dotgit_symlink_before_normalization, cause) if intact else False
            db_ok = True
            if db_link_removed and plan.database_link is not None and intact:
                db_ok = restore_database_symlink(target, plan.database_link)
            direnv_ok = True
            if direnv_moved and plan.direnv is not None and intact and transaction is not None:
                direnv_ok = restore_direnv(transaction, plan.direnv)
            elif direnv_moved:
                direnv_ok = False
            generated_caches_ok = True
            if transaction is not None and intact:
                for index, cache in reversed(tuple(enumerate(plan.generated_caches))):
                    generated_caches_ok = restore_generated_cache(transaction, cache, index) and generated_caches_ok
            elif plan.generated_caches:
                generated_caches_ok = False
            rollback_ok = intact and dotgit_ok and db_ok and direnv_ok and generated_caches_ok
            if transaction is not None:
                if rollback_ok:
                    try:
                        write_manifest(transaction, "rollback_completed")
                        transaction_cleanup(transaction)
                    except (OSError, RemovalError) as error:
                        try:
                            write_manifest(transaction, "recovery_required")
                        except (OSError, RemovalError):
                            pass
                        print(f"warning: rollback completed but transaction cleanup failed; inspect {transaction.operation_dir}: {error}", file=sys.stderr)
                else:
                    try:
                        write_manifest(transaction, "recovery_required")
                    except (OSError, RemovalError) as error:
                        print(f"warning: could not record recovery state: {error}", file=sys.stderr)
                    print(f"warning: preserved recovery state at {transaction.operation_dir}", file=sys.stderr)
            raise
        preserved_direnv: Path | None = None
        discarded_direnv = False
        preserved_generated_caches: list[Path] = []
        discarded_generated_caches: list[str] = []
        if transaction is not None:
            preservation_reasons: list[str] = []
            if plan.direnv is not None:
                direnv_record = transaction.manifest["direnv"]
                assert isinstance(direnv_record, dict)
                archive = Path(str(direnv_record["quarantine_path"]))
                if plan.discard_direnv_cache:
                    write_post_removal_manifest(transaction, "direnv_cache_purge_started")
                    direnv_record["purge_state"] = "purging"
                    direnv_record["signature"] = [list(entry) for entry in plan.direnv.signature]
                    write_post_removal_manifest(transaction, "direnv_cache_purge_started")
                    reason = purge_signature_tree(archive, plan.direnv.signature, direnv_record, transaction)
                    if reason is None:
                        discarded_direnv = True
                        direnv_record["purge_state"] = "purged"
                        direnv_record.pop("purge_cursor", None)
                        direnv_record.pop("purge_pending", None)
                        direnv_record.pop("purge_warning", None)
                        write_post_removal_manifest(transaction, "direnv_cache_purged")
                    elif not os.path.lexists(archive):
                        try:
                            verify_purge_root_missing(plan.direnv.signature, direnv_record, str(archive))
                        except RemovalError as error:
                            reason = f"{reason}; root disappearance did not match the purge journal ({error})"
                            preserved_direnv = archive
                            direnv_record["purge_warning"] = reason
                            preservation_reasons.append(reason)
                            print(f"warning: {reason}; inspect transaction {transaction.manifest_path}", file=sys.stderr)
                        else:
                            discarded_direnv = True
                            direnv_record["purge_state"] = "purged"
                            direnv_record.pop("purge_cursor", None)
                            direnv_record.pop("purge_pending", None)
                            direnv_record.pop("purge_warning", None)
                            write_post_removal_manifest(transaction, "direnv_cache_purged")
                    else:
                        preserved_direnv = archive
                        direnv_record["purge_warning"] = reason
                        preservation_reasons.append(reason)
                        print(f"warning: {reason}; preserved at {archive}", file=sys.stderr)
                else:
                    preserved_direnv = archive
                    direnv_record["purge_state"] = "retained"

            for index, cache in enumerate(plan.generated_caches):
                cache_record = generated_cache_record(transaction, index)
                archive = Path(str(cache_record["quarantine_path"]))
                if cache.preserve:
                    cache_record["purge_state"] = "retained"
                    cache_record["preserve_reason"] = "explicitly retained generated artifact"
                    preserved_generated_caches.append(archive)
                    preservation_reasons.append(str(cache.path.relative_to(target.worktree)))
                    write_post_removal_manifest(transaction, f"generated_cache_{index}_retained")
                    continue
                cache_record["purge_state"] = "purging"
                write_post_removal_manifest(transaction, f"generated_cache_{index}_purge_started")
                try:
                    reason = purge_signature_tree(archive, cache.signature, cache_record, transaction)
                except (OSError, RemovalError) as error:
                    reason = f"could not purge generated cache ({error}); preserved in quarantine"
                if reason is None:
                    cache_record["purge_state"] = "purged" if reason is None else "purged_with_warning"
                    cache_record.pop("purge_cursor", None)
                    cache_record.pop("purge_pending", None)
                    cache_record.pop("purge_warning", None)
                    discarded_generated_caches.append(str(cache.path.relative_to(target.worktree)))
                    write_post_removal_manifest(transaction, f"generated_cache_{index}_purged")
                elif not os.path.lexists(archive):
                    try:
                        verify_purge_root_missing(cache.signature, cache_record, str(archive))
                    except RemovalError as error:
                        reason = f"{reason}; root disappearance did not match the purge journal ({error})"
                        cache_record["purge_warning"] = reason
                        preserved_generated_caches.append(archive)
                        preservation_reasons.append(reason)
                        print(f"warning: {reason}; inspect transaction {transaction.manifest_path}", file=sys.stderr)
                    else:
                        cache_record["purge_state"] = "purged"
                        cache_record.pop("purge_cursor", None)
                        cache_record.pop("purge_pending", None)
                        cache_record.pop("purge_warning", None)
                        discarded_generated_caches.append(str(cache.path.relative_to(target.worktree)))
                        write_post_removal_manifest(transaction, f"generated_cache_{index}_purged")
                else:
                    cache_record["purge_warning"] = reason
                    preserved_generated_caches.append(archive)
                    preservation_reasons.append(reason)
                    print(f"warning: {reason}; preserved at {archive}", file=sys.stderr)

            if preservation_reasons or preserved_direnv is not None or preserved_generated_caches:
                transaction.manifest["preserve_reason"] = "; ".join(preservation_reasons) or "retained .direnv state"
                write_post_removal_manifest(transaction, "completed_preserved")
            else:
                try:
                    write_post_removal_manifest(
                        transaction,
                        "caches_purged" if discarded_direnv or discarded_generated_caches else "worktree_removed",
                    )
                    transaction_cleanup(transaction)
                except (OSError, RemovalError) as error:
                    try:
                        write_manifest(transaction, "recovery_required")
                    except (OSError, RemovalError):
                        pass
                    print(f"warning: worktree removed but transaction metadata remains: {error}", file=sys.stderr)
        if delete_branch_too:
            delete_branch(target, head, base_oid)
    return RemovalOutcome(
        target, preserved_direnv, discarded_direnv, tuple(preserved_generated_caches), tuple(discarded_generated_caches),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely remove a linked Git worktree (git-annex aware).")
    parser.add_argument("worktree", nargs="?", help="path of the linked worktree to remove")
    parser.add_argument("--repo", help="repository containing a preserved quarantine transaction")
    parser.add_argument("--purge-preserved-quarantine", metavar="OPERATION_ID", help="purge one completed preserved transaction by its exact 32-hex ID")
    parser.add_argument(
        "--discard-unverified-direnv", action="store_true",
        help="allow purging a legacy preserved .direnv cache without its original content signature",
    )
    parser.add_argument("--base", default="main", help="ref that must already contain HEAD (default: main)")
    parser.add_argument("--delete-branch", action="store_true", help="also delete the worktree's branch when it is fully contained in --base")
    parser.add_argument("--allow-unreferenced-reflog", action="store_true", help="accept commits that only this worktree's HEAD reflog references")
    parser.add_argument("--expect-branch", metavar="BRANCH", help="exact legacy local branch to remove; the current client session must own it")
    parser.add_argument("--expect-worktree-id", metavar="ID", help="exact detached task worktree ID to remove; the current client session must own it")
    parser.add_argument("--expect-owner", metavar="TEXT", help=argparse.SUPPRESS)
    parser.add_argument(
        "--discard-direnv-cache", action="store_true",
        help="discard a verified Nix-direnv use-flake cache after successful removal (including edits in the cache)",
    )
    parser.add_argument(
        "--discard-generated-caches", action="store_true",
        help="discard all contents of recognized pytest, Ruff, and Python bytecode caches after successful removal",
    )
    parser.add_argument(
        "--discard-generated-build-outputs", action="store_true",
        help="discard only rust/target and unlink the root result symlink after successful removal",
    )
    parser.add_argument(
        "--discard-generated-artifacts", action="store_true",
        help="discard all recognized generated artifacts after successful removal",
    )
    parser.add_argument(
        "--preserve-generated-artifacts", action="store_true",
        help="quarantine and retain recognized caches and a marked git-hooks.nix config",
    )
    parser.add_argument("--dry-run", action="store_true", help="run the checks without the lock or restage; change nothing")
    parser.add_argument("--lock-name", default=DEFAULT_LOCK_NAME, help="lock directory created under the common git dir")
    args = parser.parse_args(argv)
    try:
        if args.purge_preserved_quarantine is not None:
            if args.worktree is not None or args.repo is None:
                raise RemovalError("--purge-preserved-quarantine requires --repo and must not be combined with a worktree path")
            if any((
                args.expect_owner, args.expect_branch, args.expect_worktree_id, args.delete_branch, args.discard_direnv_cache,
                args.discard_generated_caches, args.discard_generated_build_outputs,
                args.discard_generated_artifacts, args.preserve_generated_artifacts,
                args.allow_unreferenced_reflog,
            )):
                raise RemovalError("quarantine purge mode cannot be combined with worktree-removal options")
            purge_preserved_quarantine(
                args.repo, args.purge_preserved_quarantine, dry_run=args.dry_run,
                lock_name=args.lock_name, discard_unverified_direnv=args.discard_unverified_direnv,
            )
            return 0
        if args.worktree is None or args.repo is not None:
            raise RemovalError("worktree removal requires a worktree path and does not accept --repo")
        if args.discard_unverified_direnv:
            raise RemovalError("--discard-unverified-direnv is only valid with --purge-preserved-quarantine")
        if args.expect_owner is not None:
            raise RemovalError("--expect-owner is obsolete; use an exact worktree selector; session ownership is read from the current client environment")
        if bool(args.expect_branch) == bool(args.expect_worktree_id):
            raise RemovalError("provide exactly one of --expect-branch or --expect-worktree-id")
        if args.expect_worktree_id and args.delete_branch:
            raise RemovalError("--delete-branch is only valid for a branch-backed legacy worktree")
        if args.discard_generated_artifacts and args.preserve_generated_artifacts:
            raise RemovalError("--discard-generated-artifacts cannot be combined with --preserve-generated-artifacts")
        if args.discard_generated_caches and args.preserve_generated_artifacts:
            raise RemovalError("--discard-generated-caches cannot be combined with --preserve-generated-artifacts")
        if args.dry_run:
            worktree, _ = locate(args.worktree)
            target = inspect(worktree)
            print(target.owner_line, file=sys.stderr)
            pending = unresolved_transaction(target)
            if pending is not None:
                raise RemovalError(f"an interrupted removal transaction needs inspection first: {pending}")
            plan = verify_safe(
                target, args.base, allow_unreferenced_reflog=args.allow_unreferenced_reflog,
                expect_branch=args.expect_branch, expect_worktree_id=args.expect_worktree_id,
                discard_direnv_cache=args.discard_direnv_cache,
                discard_generated_caches=args.discard_generated_caches,
                discard_generated_build_outputs=args.discard_generated_build_outputs,
                discard_generated_artifacts=args.discard_generated_artifacts,
                preserve_generated_artifacts=args.preserve_generated_artifacts,
            )
            kind = f"symlink -> {target.symlink_target}" if target.symlink_target else "gitfile"
            direnv_plan = ""
            if plan.direnv is not None:
                action = "discard after successful removal" if plan.discard_direnv_cache else "quarantine and retain"
                direnv_plan = f"; .direnv would be {action}"
            cache_plan = ""
            if plan.generated_caches:
                actions = []
                for preserve, label in ((True, "quarantined and retained"), (False, "discarded")):
                    names = ", ".join(
                        str(cache.path.relative_to(target.worktree))
                        for cache in plan.generated_caches if cache.preserve is preserve
                    )
                    if names:
                        actions.append(f"{label}: {names}")
                cache_plan = "; generated artifact paths would be " + "; ".join(actions)
            print(
                f"dry-run ok: {target.worktree} (.git is a {kind}; {target.branch_ref}) "
                f"would be removed{direnv_plan}{cache_plan}"
            )
            return 0
        outcome = remove(
            args.worktree, args.base, delete_branch_too=args.delete_branch,
            lock_name=args.lock_name, allow_unreferenced_reflog=args.allow_unreferenced_reflog,
            expect_branch=args.expect_branch, expect_worktree_id=args.expect_worktree_id,
            discard_direnv_cache=args.discard_direnv_cache,
            discard_generated_caches=args.discard_generated_caches,
            discard_generated_build_outputs=args.discard_generated_build_outputs,
            discard_generated_artifacts=args.discard_generated_artifacts,
            preserve_generated_artifacts=args.preserve_generated_artifacts,
        )
    except RemovalError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    target = outcome.target
    suffix = f" and {target.branch_ref}" if args.delete_branch and target.branch_ref else ""
    print(f"removed {target.worktree}{suffix}")
    if outcome.discarded_direnv:
        print("discarded verified Nix-direnv cache")
    elif outcome.preserved_direnv is not None:
        print(f"preserved .direnv at {outcome.preserved_direnv}")
    if outcome.discarded_generated_caches:
        print(f"discarded generated artifact paths: {', '.join(outcome.discarded_generated_caches)}")
    for artifact in outcome.preserved_generated_caches:
        print(f"preserved generated artifact quarantine at {artifact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
