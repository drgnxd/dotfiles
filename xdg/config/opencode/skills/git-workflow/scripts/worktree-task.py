#!/usr/bin/env python3
"""Coordinate owned worktrees from creation through integration and cleanup.

This composes the existing create, audit, and safe-remove helpers. It never
approves environments, configures project databases, builds project toolchains,
resolves conflicts, rewrites history, or pushes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worktree_meta as meta

HERE = Path(__file__).resolve().parent
CREATE_HELPER = HERE / "worktree-create.py"
AUDIT_HELPER = HERE / "worktree-audit.py"
REMOVE_HELPER = HERE / "safe-worktree-remove.py"
LOCK_NAME = "main-integration.lock"
MAIN_BRANCH = "main"


class TaskError(RuntimeError):
    def __init__(self, status: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.status = status
        self.details = details


def load_helper(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise TaskError("tool-error", f"cannot load helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def integration_lock(remove_module, common: Path):
    try:
        with remove_module.exclusive_lock(common, LOCK_NAME):
            yield
    except remove_module.RemovalError as error:
        raise TaskError("integration-lock-failed", str(error)) from error


def git_bytes(cwd: Path, *args: str, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=cwd, env=meta.git_env(), input=input_bytes, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise TaskError("git-command-failed", result.stderr.decode("utf-8", "replace").strip(), args=list(args), cwd=str(cwd))
    return result


def repo_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    result = meta.git(path, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise TaskError("invalid-repo", f"not a Git worktree: {path}")
    return Path(result.stdout.strip()).resolve()


def common_dir(repo: Path) -> Path:
    return Path(meta.git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()).resolve()


def worktree_entries(repo: Path) -> list[dict[str, str]]:
    output = meta.git(repo, "worktree", "list", "--porcelain").stdout
    result: list[dict[str, str]] = []
    for block in output.strip().split("\n\n"):
        item: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            item[key] = value
        if "worktree" in item:
            result.append(item)
    return result


def worktree_for_branch(repo: Path, branch: str) -> Path:
    matches = [Path(row["worktree"]).resolve() for row in worktree_entries(repo) if row.get("branch") == f"refs/heads/{branch}"]
    if len(matches) != 1:
        raise TaskError("worktree-not-unique", f"expected one registered worktree for {branch}", matches=[str(path) for path in matches])
    return matches[0]


def branch_oid(repo: Path, branch: str) -> str:
    result = meta.git(repo, "rev-parse", "--verify", f"refs/heads/{branch}", check=False)
    if result.returncode != 0:
        raise TaskError("branch-missing", f"local branch does not exist: {branch}")
    return result.stdout.strip()


def main_worktree(repo: Path) -> Path:
    for row in worktree_entries(repo):
        if row.get("branch") == f"refs/heads/{MAIN_BRANCH}":
            return Path(row["worktree"]).resolve()
    raise TaskError("main-worktree-missing", "no registered worktree has main checked out")


def current_owner(client: str | None = None) -> tuple[str, str]:
    owner = meta.current_session_identity()
    if owner is None:
        raise TaskError("session-unavailable", "one valid current client/session identity is required")
    if client is not None and owner[0] != client:
        raise TaskError("session-mismatch", f"current session belongs to {owner[0]}, not {client}")
    return owner


def branch_metadata(repo: Path, branch: str) -> tuple[str, str, str, str]:
    text = meta.git(repo, "config", "--get", f"branch.{branch}.description", check=False).stdout.strip()
    parsed = meta.parse_owner_description(text)
    if parsed is None:
        raise TaskError("owner-unknown", f"branch owner metadata is missing or invalid: {branch}")
    task, client, session = parsed
    _, trailer = meta.parse_description(text)
    base = trailer.get("base", "")
    if not meta.OID_RE.fullmatch(base):
        raise TaskError("invalid-base", f"branch has an invalid recorded base OID: {branch}")
    return task, client, session, base


def require_owned_branch(repo: Path, branch: str) -> tuple[Path, str, str]:
    owner = current_owner()
    worktree = worktree_for_branch(repo, branch)
    _, client, session, base = branch_metadata(repo, branch)
    if (client, session) != owner:
        raise TaskError("foreign-owner", f"branch belongs to {client}/{session}, not the current session")
    root = Path(meta.git(worktree, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if root != worktree:
        raise TaskError("worktree-identity", f"registered worktree root mismatch: {root}")
    creator = load_helper("worktree_create", CREATE_HELPER)
    problem = creator.verify_identity(worktree, common_dir(repo))
    if problem:
        raise TaskError("worktree-identity", problem)
    return worktree, base, meta.git(worktree, "rev-parse", "HEAD").stdout.strip()


def status_records(repo: Path) -> list[tuple[str, str]]:
    result = git_bytes(repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching", "-z")
    fields = result.stdout.split(b"\0")
    records: list[tuple[str, str]] = []
    index = 0
    while index < len(fields) - 1:
        raw = fields[index]
        index += 1
        if not raw:
            continue
        if len(raw) < 4 or raw[2:3] != b" ":
            raise TaskError("status-unreadable", "git status returned malformed porcelain data")
        try:
            code, path = raw[:2].decode("ascii"), raw[3:].decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise TaskError("path-unreadable", "a worktree path is not valid UTF-8") from error
        records.append((code, path.rstrip("/")))
        if b"R" in raw[:2] or b"C" in raw[:2]:
            index += 1
    return records


def require_clean(repo: Path, label: str) -> None:
    dirty = [(code, path) for code, path in status_records(repo) if code != "!!"]
    if dirty:
        raise TaskError("dirty-worktree", f"{label} has tracked or untracked changes", paths=[f"{code} {path}" for code, path in dirty])


def require_no_index_flags(repo: Path, label: str) -> None:
    output = git_bytes(repo, "ls-files", "-v", "-z").stdout
    flagged = []
    for record in output.split(b"\0"):
        if record and (chr(record[0]) == "S" or chr(record[0]).islower()):
            try:
                flagged.append(record[2:].decode("utf-8", "strict"))
            except UnicodeDecodeError as error:
                raise TaskError("path-unreadable", "an index path is not valid UTF-8") from error
    if flagged:
        raise TaskError("index-flags", f"{label} has assume-unchanged or skip-worktree entries", paths=flagged)


def ancestor(repo: Path, older: str, newer: str) -> bool:
    return meta.git(repo, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def require_no_replace_refs(repo: Path) -> None:
    refs = meta.git(repo, "for-each-ref", "--format=%(refname)", "refs/replace").stdout.splitlines()
    if refs:
        raise TaskError("replace-refs", "refs/replace is present; object identity cannot be checked safely", refs=refs)


def tree_entries(repo: Path, oid: str) -> dict[str, tuple[str, str]]:
    result = git_bytes(repo, "ls-tree", "-r", "-z", oid)
    paths: dict[str, tuple[str, str]] = {}
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, separator, raw_path = record.partition(b"\t")
        if not separator:
            raise TaskError("tree-read-failed", "git ls-tree returned malformed output")
        try:
            fields = metadata.split(b" ")
            if len(fields) != 3:
                raise TaskError("tree-read-failed", "git ls-tree returned malformed entry metadata")
            mode, object_oid = fields[0].decode("ascii"), fields[2].decode("ascii")
            path = raw_path.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            raise TaskError("path-unreadable", "a tracked Git path is not valid UTF-8") from error
        paths[path] = (mode, object_oid)
    return paths


def tree_modes(repo: Path, oid: str) -> dict[str, str]:
    return {path: mode for path, (mode, _) in tree_entries(repo, oid).items()}


def path_key(path: str) -> tuple[str, ...]:
    parts = path.split("/")
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise TaskError("path-unrepresentable", f"invalid Git path: {path!r}")
    if any(part.endswith((".", " ")) for part in parts):
        raise TaskError("path-unrepresentable", f"path has a trailing dot/space: {path!r}")
    if any(unicodedata.normalize("NFD", part).casefold() == ".git" for part in parts):
        raise TaskError("path-unrepresentable", f"path aliases Git metadata: {path!r}")
    return tuple(unicodedata.normalize("NFD", part).casefold() for part in parts)


def prefixes(key: tuple[str, ...]) -> list[tuple[str, ...]]:
    return [key[:depth] for depth in range(1, len(key) + 1)]


def check_tree_paths(repo: Path, current_oid: str, final_oid: str) -> list[str]:
    current, final = tree_modes(repo, current_oid), tree_modes(repo, final_oid)
    extras = [(code, path) for code, path in status_records(repo) if code in ("??", "!!")]
    issues: set[str] = set()
    final_keys: dict[tuple[str, ...], str] = {}
    final_directory_spellings: dict[tuple[str, ...], tuple[str, ...]] = {}
    for path in final:
        parts = tuple(path.split("/"))
        key = path_key(path)
        previous = final_keys.setdefault(key, path)
        if previous != path:
            issues.add(f"final-tree case/Unicode alias: {previous!r} and {path!r}")
        for depth in range(1, len(parts)):
            prefix_key, spelling = key[:depth], parts[:depth]
            old_spelling = final_directory_spellings.setdefault(prefix_key, spelling)
            if old_spelling != spelling:
                issues.add(f"final-tree directory alias: {'/'.join(old_spelling)!r} and {'/'.join(spelling)!r}")
        for depth in range(1, len(key)):
            if key[:depth] in final_keys:
                issues.add(f"final-tree file/directory alias: {final_keys[key[:depth]]!r} and {path!r}")
    for key, path in final_keys.items():
        for depth in range(1, len(key)):
            if key[:depth] in final_keys:
                issues.add(f"final-tree file/directory alias: {final_keys[key[:depth]]!r} and {path!r}")

    existing: dict[tuple[str, ...], list[tuple[str, str, str]]] = {}
    existing_directory_spellings: dict[tuple[str, ...], tuple[str, ...]] = {}
    for path, mode in current.items():
        parts = tuple(path.split("/"))
        key = path_key(path)
        existing.setdefault(key, []).append((path, mode, "tracked"))
        for depth in range(1, len(parts)):
            prefix_key, spelling = key[:depth], parts[:depth]
            previous = existing_directory_spellings.setdefault(prefix_key, spelling)
            if previous != spelling:
                existing_directory_spellings[prefix_key] = ("<ambiguous>",)
    for code, path in extras:
        key = path_key(path)
        existing.setdefault(key, []).append((path, "", code))
        parts = tuple(path.split("/"))
        for depth in range(1, len(parts)):
            prefix_key, spelling = key[:depth], parts[:depth]
            previous = existing_directory_spellings.setdefault(prefix_key, spelling)
            if previous != spelling:
                existing_directory_spellings[prefix_key] = ("<ambiguous>",)

    extra_descendants: dict[tuple[str, ...], list[str]] = {}
    for code, path in extras:
        key = path_key(path)
        for prefix in prefixes(key):
            extra_descendants.setdefault(prefix, []).append(path)

    for path, mode in final.items():
        key = path_key(path)
        for depth in range(1, len(key)):
            prefix = key[:depth]
            spelling = tuple(path.split("/")[:depth])
            existing_spelling = existing_directory_spellings.get(prefix)
            if prefix in existing_directory_spellings and existing_spelling != spelling:
                issues.add(f"main/final directory spelling collision: {'/'.join(existing_spelling)!r} and {'/'.join(spelling)!r}")
            for existing_path, existing_mode, status in existing.get(prefix, []):
                if existing_mode == "120000" or status in ("??", "!!") or existing_mode not in ("040000", ""):
                    issues.add(f"main file/symlink blocks final descendant: {existing_path!r} -> {path!r}")

        same = existing.get(key, [])
        for existing_path, existing_mode, status in same:
            if existing_path != path:
                issues.add(f"main path aliases final path: {existing_path!r} and {path!r}")
            elif status in ("??", "!!"):
                issues.add(f"final path would overwrite {status} data: {path!r}")
            elif existing_mode == "120000" and mode != "120000":
                issues.add(f"final tree replaces a tracked symlink: {path!r}")
        descendants = extra_descendants.get(key, [])
        if descendants and any(path_key(item) != key for item in descendants):
            issues.add(f"final file would replace ignored/untracked descendants: {path!r} -> {descendants}")

        cursor = repo
        for part in path.split("/")[:-1]:
            cursor = cursor / part
            if cursor.is_symlink():
                issues.add(f"final path traverses a main-worktree symlink: {path!r} via {cursor.relative_to(repo)!s}")
                break

    if issues:
        raise TaskError("path-collision", "final tree conflicts with main or ignored/untracked paths", collisions=sorted(issues))
    return changed_paths(repo, current_oid, final_oid)


def changed_paths(repo: Path, base: str, tip: str) -> list[str]:
    result = git_bytes(repo, "diff", "--name-only", "-z", base, tip)
    try:
        return [entry.decode("utf-8", "strict") for entry in result.stdout.split(b"\0") if entry]
    except UnicodeDecodeError as error:
        raise TaskError("path-unreadable", "a changed path is not valid UTF-8") from error


def require_no_gitlinks(repo: Path, base: str, tip: str) -> None:
    before, after = tree_entries(repo, base), tree_entries(repo, tip)
    for path in set(before) | set(after):
        old, new = before.get(path), after.get(path)
        if old != new and ((old and old[0] == "160000") or (new and new[0] == "160000")):
            raise TaskError("submodule-change", f"submodule gitlink changes require a separate task: {path}")


ANNEX_FILTER_COMMANDS = {
    "filter.annex.clean": "git-annex smudge --clean -- %f",
    "filter.annex.smudge": "git-annex smudge -- %f",
    "filter.annex.process": "git-annex filter-process",
}


def require_annex_filter(repo: Path) -> None:
    mismatches = []
    for name, expected in ANNEX_FILTER_COMMANDS.items():
        result = meta.git(repo, "config", "--get", name, check=False)
        actual = result.stdout.strip() if result.returncode == 0 else ""
        if actual != expected:
            mismatches.append(f"{name}={actual or '<unset>'}")
    if mismatches:
        raise TaskError("filters-present", "git-annex filter commands do not match the reviewed local configuration", filters=mismatches)
    version = meta.git(repo, "annex", "version", check=False)
    if version.returncode != 0:
        raise TaskError("filters-present", "git-annex is unavailable; run the lifecycle helper in its Nix dev shell")


def require_no_filters(repo: Path, paths: list[str], *, allow_annex_filter: bool = False) -> None:
    if not paths:
        return
    payload = b"\0".join(path.encode("utf-8") for path in paths) + b"\0"
    result = git_bytes(repo, "check-attr", "-z", "filter", "--stdin", check=False, input_bytes=payload)
    if result.returncode != 0:
        raise TaskError("filter-check-failed", result.stderr.decode("utf-8", "replace").strip())
    fields = result.stdout.split(b"\0")
    if fields and not fields[-1]:
        fields.pop()
    if len(fields) % 3:
        raise TaskError("filter-check-failed", "git check-attr returned malformed output")
    active = []
    annex = []
    for index in range(0, len(fields), 3):
        path, _, value = fields[index:index + 3]
        if value not in (b"unspecified", b"unset"):
            entry = f"{path.decode('utf-8', 'replace')}:filter={value.decode('utf-8', 'replace')}"
            (annex if value == b"annex" else active).append(entry)
    if active:
        raise TaskError("filters-present", "changed paths use Git filters that need manual review", paths=active)
    if annex:
        if not allow_annex_filter:
            raise TaskError("filters-present", "git-annex filters require explicit --allow-annex-filter", paths=annex)
        require_annex_filter(repo)


def require_no_hooks(repo: Path, *, merge_commit: bool, allow_repository_hooks: bool = False) -> None:
    relevant = {"post-merge", "reference-transaction"}
    if merge_commit:
        relevant.update({"pre-merge-commit", "pre-commit", "prepare-commit-msg", "commit-msg"})
    blocked = set(meta.executable_hooks(repo, relevant))
    if allow_repository_hooks:
        blocked.discard("post-merge")
        if merge_commit:
            blocked.difference_update({"pre-merge-commit", "pre-commit", "prepare-commit-msg", "commit-msg"})
    if blocked:
        detail = (
            "reference-transaction hooks are never run during task integration"
            if "reference-transaction" in blocked
            else "inspect repository hooks, then pass --allow-repository-hooks to run them normally"
        )
        raise TaskError("hooks-present", detail, hooks=sorted(blocked))
    if merge_commit and meta.git(repo, "config", "--bool", "--get", "commit.gpgsign", check=False).stdout.strip().lower() == "true":
        raise TaskError("commit-signing", "integration merge may require interactive signing; use the manual procedure")


def create_worktree(
    repo: Path, *, slug: str, client: str, task: str, source: str, parent: str | None, prefix: str,
    worktrees_root: str | None = None, allow_repository_hooks: bool = False,
) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(CREATE_HELPER), "--repo", str(repo), "--slug", slug, "--client", client, "--task", task, "--from", source, "--prefix", prefix]
    if parent:
        argv.extend(("--parent", parent))
    if worktrees_root:
        argv.extend(("--worktrees-root", worktrees_root))
    if allow_repository_hooks:
        argv.append("--allow-repository-hooks")
    return subprocess.run(argv, cwd=repo, text=True, capture_output=True, check=False)


def parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key] = value
    return values


def inspect_creation(repo: Path, output: str) -> dict[str, Any]:
    values = parse_key_values(output)
    path, branch = values.get("worktree"), values.get("branch")
    return {
        "created_worktree": path,
        "created_branch": branch,
        "worktree_registered": bool(path and any(Path(row["worktree"]).resolve() == Path(path).resolve() for row in worktree_entries(repo))),
        "branch_exists": bool(branch and meta.git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0),
    }


def emit(status: str, json_output: bool = False, **fields: Any) -> int:
    record = {"status": status, **fields}
    if json_output:
        print(json.dumps(record, ensure_ascii=False, indent=2))
    else:
        for key, value in record.items():
            print(f"{key}={json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}")
    return 0


def emit_error(error: TaskError, json_output: bool = False) -> int:
    emit(error.status, json_output, error=str(error), **error.details)
    return 1


def start(args: argparse.Namespace) -> int:
    repo = repo_root(args.repo)
    owner = current_owner(args.client)
    result = create_worktree(
        repo, slug=args.slug, client=args.client, task=args.task, source=args.source,
        parent=args.parent, prefix=args.prefix, worktrees_root=args.worktrees_root,
        allow_repository_hooks=args.allow_repository_hooks,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode == 0:
        emit("created", args.json, repo=str(repo), client=owner[0], session=owner[1], **parse_key_values(result.stdout))
    else:
        state = "partial-creation" if result.returncode in (3, 4) else "creation-failed"
        emit(state, args.json, repo=str(repo), helper_exit=result.returncode, helper_output=result.stdout, **inspect_creation(repo, result.stdout + result.stderr))
    return result.returncode


def status(args: argparse.Namespace) -> int:
    repo = repo_root(args.repo)
    command = [sys.executable, str(AUDIT_HELPER), "--repo", str(repo), "--base", args.base]
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=repo, check=False).returncode


def main_state(repo: Path) -> tuple[Path, str]:
    require_no_replace_refs(repo)
    main = main_worktree(repo)
    current = meta.git(main, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).stdout.strip()
    if current != MAIN_BRANCH:
        raise TaskError("main-not-checked-out", f"main worktree is on {current or 'detached HEAD'}")
    head, live = meta.git(main, "rev-parse", "HEAD").stdout.strip(), branch_oid(repo, MAIN_BRANCH)
    if head != live:
        raise TaskError("main-ref-mismatch", f"main HEAD {head} != live main ref {live}")
    require_clean(main, "main worktree")
    require_no_index_flags(main, "main worktree")
    return main, head


def preflight(
    repo: Path, main: Path, task_wt: Path, base: str, final_oid: str, *, allow_repository_hooks: bool,
    allow_annex_filter: bool, check_final_paths: bool = True,
) -> list[str]:
    require_clean(main, "main worktree")
    require_clean(task_wt, "task/integration worktree")
    require_no_index_flags(main, "main worktree")
    require_no_index_flags(task_wt, "task/integration worktree")
    require_no_replace_refs(repo)
    require_no_gitlinks(repo, base, final_oid)
    paths = changed_paths(repo, base, final_oid)
    require_no_hooks(main, merge_commit=False, allow_repository_hooks=allow_repository_hooks)
    require_no_filters(main, paths, allow_annex_filter=allow_annex_filter)
    require_no_filters(task_wt, paths, allow_annex_filter=allow_annex_filter)
    if check_final_paths:
        check_tree_paths(main, base, final_oid)
    return paths


def inspect_main_state(repo: Path) -> dict[str, Any]:
    try:
        main = main_worktree(repo)
        head = meta.git(main, "rev-parse", "HEAD", check=False).stdout.strip()
        live = meta.git(repo, "rev-parse", "refs/heads/main", check=False).stdout.strip()
        records = status_records(main)
        return {"main_worktree": str(main), "head": head, "main_ref": live, "status": [f"{code} {path}" for code, path in records]}
    except (TaskError, OSError, subprocess.SubprocessError) as error:
        return {"inspection_error": str(error)}


def postcheck(repo: Path, main: Path, expected: str, task_branch: str, task_tip: str, integration_branch: str | None, integration_tip: str) -> dict[str, Any]:
    actual, live = meta.git(main, "rev-parse", "HEAD").stdout.strip(), branch_oid(repo, MAIN_BRANCH)
    status_rows = [(code, path) for code, path in status_records(main) if code != "!!"]
    failures = []
    if actual != expected:
        failures.append(f"HEAD {actual} != expected {expected}")
    if live != expected:
        failures.append(f"refs/heads/main {live} != expected {expected}")
    if status_rows:
        failures.append("main worktree status is not empty")
    if not ancestor(repo, task_tip, actual):
        failures.append("task tip is not reachable from main")
    if not ancestor(repo, integration_tip, actual):
        failures.append("integration tip is not reachable from main")
    if branch_oid(repo, task_branch) != task_tip:
        failures.append("task branch tip changed during integration")
    if integration_branch and branch_oid(repo, integration_branch) != integration_tip:
        failures.append("integration branch tip changed during integration")
    expected_tree = meta.git(repo, "rev-parse", f"{expected}^{{tree}}").stdout.strip()
    actual_tree = meta.git(repo, "rev-parse", f"{actual}^{{tree}}").stdout.strip()
    if expected_tree != actual_tree:
        failures.append(f"tree {actual_tree} != expected tree {expected_tree}")
    return {"ok": not failures, "failures": failures, "head": actual, "main_ref": live, "expected": expected, "status": [f"{code} {path}" for code, path in status_rows]}


def creator_partial(repo: Path, result: subprocess.CompletedProcess[str], stage: str) -> TaskError:
    state = inspect_creation(repo, result.stdout + "\n" + result.stderr)
    return TaskError(f"{stage}-worktree-create-partial", f"creator exited {result.returncode}; merge/update/cleanup stopped", helper_exit=result.returncode, helper_output=result.stdout + result.stderr, **state)


def cleanup_state(repo: Path, worktree: Path, branch: str) -> dict[str, Any]:
    registered = any(Path(row["worktree"]).resolve() == worktree.resolve() for row in worktree_entries(repo))
    ref = meta.git(repo, "show-ref", "--verify", "--hash", f"refs/heads/{branch}", check=False)
    return {"worktree_registered": registered, "worktree_path_exists": worktree.exists(), "branch_exists": ref.returncode == 0, "branch_oid": ref.stdout.strip() if ref.returncode == 0 else None}


def safe_remove(repo: Path, worktree: Path, branch: str, args: argparse.Namespace, delete_branch: bool) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(REMOVE_HELPER), str(worktree), "--expect-branch", branch, "--base", MAIN_BRANCH]
    if delete_branch:
        command.append("--delete-branch")
    for name in (
        "discard_direnv_cache", "discard_generated_caches", "discard_generated_build_outputs",
        "preserve_generated_artifacts",
    ):
        if getattr(args, name, False):
            command.append("--" + name.replace("_", "-"))
    return subprocess.run(command, cwd=repo, env=meta.git_env(), text=True, capture_output=True, check=False)


def finish(args: argparse.Namespace) -> int:
    if not args.external_writers_quiesced:
        raise TaskError("external-writers-not-confirmed", "inspect repo-specific scheduled/non-cooperating writers; pass --external-writers-quiesced only while they remain stopped through all cleanup")
    repo = repo_root(args.repo)
    owner = current_owner()
    task_wt, task_base, task_tip = require_owned_branch(repo, args.branch)
    if not ancestor(repo, task_base, task_tip):
        raise TaskError("invalid-task-history", "recorded task base is not an ancestor of task tip")

    remover = load_helper("safe_worktree_remove", REMOVE_HELPER)
    common = common_dir(repo)
    integration_wt: Path | None = None
    integration_branch: str | None = None
    plan = ""
    integration_tip = ""
    with integration_lock(remover, common):
        lock_token = (common / LOCK_NAME / "owner").read_text(encoding="utf-8").splitlines()[0]
        main, main_tip = main_state(repo)
        task_wt, current_base, current_task_tip = require_owned_branch(repo, args.branch)
        if current_base != task_base or current_task_tip != task_tip:
            raise TaskError("task-ref-changed", "task metadata/ref changed during preflight")

        if main_tip == task_base:
            plan = "direct-fast-forward"
            direct_paths = preflight(
                repo, main, task_wt, task_base, task_tip,
                allow_repository_hooks=args.allow_repository_hooks,
                allow_annex_filter=args.allow_annex_filter,
            )
            if main_state(repo)[1] != main_tip or branch_oid(repo, args.branch) != task_tip:
                raise TaskError("pre-merge-race", "main/task ref changed before fast-forward")
            if (common / LOCK_NAME / "owner").read_text(encoding="utf-8").splitlines()[0] != lock_token:
                raise TaskError("lock-owner-changed", "integration lock ownership changed")
            require_no_hooks(main, merge_commit=False, allow_repository_hooks=args.allow_repository_hooks)
            require_no_filters(main, direct_paths, allow_annex_filter=args.allow_annex_filter)
            update = meta.git(main, "merge", "--ff-only", "--no-overwrite-ignore", task_tip, check=False)
            integration_tip = task_tip
            if update.returncode != 0:
                raise TaskError("integration-verification-failed", "main update command failed; actual main state inspected and no cleanup attempted", expected=task_tip, **inspect_main_state(repo), stderr=update.stderr.strip())
            expected_main = task_tip
        elif ancestor(repo, task_tip, main_tip):
            plan = "already-integrated"
            integration_tip = task_tip
            expected_main = main_tip
        elif ancestor(repo, task_base, main_tip):
            plan = "integration-worktree-merge"
            preflight(
                repo, main, task_wt, task_base, task_tip,
                allow_repository_hooks=args.allow_repository_hooks,
                allow_annex_filter=args.allow_annex_filter,
                check_final_paths=False,
            )
            if main_state(repo)[1] != main_tip or branch_oid(repo, args.branch) != task_tip:
                raise TaskError("pre-merge-race", "main/task ref changed before creating integration worktree")
            if (common / LOCK_NAME / "owner").read_text(encoding="utf-8").splitlines()[0] != lock_token:
                raise TaskError("lock-owner-changed", "integration lock ownership changed")

            created = create_worktree(
                repo, slug="integration-merge", client=owner[0], task=f"Integrate {args.branch}",
                source=MAIN_BRANCH, parent=args.branch, prefix="integration",
                allow_repository_hooks=args.allow_repository_hooks,
            )
            if created.returncode != 0:
                raise creator_partial(repo, created, "integration")
            values = parse_key_values(created.stdout)
            if "worktree" not in values or "branch" not in values:
                raise TaskError("integration-worktree-create-partial", "creator succeeded without reporting its worktree and branch", helper_output=created.stdout)
            integration_wt, integration_branch = Path(values["worktree"]).resolve(), values["branch"]
            identity_problem = load_helper("worktree_create", CREATE_HELPER).verify_identity(integration_wt, common)
            if identity_problem:
                raise TaskError("integration-worktree-identity", identity_problem, integration_worktree=str(integration_wt), integration_branch=integration_branch)
            _, int_client, int_session, int_base = branch_metadata(repo, integration_branch)
            if (int_client, int_session) != owner or int_base != main_tip:
                raise TaskError("integration-owner-invalid", "integration branch owner/base metadata mismatch", integration_branch=integration_branch)
            require_no_hooks(main, merge_commit=True, allow_repository_hooks=args.allow_repository_hooks)
            require_no_filters(main, changed_paths(repo, task_base, task_tip), allow_annex_filter=args.allow_annex_filter)
            require_no_hooks(integration_wt, merge_commit=True, allow_repository_hooks=args.allow_repository_hooks)
            merge = meta.git(
                integration_wt, "merge", "--no-edit", "--no-ff", "--no-overwrite-ignore",
                "-m", args.integration_message, task_tip, check=False,
            )
            if merge.returncode != 0:
                raise TaskError("integration-conflict", "integration merge failed; task and integration worktrees are preserved", integration_worktree=str(integration_wt), integration_branch=integration_branch, stderr=merge.stderr.strip())

            integration_tip = meta.git(integration_wt, "rev-parse", "HEAD").stdout.strip()
            if branch_oid(repo, integration_branch) != integration_tip or not ancestor(repo, main_tip, integration_tip) or not ancestor(repo, task_tip, integration_tip):
                raise TaskError("integration-tree-invalid", "integration tip does not preserve both verified parents", integration_tip=integration_tip)
            require_clean(integration_wt, "integration worktree")
            require_no_index_flags(integration_wt, "integration worktree")
            require_no_gitlinks(repo, main_tip, integration_tip)
            final_paths = changed_paths(repo, main_tip, integration_tip)
            require_no_hooks(integration_wt, merge_commit=False, allow_repository_hooks=args.allow_repository_hooks)
            require_no_filters(integration_wt, final_paths, allow_annex_filter=args.allow_annex_filter)
            require_no_hooks(main, merge_commit=False, allow_repository_hooks=args.allow_repository_hooks)
            require_no_filters(main, final_paths, allow_annex_filter=args.allow_annex_filter)
            check_tree_paths(main, main_tip, integration_tip)
            if main_state(repo)[1] != main_tip or branch_oid(repo, args.branch) != task_tip or branch_oid(repo, integration_branch) != integration_tip:
                raise TaskError("pre-merge-race", "main/task/integration ref or status changed before final fast-forward")
            if (common / LOCK_NAME / "owner").read_text(encoding="utf-8").splitlines()[0] != lock_token:
                raise TaskError("lock-owner-changed", "integration lock ownership changed")
            update = meta.git(main, "merge", "--ff-only", "--no-overwrite-ignore", integration_tip, check=False)
            expected_main = integration_tip
            if update.returncode != 0:
                raise TaskError("integration-verification-failed", "main fast-forward failed; actual state inspected and no cleanup attempted", expected=integration_tip, **inspect_main_state(repo), stderr=update.stderr.strip(), integration_worktree=str(integration_wt), integration_branch=integration_branch)
        else:
            raise TaskError("histories-diverged", "no verified common base between task and current main; no refs changed", task_base=task_base, main_tip=main_tip, task_tip=task_tip)

        try:
            checked = postcheck(repo, main, expected_main, args.branch, task_tip, integration_branch, integration_tip)
        except Exception as error:
            raise TaskError("integration-verification-failed", "post-check raised after main update; all worktrees preserved", expected=expected_main, **inspect_main_state(repo), detail=str(error)) from error
        if not checked["ok"]:
            raise TaskError("integration-verification-failed", "main post-check failed; no rollback or cleanup attempted", **checked)

    if args.keep_worktree:
        return emit("integrated-kept", args.json, repo=str(repo), main_tip=branch_oid(repo, MAIN_BRANCH), task_branch=args.branch, task_tip=task_tip, integration_branch=integration_branch, integration_tip=integration_tip, plan=plan)

    removals = [(task_wt, args.branch, args.delete_branch)]
    if integration_wt is not None and integration_branch is not None:
        removals.append((integration_wt, integration_branch, True))
    removed_worktrees: list[str] = []
    deleted_branches: list[str] = []
    removal_outputs: list[dict[str, Any]] = []
    for worktree, branch, delete_branch in removals:
        expected_tip = integration_tip if branch == integration_branch else task_tip
        actual_tip = branch_oid(repo, branch)
        if actual_tip != expected_tip:
            emit("cleanup-pending", args.json, repo=str(repo), main_tip=branch_oid(repo, MAIN_BRANCH), task_branch=args.branch, task_tip=task_tip, integration_branch=integration_branch, integration_tip=integration_tip, branch=branch, expected_branch_tip=expected_tip, actual_branch_tip=actual_tip, removed_worktrees=removed_worktrees, deleted_branches=deleted_branches)
            return 1
        result = safe_remove(repo, worktree, branch, args, delete_branch)
        if not args.json and result.stdout:
            print(result.stdout, end="")
        if not args.json and result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        removal_outputs.append({"branch": branch, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode != 0:
            state = cleanup_state(repo, worktree, branch)
            if not state["worktree_registered"]:
                removed_worktrees.append(branch)
            if delete_branch and not state["branch_exists"]:
                deleted_branches.append(branch)
            emit("cleanup-partial", args.json, repo=str(repo), main_tip=branch_oid(repo, MAIN_BRANCH), task_branch=args.branch, integration_branch=integration_branch, integration_tip=integration_tip, failed_branch=branch, helper_exit=result.returncode, removed_worktrees=removed_worktrees, deleted_branches=deleted_branches, removal_outputs=removal_outputs, **state)
            return 1
        removed_worktrees.append(branch)
        if delete_branch:
            deleted_branches.append(branch)
    return emit("removed", args.json, repo=str(repo), main_tip=branch_oid(repo, MAIN_BRANCH), task_branch=args.branch, task_tip=task_tip, integration_branch=integration_branch, integration_tip=integration_tip, plan=plan, removed_worktrees=removed_worktrees, deleted_branches=deleted_branches, removal_outputs=removal_outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    start_parser = sub.add_parser("start", help="create a task worktree via worktree-create.py")
    start_parser.add_argument("--repo", required=True, help="explicit repository path; never inferred from cwd")
    start_parser.add_argument("--slug", required=True)
    start_parser.add_argument("--client", required=True, choices=meta.CLIENTS)
    start_parser.add_argument("--task", required=True)
    start_parser.add_argument("--from", dest="source", default=MAIN_BRANCH)
    start_parser.add_argument("--parent")
    start_parser.add_argument("--prefix", default="task", choices=("task", "integration"))
    start_parser.add_argument("--worktrees-root")
    start_parser.add_argument("--allow-repository-hooks", action="store_true")
    start_parser.add_argument("--json", action="store_true")
    status_parser = sub.add_parser("status", help="delegate liveness/ownership status to worktree-audit.py")
    status_parser.add_argument("--repo", required=True)
    status_parser.add_argument("--base", default=MAIN_BRANCH)
    status_parser.add_argument("--json", action="store_true")
    finish_parser = sub.add_parser("finish", help="integrate and safely remove an owned task worktree")
    finish_parser.add_argument("--repo", required=True)
    finish_parser.add_argument("--branch", required=True)
    finish_parser.add_argument("--external-writers-quiesced", action="store_true", help="assert known non-cooperating writers are stopped through integration and all cleanup")
    finish_parser.add_argument("--integration-message", default="chore: integrate task branch")
    finish_parser.add_argument("--delete-branch", action="store_true")
    finish_parser.add_argument("--discard-direnv-cache", action="store_true")
    finish_parser.add_argument("--discard-generated-caches", action="store_true")
    finish_parser.add_argument("--discard-generated-build-outputs", action="store_true")
    finish_parser.add_argument(
        "--allow-annex-filter", action="store_true",
        help="allow the verified git-annex filter in addition to normal repository hooks",
    )
    finish_parser.add_argument(
        "--preserve-generated-artifacts", action="store_true",
        help="quarantine and retain recognized caches and a marked git-hooks.nix config",
    )
    finish_parser.add_argument(
        "--allow-repository-hooks", action="store_true",
        help="run inspected repository hooks except reference-transaction hooks",
    )
    finish_parser.add_argument("--keep-worktree", action="store_true")
    finish_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "start":
            return start(args)
        if args.command == "status":
            repo = repo_root(args.repo)
            command = [sys.executable, str(AUDIT_HELPER), "--repo", str(repo), "--base", args.base]
            if args.json:
                command.append("--json")
            return subprocess.run(command, cwd=repo, check=False).returncode
        if not args.integration_message.strip() or "\n" in args.integration_message or "\r" in args.integration_message:
            raise TaskError("invalid-options", "--integration-message must be a non-empty single line")
        if args.discard_generated_caches and args.preserve_generated_artifacts:
            raise TaskError("invalid-options", "--discard-generated-caches cannot be combined with --preserve-generated-artifacts")
        if args.keep_worktree and (
            args.delete_branch or args.discard_direnv_cache or args.discard_generated_caches
            or args.discard_generated_build_outputs or args.preserve_generated_artifacts
        ):
            raise TaskError("invalid-options", "--keep-worktree cannot be combined with branch deletion/cache/output flags")
        return finish(args)
    except TaskError as error:
        return emit_error(error, getattr(args, "json", False))
    except (OSError, subprocess.SubprocessError) as error:
        return emit_error(TaskError("lifecycle-error", str(error)), getattr(args, "json", False))


if __name__ == "__main__":
    raise SystemExit(main())
