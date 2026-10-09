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

A root `.direnv` path is moved to a private state quarantine so it does not block
Git removal. By default its contents are retained. `--discard-direnv-cache`
purges only the verified Nix-direnv `use flake` cache after successful worktree
removal; unknown layouts and unsafe purge conditions remain quarantined. The
flag discards all files in that recognized cache, including edits.

Residual risk: `git worktree remove` runs its own `git status`, which can start
the git-annex clean filter. If that turns `.git` back into a symlink, Git
refuses and the symlink is restored; nothing is deleted.
"""

from __future__ import annotations

import argparse
import ctypes
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

DEFAULT_LOCK_NAME = "main-integration.lock"
DIR_ENV_NAME = ".direnv"
NIX_STORE_ROOT = Path("/nix/store")
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
    uses_annex: bool
    symlink_target: str | None
    description: str | None

    @property
    def owner_line(self) -> str:
        if not self.description:
            return "owner: none (no branch description; legacy or detached worktree)"
        one_line = "".join(c if c.isprintable() else c.encode("unicode_escape").decode() for c in self.description)
        return f"owner: {one_line}"


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
class RemovalPlan:
    database_link: CanonicalDatabaseLink | None
    direnv: DirenvArtifact | None
    discard_direnv_cache: bool


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
    operation_id = secrets.token_hex(16)
    operation_dir = root / operation_id
    operation_dir.mkdir(mode=0o700)
    fsync_directory(root)
    worktree_info, admin_info = target.worktree.stat(), target.admin_dir.stat()
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
            "discard_requested": plan.discard_direnv_cache,
            "discardable": direnv.discardable,
            "discard_reason": direnv.discard_reason,
            "quarantine_path": str(operation_dir / DIR_ENV_NAME),
        },
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


def lsof_open_paths(paths: tuple[Path, ...]) -> set[str] | None:
    lsof = shutil.which("lsof")
    if lsof is None:
        return None
    existing = [str(path) for path in paths if os.path.lexists(path)]
    if not existing:
        return set()
    result = subprocess.run([lsof, "-Fpn", *existing], capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1) or result.stderr.strip():
        return None
    pids: set[str] = set()
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
    if branch_ref and branch_ref.startswith("refs/heads/"):
        description = run_git(worktree, "config", "--get", f"branch.{branch_ref.removeprefix('refs/heads/')}.description").stdout.strip() or None
    return Target(
        worktree, git_dir, common_dir, worktree_command_root(entries, worktree), registered_main_worktree(entries),
        branch_ref, uses_annex, symlink_target, description,
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


def verify_safe(
    target: Target, base: str, *, allow_unreferenced_reflog: bool, expect_owner: str | None = None,
    discard_direnv_cache: bool = False,
) -> RemovalPlan:
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
    status = status_entries(wt)
    db_link: CanonicalDatabaseLink | None = None
    direnv_status: list[tuple[bytes, bytes]] = []
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
    discard_cache = bool(discard_direnv_cache and direnv is not None and direnv.discardable)
    if discard_direnv_cache and direnv is not None and not direnv.discardable:
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
    return RemovalPlan(db_link, direnv, discard_cache)


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
    expect_owner: str | None = None, discard_direnv_cache: bool = False,
) -> RemovalOutcome:
    worktree, common_dir = locate(worktree_arg)
    with exclusive_lock(common_dir, lock_name):
        target = inspect(worktree)
        print(target.owner_line, file=sys.stderr)
        pending = unresolved_transaction(target)
        if pending is not None:
            raise RemovalError(f"an interrupted removal transaction needs inspection first: {pending}")
        if target.uses_annex:
            result = run_git(worktree, "annex", "restage")
            if result.returncode != 0:
                raise RemovalError(f"git annex restage failed: {result.stderr.strip()}")
            target = inspect(worktree)
        plan = verify_safe(
            target, base, allow_unreferenced_reflog=allow_unreferenced_reflog, expect_owner=expect_owner,
            discard_direnv_cache=discard_direnv_cache,
        )
        base_oid = resolve_base(target, base)
        head = git_out(worktree, "rev-parse", "HEAD")
        transaction = create_transaction(target, head, plan) if plan.database_link or plan.direnv else None
        direnv_moved = False
        db_link_removed = False
        git_removed = False
        try:
            if plan.direnv is not None and transaction is not None:
                transact_direnv_move(transaction, plan.direnv)
                direnv_moved = True
            if target.symlink_target is not None:
                if check_dotgit(worktree, target.admin_dir) != target.symlink_target:
                    raise RemovalError(".git changed since inspection")
                replace_dotgit(worktree, gitfile=target.admin_dir)
                if transaction is not None:
                    write_manifest(transaction, "dotgit_normalized")
            if check_dotgit(worktree, target.admin_dir) is not None:
                raise RemovalError(".git became a symlink again before removal")
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
                if check_dotgit(worktree, target.admin_dir) is not None:
                    raise RemovalError(".git became a symlink again before removal")
            elif status_entries(worktree):
                raise RemovalError(
                    "worktree changed after removing generated state:\n  "
                    + show_status_entries(status_entries(worktree))
                )
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
            dotgit_ok = rollback(target, target.symlink_target, cause) if intact else False
            db_ok = True
            if db_link_removed and plan.database_link is not None and intact:
                db_ok = restore_database_symlink(target, plan.database_link)
            direnv_ok = True
            if direnv_moved and plan.direnv is not None and intact and transaction is not None:
                direnv_ok = restore_direnv(transaction, plan.direnv)
            elif direnv_moved:
                direnv_ok = False
            rollback_ok = intact and dotgit_ok and db_ok and direnv_ok
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
        if transaction is not None and plan.direnv is not None:
            archive = Path(str(transaction.manifest["direnv"]["quarantine_path"]))  # type: ignore[index]
            if plan.discard_direnv_cache:
                write_manifest(transaction, "cache_purge_started")
                reason = purge_direnv_cache(archive, plan.direnv.signature)
                if reason is None:
                    discarded_direnv = True
                    try:
                        write_manifest(transaction, "cache_purged")
                        transaction_cleanup(transaction)
                    except (OSError, RemovalError) as error:
                        try:
                            write_manifest(transaction, "recovery_required")
                        except (OSError, RemovalError):
                            pass
                        print(
                            f"warning: cache was discarded but transaction metadata remains at "
                            f"{transaction.operation_dir}: {error}",
                            file=sys.stderr,
                        )
                else:
                    preserved_direnv = archive
                    transaction.manifest["preserve_reason"] = reason
                    try:
                        write_manifest(transaction, "completed_preserved")
                    except (OSError, RemovalError) as error:
                        print(f"warning: could not update quarantine manifest {transaction.manifest_path}: {error}", file=sys.stderr)
                    print(f"warning: {reason}; preserved at {archive}", file=sys.stderr)
            else:
                preserved_direnv = archive
                try:
                    write_manifest(transaction, "completed_preserved")
                except (OSError, RemovalError) as error:
                    print(f"warning: could not update quarantine manifest {transaction.manifest_path}: {error}", file=sys.stderr)
        elif transaction is not None:
            try:
                write_manifest(transaction, "worktree_removed")
                transaction_cleanup(transaction)
            except (OSError, RemovalError) as error:
                try:
                    write_manifest(transaction, "recovery_required")
                except (OSError, RemovalError):
                    pass
                print(f"warning: worktree removed but transaction metadata remains: {error}", file=sys.stderr)
        if delete_branch_too:
            delete_branch(target, head, base_oid)
    return RemovalOutcome(target, preserved_direnv, discarded_direnv)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely remove a linked Git worktree (git-annex aware).")
    parser.add_argument("worktree", help="path of the linked worktree to remove")
    parser.add_argument("--base", default="main", help="ref that must already contain HEAD (default: main)")
    parser.add_argument("--delete-branch", action="store_true", help="also delete the worktree's branch when it is fully contained in --base")
    parser.add_argument("--allow-unreferenced-reflog", action="store_true", help="accept commits that only this worktree's HEAD reflog references")
    parser.add_argument("--expect-owner", metavar="TEXT", help="refuse unless the branch description contains TEXT (use the task text you recorded)")
    parser.add_argument(
        "--discard-direnv-cache", action="store_true",
        help="discard a verified Nix-direnv use-flake cache after successful removal (including edits in the cache)",
    )
    parser.add_argument("--dry-run", action="store_true", help="run the checks without the lock or restage; change nothing")
    parser.add_argument("--lock-name", default=DEFAULT_LOCK_NAME, help="lock directory created under the common git dir")
    args = parser.parse_args(argv)
    try:
        if args.dry_run:
            worktree, _ = locate(args.worktree)
            target = inspect(worktree)
            print(target.owner_line, file=sys.stderr)
            pending = unresolved_transaction(target)
            if pending is not None:
                raise RemovalError(f"an interrupted removal transaction needs inspection first: {pending}")
            plan = verify_safe(
                target, args.base, allow_unreferenced_reflog=args.allow_unreferenced_reflog,
                expect_owner=args.expect_owner, discard_direnv_cache=args.discard_direnv_cache,
            )
            kind = f"symlink -> {target.symlink_target}" if target.symlink_target else "gitfile"
            direnv_plan = ""
            if plan.direnv is not None:
                action = "discard after successful removal" if plan.discard_direnv_cache else "quarantine and retain"
                direnv_plan = f"; .direnv would be {action}"
            print(f"dry-run ok: {target.worktree} (.git is a {kind}; {target.branch_ref}) would be removed{direnv_plan}")
            return 0
        outcome = remove(
            args.worktree, args.base, delete_branch_too=args.delete_branch,
            lock_name=args.lock_name, allow_unreferenced_reflog=args.allow_unreferenced_reflog,
            expect_owner=args.expect_owner, discard_direnv_cache=args.discard_direnv_cache,
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
