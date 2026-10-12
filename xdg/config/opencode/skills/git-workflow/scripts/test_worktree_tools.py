from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import worktree_meta as meta


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


create = load("worktree_create", "worktree-create.py")
audit = load("worktree_audit", "worktree-audit.py")

UUID = "0e7f96a6-1234-4abc-8def-0123456789ab"
OC_ID = "ses_" + "a" * 26


@pytest.fixture(autouse=True)
def isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in (
        "CLAUDE_CODE_SESSION_ID", "OPENCODE_SESSION_ID", "CLAUDE_PID", "OPENCODE_PID",
        "CLAUDE_CONFIG_DIR", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    ):
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_STATE_HOME", str(home / "state"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / "data"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "t")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "t")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@example.invalid")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "proj"
    path.mkdir()
    for args in (["init", "-q", "-b", "main"], ["commit", "-q", "--allow-empty", "-m", "root"]):
        subprocess.run(["git", *args], cwd=path, check=True)
    return path


def run_create(repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    argv = ["--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing", *extra]
    code = create.main(argv)
    assert code == 0
    return subprocess.CompletedProcess(argv, code)


def description(repo: Path, branch: str) -> str:
    return meta.git(repo, "config", "--get", f"branch.{branch}.description").stdout.strip()


def commit(cwd: Path, name: str, message: str) -> None:
    (cwd / name).write_text(name)
    meta.git(cwd, "add", name)
    meta.git(cwd, "commit", "-q", "-m", message)


def test_parse_roundtrip_and_structured_session_owner() -> None:
    text = meta.format_description("Fix the thing", "claude", UUID, "a" * 40, None, "task/x-20260101-01")
    task, trailer = meta.parse_description(text)
    assert task == "Fix the thing"
    assert trailer == {"client": "claude", "session": UUID, "base": "a" * 40, "parent": "task/x-20260101-01"}
    assert meta.parse_owner_description(text) == ("Fix the thing", "claude", UUID)


def test_task_text_cannot_forge_owner_trailer() -> None:
    with pytest.raises(ValueError, match="owner metadata tokens"):
        meta.format_description("tidy session=forged", "opencode", OC_ID, "b" * 40, None, None)
    with pytest.raises(ValueError):
        meta.format_description("two\nlines", "claude", UUID, "b" * 40, None, None)


def test_owner_parser_requires_structured_known_session() -> None:
    valid = meta.format_description("same session, two tasks", "opencode", OC_ID, "b" * 40, None, None)
    assert meta.parse_owner_description(valid) == ("same session, two tasks", "opencode", OC_ID)
    assert meta.parse_owner_description("legacy task client=opencode") is None
    unknown = meta.format_description("unknown task", "opencode", "unknown", "b" * 40, None, None)
    assert meta.parse_owner_description(unknown) is None
    duplicate = valid + " session=" + OC_ID
    assert meta.parse_owner_description(duplicate) is None
    malformed_pid = meta.format_description("PID boundary", "opencode", OC_ID, "b" * 40, None, None) + " pid=1@0"
    assert meta.parse_owner_description(malformed_pid) is None


def test_session_comes_only_from_the_clients_own_variable() -> None:
    env = {"CLAUDE_CODE_SESSION_ID": UUID, "OPENCODE_SESSION_ID": OC_ID}
    assert meta.session_from_env("claude", env) == (UUID, None)
    assert meta.session_from_env("opencode", env) == (OC_ID, None)
    assert meta.session_from_env("copilot", env) == ("unknown", None)
    assert meta.session_from_env("opencode", {"CLAUDE_CODE_SESSION_ID": UUID})[0] == "unknown"
    assert meta.session_from_env("claude", {"CLAUDE_CODE_SESSION_ID": "not-a-uuid"})[0] == "unknown"
    assert meta.current_session_identity({"OPENCODE_SESSION_ID": OC_ID}) == ("opencode", OC_ID)
    assert meta.current_session_identity({"CLAUDE_CODE_SESSION_ID": UUID}) == ("claude", UUID)
    assert meta.current_session_identity({"CLAUDE_CODE_SESSION_ID": UUID, "OPENCODE_SESSION_ID": OC_ID}) is None
    assert meta.current_session_identity({"OPENCODE_SESSION_ID": "bad"}) is None
    assert meta.current_session_identity({}) is None


def test_create_numbers_branches_and_records_owner(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", UUID)
    monkeypatch.setenv("CLAUDE_PID", str(os.getpid()))
    run_create(repo)
    run_create(repo)
    branches = meta.git(repo, "branch", "--list", "task/*", "--format=%(refname:short)").stdout.split()
    assert any(b.endswith("-01") for b in branches) and any(b.endswith("-02") for b in branches)
    second = next(b for b in branches if b.endswith("-02"))
    text = description(repo, second)
    base = meta.git(repo, "rev-parse", "main").stdout.strip()
    assert f"client=claude session={UUID} base={base}" in text
    assert f"pid={os.getpid()}@" in text
    assert (Path(os.environ["XDG_STATE_HOME"]) / "proj" / "worktrees" / second.split("/", 1)[1]).is_dir()


def test_create_without_session_records_unknown(repo: Path) -> None:
    run_create(repo)
    branch = meta.git(repo, "branch", "--list", "task/*", "--format=%(refname:short)").stdout.split()[0]
    assert "session=unknown" in description(repo, branch)


def test_create_rejects_bad_slug_and_missing_source(repo: Path) -> None:
    with pytest.raises(SystemExit):
        create.main(["--repo", str(repo), "--slug", "Bad Slug", "--client", "claude", "--task", "t"])
    with pytest.raises(SystemExit):
        create.main(["--repo", str(repo), "--slug", "ok-slug", "--client", "claude", "--task", "t", "--from", "nope"])
    with pytest.raises(SystemExit):
        create.main(["--repo", str(repo), "--slug", "ok-slug", "--client", "claude", "--task", "tidy session=forged"])
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1


def test_create_requires_opt_in_for_post_checkout_hook(repo: Path, tmp_path: Path) -> None:
    hooks = Path(meta.git(repo, "rev-parse", "--git-path", "hooks").stdout.strip())
    if not hooks.is_absolute():
        hooks = repo / hooks
    marker = tmp_path / "post-checkout-ran"
    hook = hooks / "post-checkout"
    hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n")
    hook.chmod(0o755)
    argv = ["--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing"]

    with pytest.raises(SystemExit) as caught:
        create.main(argv)

    assert caught.value.code == 2
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1

    assert create.main([*argv, "--allow-repository-hooks"]) == 0
    assert marker.read_text() == "called"


def test_create_checks_relative_hooks_from_the_source_tree(repo: Path, tmp_path: Path) -> None:
    meta.git(repo, "switch", "-q", "-c", "hooked-source")
    marker = tmp_path / "source-post-checkout-ran"
    hook = repo / ".githooks" / "post-checkout"
    hook.parent.mkdir()
    hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n")
    hook.chmod(0o755)
    meta.git(repo, "add", ".githooks/post-checkout")
    meta.git(repo, "commit", "-q", "-m", "add source hook")
    meta.git(repo, "switch", "-q", "main")
    meta.git(repo, "config", "core.hooksPath", "./.githooks")
    argv = [
        "--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing",
        "--from", "hooked-source",
    ]

    with pytest.raises(SystemExit) as caught:
        create.main(argv)

    assert caught.value.code == 2
    assert not marker.exists()
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1


def test_create_blocks_hook_beneath_source_tree_symlink_ancestor(repo: Path, tmp_path: Path) -> None:
    external_hooks = tmp_path / "external" / "hooks"
    external_hooks.mkdir(parents=True)
    marker = tmp_path / "external-post-checkout-ran"
    hook = external_hooks / "post-checkout"
    hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n")
    hook.chmod(0o755)
    meta.git(repo, "switch", "-q", "-c", "hooked-source")
    (repo / "tools").symlink_to(tmp_path / "external", target_is_directory=True)
    meta.git(repo, "add", "tools")
    meta.git(repo, "commit", "-q", "-m", "add hook symlink ancestor")
    meta.git(repo, "switch", "-q", "main")
    meta.git(repo, "config", "core.hooksPath", "tools/hooks")

    with pytest.raises(SystemExit) as caught:
        create.main([
            "--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing",
            "--from", "hooked-source",
        ])

    assert caught.value.code == 2
    assert not marker.exists()
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1


def test_create_runs_relative_hooks_from_repository_and_target_paths(repo: Path, tmp_path: Path) -> None:
    hook_root = repo / ".githooks"
    hook_root.mkdir()
    marker = tmp_path / "relative-post-checkout-ran"
    hook = hook_root / "post-checkout"
    hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n")
    hook.chmod(0o755)
    meta.git(repo, "add", ".githooks/post-checkout")
    meta.git(repo, "commit", "-q", "-m", "add relative checkout hook")
    meta.git(repo, "config", "core.hooksPath", "./.githooks")
    argv = ["--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing"]

    with pytest.raises(SystemExit) as caught:
        create.main(argv)
    assert caught.value.code == 2 and not marker.exists()
    assert create.main([*argv, "--allow-repository-hooks"]) == 0
    assert marker.read_text() == "called"


def test_create_never_allows_reference_transaction_hook(repo: Path, tmp_path: Path) -> None:
    hooks = Path(meta.git(repo, "rev-parse", "--git-path", "hooks").stdout.strip())
    if not hooks.is_absolute():
        hooks = repo / hooks
    marker = tmp_path / "reference-transaction-ran"
    hook = hooks / "reference-transaction"
    hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n")
    hook.chmod(0o755)
    argv = [
        "--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing",
        "--allow-repository-hooks",
    ]

    with pytest.raises(SystemExit) as caught:
        create.main(argv)

    assert caught.value.code == 2
    assert not marker.exists()
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1


def test_create_refuses_uninspectable_parent_relative_hooks_path(repo: Path) -> None:
    meta.git(repo, "config", "core.hooksPath", "tools/../hooks")

    with pytest.raises(SystemExit) as caught:
        create.main([
            "--repo", str(repo), "--slug", "fix-thing", "--client", "claude", "--task", "Fix the thing",
            "--allow-repository-hooks",
        ])

    assert caught.value.code == 2
    assert meta.git(repo, "worktree", "list", "--porcelain").stdout.count("worktree ") == 1


def audit_rows(repo: Path, **kwargs):
    return audit.audit(
        repo, "main", kwargs.get("active_hours", 2.0), dict(os.environ), kwargs.get("now", time.time()),
        str(HERE),
    )


def set_transcript_age(hours: float) -> None:
    root = Path(os.environ["HOME"]) / ".claude" / "projects" / "-x"
    root.mkdir(parents=True, exist_ok=True)
    file = root / f"{UUID}.jsonl"
    file.write_text("{}")
    old = time.time() - hours * 3600
    os.utime(file, (old, old))


def test_audit_states(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", UUID)
    run_create(repo)
    branch = meta.git(repo, "branch", "--list", "task/*", "--format=%(refname:short)").stdout.split()[0]
    wt = next(e["worktree"] for e in audit.worktrees(repo))

    assert audit_rows(repo)[0].state == "UNKNOWN"  # transcript not found: never idle

    set_transcript_age(0.5)
    assert audit_rows(repo)[0].state == "ACTIVE"

    set_transcript_age(30)
    row = audit_rows(repo)[0]
    assert row.state == "IDLE-UNMERGED" and row.command is None  # no commits beyond base yet

    (Path(wt) / "f.txt").write_text("x")
    meta.git(wt, "add", "f.txt")
    meta.git(wt, "commit", "-q", "-m", "work")
    row = audit_rows(repo)[0]
    assert row.state == "IDLE-UNMERGED" and row.command is None

    meta.git(repo, "merge", "-q", "--ff-only", branch)
    row = audit_rows(repo)[0]
    assert row.state == "IDLE-MERGED"
    assert row.command is not None and "--dry-run" in row.command
    assert "--expect-branch" in row.command and branch in row.command
    assert "--expect-owner" not in row.command
    assert "--discard-generated-caches" not in row.command

    (Path(wt) / "dirty.txt").write_text("y")
    assert audit_rows(repo)[0].state == "IDLE-UNMERGED"


def test_audit_pid_is_a_positive_signal(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", UUID)
    monkeypatch.setenv("CLAUDE_PID", str(os.getpid()))
    run_create(repo)
    set_transcript_age(30)
    assert audit_rows(repo)[0].state == "ACTIVE"


def test_audit_never_offers_another_session_worktree(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", UUID)
    run_create(repo)
    branch = meta.git(repo, "branch", "--list", "task/*", "--format=%(refname:short)").stdout.split()[0]
    wt = Path(next(e["worktree"] for e in audit.worktrees(repo)))
    commit(wt, "work.txt", "work")
    meta.git(repo, "merge", "--ff-only", branch)
    set_transcript_age(30)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID")
    monkeypatch.setenv("OPENCODE_SESSION_ID", OC_ID)

    row = audit_rows(repo)[0]
    assert row.state == "IDLE-OTHER-SESSION"
    assert row.command is None


def test_audit_legacy_and_missing_description(repo: Path) -> None:
    for name, desc in (("old", "Old task client=claude"), ("bare", None)):
        meta.git(repo, "worktree", "add", "-q", "-b", f"task/{name}", str(repo.parent / name))
        if desc:
            meta.git(repo, "config", f"branch.task/{name}.description", desc)
    states = {Path(r.path).name: r.state for r in audit_rows(repo)}
    assert states == {"old": "LEGACY", "bare": "UNKNOWN"}


def test_audit_does_not_modify_the_repository(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", UUID)
    run_create(repo)
    before = meta.git(repo, "for-each-ref").stdout, (repo / ".git" / "config").read_text()
    audit_rows(repo)
    assert before == (meta.git(repo, "for-each-ref").stdout, (repo / ".git" / "config").read_text())
    assert json.dumps(audit.asdict(audit_rows(repo)[0]))
