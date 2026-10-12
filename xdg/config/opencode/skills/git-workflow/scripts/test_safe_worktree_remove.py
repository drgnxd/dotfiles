from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("safe-worktree-remove.py")
LOCK = "main-integration.lock"
SESSION = "ses_" + "a" * 26
sys.path.insert(0, str(SCRIPT.parent))
import worktree_meta as meta

SPEC = importlib.util.spec_from_file_location("safe_worktree_remove", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HELPER
SPEC.loader.exec_module(HELPER)


@pytest.fixture(autouse=True)
def isolated_git_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / ".local" / "state"))
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.setenv("OPENCODE_SESSION_ID", SESSION)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def run_raw(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False, env=env, cwd=cwd)


def run(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    actual_args = list(args)
    if actual_args and "--expect-branch" not in actual_args and "--expect-owner" not in actual_args:
        worktree = Path(actual_args[0])
        if worktree.is_dir():
            branch = subprocess.run(
                ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
                cwd=worktree, capture_output=True, text=True, check=False,
            )
            if branch.returncode == 0:
                actual_args.extend(("--expect-branch", branch.stdout.strip()))
    return run_raw(*actual_args, env=env, cwd=cwd)


def commit(cwd: Path, name: str, message: str = "c") -> str:
    (cwd / name).write_text(name)
    git(cwd, "add", name)
    git(cwd, "commit", "--quiet", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    main = tmp_path / "main"
    main.mkdir()
    git(main, "init", "--quiet", "-b", "main")
    git(main, "config", "user.name", "Fixture")
    git(main, "config", "user.email", "fixture@example.invalid")
    commit(main, "a.txt", "init")
    return main


def admin_of(wt: Path) -> Path:
    text = (wt / ".git").read_text().removeprefix("gitdir: ").strip() if (wt / ".git").is_file() else os.readlink(wt / ".git")
    return (wt / text).resolve()


def make_worktree(main: Path, name: str, *, symlink: bool = True, extra: tuple[str, ...] = ()) -> Path:
    wt = main.parent / name
    git(main, "worktree", "add", "--quiet", *extra, "-b", f"task/{name}", str(wt))
    description = meta.format_description(
        f"test task {name}", "opencode", SESSION, git(wt, "rev-parse", "HEAD"), None, None,
    )
    git(main, "config", f"branch.task/{name}.description", description)
    if symlink:
        admin = admin_of(wt)
        (wt / ".git").unlink()
        os.symlink(os.path.relpath(admin, wt), wt / ".git")
    return wt


def owner_description(wt: Path, task: str, *, session: str = SESSION, client: str = "opencode") -> str:
    return meta.format_description(task, client, session, git(wt, "rev-parse", "HEAD"), None, None)


def set_owner(main: Path, wt: Path, task: str, *, session: str = SESSION, client: str = "opencode") -> str:
    branch = git(wt, "symbolic-ref", "--short", "HEAD")
    description = owner_description(wt, task, session=session, client=client)
    git(main, "config", f"branch.{branch}.description", description)
    return description


def add_canonical_database(main: Path, data: bytes = b"canonical database") -> Path:
    (main / ".gitignore").write_text("cultura.db\n*.ignored\ncultura.db/\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "--quiet", "-m", "ignore database state")
    database = main / "cultura.db"
    database.write_bytes(data)
    return database


def link_canonical_database(main: Path, worktree: Path) -> Path:
    link = worktree / "cultura.db"
    link.symlink_to(main / "cultura.db")
    return link


def add_direnv_ignore(main: Path, *, include_database: bool = False) -> None:
    entries = [".direnv/"]
    if include_database:
        entries.append("cultura.db")
    (main / ".gitignore").write_text("\n".join(entries) + "\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "--quiet", "-m", "ignore worktree runtime state")


def add_generated_cache_ignores(main: Path) -> None:
    (main / ".gitignore").write_text(".pytest_cache/\n.ruff_cache/\n__pycache__/\nkeep.ignored\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "--quiet", "-m", "ignore generated caches")


def add_generated_build_output_ignores(main: Path) -> None:
    (main / ".gitignore").write_text("rust/target/\nresult\n")
    git(main, "add", ".gitignore")
    git(main, "commit", "--quiet", "-m", "ignore generated build outputs")


def make_generated_caches(wt: Path) -> tuple[Path, ...]:
    paths = (
        wt / ".pytest_cache" / "v" / "cache" / "nodeids",
        wt / ".ruff_cache" / "0.17.0" / "content",
        wt / "xdg" / "config" / "opencode" / "skills" / "git-workflow" / "scripts" / "__pycache__" / "helper.pyc",
    )
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"generated cache")
    return paths


def make_nix_direnv_cache(worktree: Path, store_root: Path) -> Path:
    cache = worktree / ".direnv"
    bin_dir = cache / "bin"
    inputs_dir = cache / "flake-inputs"
    bin_dir.mkdir(parents=True)
    inputs_dir.mkdir()

    input_hash = "a" * 32
    input_target = store_root / f"{input_hash}-source"
    input_target.mkdir(parents=True)
    (inputs_dir / f"{input_hash}-source").symlink_to(input_target)

    profile_hash = "b" * 40
    profile_target = store_root / f"{'c' * 32}-nix-shell-env"
    profile_target.mkdir()
    (cache / f"flake-profile-{profile_hash}").symlink_to(profile_target)
    (cache / f"flake-profile-{profile_hash}.rc").write_text("export PATH=/nix/store/bin\n")
    reload = bin_dir / "nix-direnv-reload"
    reload.write_text("#!/bin/sh\nexit 0\n")
    reload.chmod(0o711)
    return cache


def make_git_wrapper(
    tmp_path: Path,
    *,
    trigger: tuple[str, ...] | None = None,
    hook: str = "",
    hook_on_second_status: bool = False,
    reverse_worktrees: bool = False,
    duplicate_main: bool = False,
    refuse_remove: bool = False,
) -> Path:
    real_git = shutil.which("git")
    assert real_git is not None
    bin_dir = tmp_path / "git-wrapper-bin"
    bin_dir.mkdir()
    counter = tmp_path / "git-wrapper-status-count"
    trigger_marker = tmp_path / "git-wrapper-triggered"
    lines = [
        "#!/usr/bin/env python3",
        "import subprocess, sys",
        "from pathlib import Path",
        f"real_git = {real_git!r}",
        "args = sys.argv[1:]",
    ]
    if hook_on_second_status:
        lines.extend([
            "if args[:1] == ['status']:",
            f"    counter = Path({str(counter)!r})",
            "    count = int(counter.read_text()) + 1 if counter.exists() else 1",
            "    counter.write_text(str(count))",
            "    if count == 2:",
            *(f"        {line}" for line in hook.splitlines()),
        ])
    if trigger is not None:
        lines.extend([
            f"if tuple(args) == {trigger!r} and not Path({str(trigger_marker)!r}).exists():",
            f"    Path({str(trigger_marker)!r}).write_text('triggered')",
        ])
        lines.extend(f"    {line}" for line in hook.splitlines())
    if refuse_remove:
        lines.extend([
            "if args[:2] == ['worktree', 'remove']:",
            "    sys.stderr.write('fatal: simulated refusal\\n')",
            "    raise SystemExit(128)",
        ])
    lines.append("result = subprocess.run([real_git, *args], capture_output=True)")
    if reverse_worktrees or duplicate_main:
        lines.extend([
            "if args == ['worktree', 'list', '--porcelain']:",
            "    blocks = [block for block in result.stdout.split(b'\\n\\n') if block]",
        ])
        if reverse_worktrees:
            lines.append("    blocks.reverse()")
        if duplicate_main:
            lines.extend([
                "    main_blocks = [block for block in blocks if b'branch refs/heads/main' in block]",
                "    blocks.extend(main_blocks)",
            ])
        lines.append("    result.stdout = b'\\n\\n'.join(blocks) + b'\\n\\n'")
    lines.extend([
        "sys.stdout.buffer.write(result.stdout)",
        "sys.stderr.buffer.write(result.stderr)",
        "raise SystemExit(result.returncode)",
    ])
    wrapper = bin_dir / "git"
    wrapper.write_text("\n".join(lines) + "\n")
    wrapper.chmod(0o755)
    return bin_dir


def run_with_git_wrapper(wt: Path, bin_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    return run(str(wt), *args, env=env)


def assert_untouched(wt: Path, *, symlink: bool = True) -> None:
    assert wt.exists()
    assert (wt / ".git").is_symlink() == symlink
    assert not list(wt.glob(".git.normalize.*"))


def test_removes_symlinked_worktree_and_branch(repo: Path) -> None:
    wt = make_worktree(repo, "wt1")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert "task/wt1" not in git(repo, "branch", "--list")
    assert git(repo, "worktree", "list").count("\n") == 0
    assert not (repo / ".git" / LOCK).exists()
    assert not list((repo / ".git").glob(f"{LOCK}*"))


def config_keys(repo: Path, pattern: str) -> str:
    return subprocess.run(["git", "config", "--get-regexp", pattern], cwd=repo, capture_output=True, text=True, check=False).stdout


def test_owner_goes_to_stderr_and_stdout_is_unchanged(repo: Path) -> None:
    wt = make_worktree(repo, "wt-desc")
    result = run(str(wt))
    assert result.returncode == 0, result.stderr
    assert f"owner: client=opencode session={SESSION}; branch=task/wt-desc; task=test task wt-desc" in result.stderr.splitlines()
    assert result.stdout == f"removed {wt.resolve()}\n"


def test_delete_branch_drops_only_its_own_config_section(repo: Path) -> None:
    wt = make_worktree(repo, "wt-desc")
    git(repo, "branch", "task/wt-desc-x")
    git(repo, "config", "branch.task/wt-desc.remote", "origin")
    git(repo, "config", "branch.task/wt-desc-x.description", "sibling")
    assert run(str(wt), "--delete-branch").returncode == 0
    assert config_keys(repo, r"^branch\.task/wt-desc\.") == ""
    assert git(repo, "config", "--get", "branch.task/wt-desc-x.description") == "sibling"


def test_branch_without_session_owner_is_preserved(repo: Path) -> None:
    wt = make_worktree(repo, "wt-upstream")
    git(repo, "config", "--unset", "branch.task/wt-upstream.description")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert_untouched(wt)
    assert "task/wt-upstream" in git(repo, "branch", "--list")


def test_unusual_branch_name_section_is_removed(repo: Path) -> None:
    wt = repo.parent / "wt-dotted"
    git(repo, "worktree", "add", "--quiet", "-b", "task/Foo.v2", str(wt))
    description = meta.format_description("dotted task", "opencode", SESSION, git(wt, "rev-parse", "HEAD"), None, None)
    git(repo, "config", "branch.task/Foo.v2.description", description)
    assert run(str(wt), "--delete-branch").returncode == 0
    assert config_keys(repo, r"^branch\.") == ""


def test_dry_run_prints_owner_and_keeps_description(repo: Path) -> None:
    wt = make_worktree(repo, "wt-desc2")
    result = run(str(wt), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert f"owner: client=opencode session={SESSION}; branch=task/wt-desc2; task=test task wt-desc2" in result.stderr.splitlines()
    assert "client=opencode session=" + SESSION in git(repo, "config", "--get", "branch.task/wt-desc2.description")


def test_refusal_still_reports_owner(repo: Path) -> None:
    wt = make_worktree(repo, "wt-refused")
    (wt / "new.txt").write_text("x")
    result = run(str(wt))
    assert result.returncode == 1 and "not clean" in result.stderr
    assert f"owner: client=opencode session={SESSION}; branch=task/wt-refused; task=test task wt-refused" in result.stderr.splitlines()


def test_malformed_description_is_not_a_session_owner(repo: Path) -> None:
    wt = make_worktree(repo, "wt-multi")
    git(repo, "config", "branch.task/wt-multi.description", "line1\nline2\x1b[31m")
    result = run(str(wt))
    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert "owner: unknown; branch=task/wt-multi" in result.stderr.splitlines()
    assert_untouched(wt)


def test_japanese_description_is_kept_readable(repo: Path) -> None:
    wt = make_worktree(repo, "wt-ja")
    description = meta.format_description("worktree命名の記録", "opencode", SESSION, git(wt, "rev-parse", "HEAD"), None, None)
    git(repo, "config", "branch.task/wt-ja.description", description)
    result = run(str(wt))
    assert f"owner: client=opencode session={SESSION}; branch=task/wt-ja; task=worktree命名の記録" in result.stderr.splitlines()
    assert git(repo, "config", "--get", "branch.task/wt-ja.description") == description


def test_description_from_env_config_does_not_fail_the_cleanup(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wt = make_worktree(repo, "wt-env")
    description = meta.format_description("task from environment config", "opencode", SESSION, git(wt, "rev-parse", "HEAD"), None, None)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "branch.task/wt-env.description")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", description)
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert "task/wt-env" not in git(repo, "branch", "--list")


def test_busy_config_only_warns_after_removal(repo: Path) -> None:
    wt = make_worktree(repo, "wt-busy")
    (repo / ".git" / "config.lock").write_text("")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert not wt.exists() and "task/wt-busy" not in git(repo, "branch", "--list")
    assert "warning: refs/heads/task/wt-busy removed, but config section" in result.stderr


def test_without_description_refuses_automatic_removal(repo: Path) -> None:
    wt = make_worktree(repo, "wt-nodesc")
    git(repo, "config", "--unset", "branch.task/wt-nodesc.description")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert "owner: unknown; branch=task/wt-nodesc" in result.stderr.splitlines()
    assert_untouched(wt)


def test_detached_worktree_reports_none(repo: Path) -> None:
    wt = repo.parent / "wt-detached"
    git(repo, "worktree", "add", "--quiet", "--detach", str(wt))
    result = run_raw(str(wt), "--expect-branch", "task/detached")
    assert result.returncode == 1 and "not on a local branch" in result.stderr
    assert_untouched(wt, symlink=False)


def test_description_kept_when_branch_is_kept(repo: Path) -> None:
    wt = make_worktree(repo, "wt-keep")
    assert run(str(wt)).returncode == 0
    assert "task/wt-keep" in git(repo, "branch", "--list")
    assert "session=" + SESSION in git(repo, "config", "--get", "branch.task/wt-keep.description")


def test_plain_gitfile_worktree_is_also_removed(repo: Path) -> None:
    wt = make_worktree(repo, "wt2", symlink=False)
    assert run(str(wt)).returncode == 0
    assert not wt.exists()


def test_exact_branch_selects_one_of_two_same_session_worktrees(repo: Path) -> None:
    first = make_worktree(repo, "wt-same-session-a")
    second = make_worktree(repo, "wt-same-session-b")
    result = run(str(first), "--expect-branch", "task/wt-same-session-b")
    assert result.returncode == 1 and "branch mismatch" in result.stderr
    assert_untouched(first)
    assert_untouched(second)
    assert not (repo / ".git" / LOCK).exists()


def test_other_session_cannot_remove_worktree_before_annex_restage(repo: Path, tmp_path: Path) -> None:
    wt = make_worktree(repo, "wt-other-session")
    other = "ses_" + "b" * 26
    description = meta.format_description("other session task", "opencode", other, git(wt, "rev-parse", "HEAD"), None, None)
    git(repo, "config", "branch.task/wt-other-session.description", description)
    git(repo, "config", "filter.annex.process", "git-annex filter-process")
    log = tmp_path / "annex.log"
    bin_dir = tmp_path / "annex-bin"
    bin_dir.mkdir()
    stub = bin_dir / "git-annex"
    stub.write_text(f'#!/bin/sh\nprintf "$*" >> "{log}"\n')
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}

    result = run(str(wt), env=env)

    assert result.returncode == 1 and "different client session" in result.stderr
    assert not log.exists()
    assert_untouched(wt)
    assert not (repo / ".git" / LOCK).exists()


def test_unknown_session_metadata_cannot_authorize_removal(repo: Path) -> None:
    wt = make_worktree(repo, "wt-unknown-session")
    description = meta.format_description("unknown session task", "opencode", meta.UNKNOWN, git(wt, "rev-parse", "HEAD"), None, None)
    git(repo, "config", "branch.task/wt-unknown-session.description", description)
    result = run(str(wt))
    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert_untouched(wt)


def test_invalid_pid_metadata_cannot_authorize_removal(repo: Path) -> None:
    wt = make_worktree(repo, "wt-invalid-pid")
    description = meta.format_description("invalid PID task", "opencode", SESSION, git(wt, "rev-parse", "HEAD"), None, None)
    git(repo, "config", "branch.task/wt-invalid-pid.description", description + " pid=1@0")
    result = run(str(wt))
    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert_untouched(wt)


def test_missing_current_session_refuses(repo: Path) -> None:
    wt = make_worktree(repo, "wt-no-current-session")
    env = {key: value for key, value in os.environ.items() if key not in ("OPENCODE_SESSION_ID", "CLAUDE_CODE_SESSION_ID")}
    result = run(str(wt), env=env)
    assert result.returncode == 1 and "current client session" in result.stderr
    assert_untouched(wt)


def test_ambiguous_current_sessions_refuse(repo: Path) -> None:
    wt = make_worktree(repo, "wt-ambiguous-session")
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "0e7f96a6-1234-4abc-8def-0123456789ab"}
    result = run(str(wt), env=env)
    assert result.returncode == 1 and "current client session" in result.stderr
    assert_untouched(wt)


def test_old_expect_owner_flag_is_rejected(repo: Path) -> None:
    wt = make_worktree(repo, "wt-old-owner-flag")
    result = run(str(wt), "--expect-owner", "test task wt-old-owner-flag")
    assert result.returncode == 1 and "obsolete" in result.stderr
    assert_untouched(wt)


def test_branch_selector_is_required(repo: Path) -> None:
    wt = make_worktree(repo, "wt-missing-branch-selector")
    result = run_raw(str(wt))
    assert result.returncode == 1 and "--expect-branch is required" in result.stderr
    assert_untouched(wt)


def git_supports_relative_paths() -> bool:
    result = subprocess.run(["git", "worktree", "add", "-h"], capture_output=True, text=True, check=False)
    return "relative-paths" in result.stdout + result.stderr


@pytest.mark.skipif(not git_supports_relative_paths(), reason="needs a Git with `worktree add --relative-paths`")
def test_relative_paths_worktree(repo: Path) -> None:
    wt = make_worktree(repo, "wt3", symlink=False, extra=("--relative-paths",))
    result = run(str(wt))
    assert result.returncode == 0, result.stderr


def test_dry_run_changes_nothing(repo: Path) -> None:
    wt = make_worktree(repo, "wt4")
    result = run(str(wt), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert_untouched(wt)
    assert not (repo / ".git" / LOCK).exists()


def test_refuses_untracked_file(repo: Path) -> None:
    wt = make_worktree(repo, "wt5")
    (wt / "new.txt").write_text("x")
    result = run(str(wt))
    assert result.returncode == 1 and "not clean" in result.stderr
    assert_untouched(wt)
    assert (wt / "new.txt").exists()
    assert not (repo / ".git" / LOCK).exists()


def test_refuses_staged_only_change(repo: Path) -> None:
    wt = make_worktree(repo, "wt6")
    (wt / "s.txt").write_text("s")
    git(wt, "add", "s.txt")
    result = run(str(wt))
    assert result.returncode == 1 and "not clean" in result.stderr
    assert_untouched(wt)


def test_refuses_ignored_files(repo: Path) -> None:
    (repo / ".gitignore").write_text("*.log\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore")
    wt = make_worktree(repo, "wt7")
    (wt / "x.log").write_text("keep me")
    result = run(str(wt))
    assert result.returncode == 1 and "x.log" in result.stderr
    assert (wt / "x.log").exists()


def test_generated_cache_flag_is_opt_in(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-default")
    cache_files = make_generated_caches(wt)

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)


def test_generated_build_output_flag_is_opt_in(repo: Path, tmp_path: Path) -> None:
    add_generated_build_output_ignores(repo)
    wt = make_worktree(repo, "wt-build-output-default")
    target_file = wt / "rust" / "target" / "debug" / "artifact"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("build output")
    result_target = tmp_path / "nix-result"
    result_target.mkdir()
    (result_target / "output").write_text("keep target")
    result_link = wt / "result"
    result_link.symlink_to(result_target)

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert_untouched(wt)
    assert target_file.read_text() == "build output"
    assert result_link.is_symlink() and (result_target / "output").read_text() == "keep target"


def test_discards_only_selected_generated_build_outputs(repo: Path, tmp_path: Path) -> None:
    add_generated_build_output_ignores(repo)
    wt = make_worktree(repo, "wt-build-output-discard")
    target_file = wt / "rust" / "target" / "debug" / "artifact"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("build output")
    result_target = tmp_path / "nix-result"
    result_target.mkdir()
    (result_target / "output").write_text("keep target")
    result_link = wt / "result"
    result_link.symlink_to(result_target)

    dry_run = run(str(wt), "--discard-generated-build-outputs", "--dry-run")
    assert dry_run.returncode == 0, dry_run.stderr
    assert "generated artifact paths would be discarded: result, rust/target" in dry_run.stdout
    assert target_file.read_text() == "build output"
    assert result_link.is_symlink() and (result_target / "output").read_text() == "keep target"

    result = run(str(wt), "--discard-generated-build-outputs", "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert "discarded generated artifact paths: result, rust/target" in result.stdout
    assert (result_target / "output").read_text() == "keep target"
    assert "task/wt-build-output-discard" not in git(repo, "branch", "--list")
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_result_symlink_does_not_probe_its_target_for_open_handles(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_build_output_ignores(repo)
    wt = make_worktree(repo, "wt-result-no-target-probe")
    result_target = tmp_path / "open-result-target"
    result_target.mkdir()
    result_link = wt / "result"
    result_link.symlink_to(result_target)

    def fail_if_target_is_probed(paths: tuple[Path, ...]) -> set[str] | None:
        pytest.fail(f"result symlink target was passed to lsof: {paths}")

    monkeypatch.setattr(HELPER, "lsof_open_paths", fail_if_target_is_probed)
    outcome = HELPER.remove(
        str(wt), "main", delete_branch_too=False, lock_name=LOCK,
        allow_unreferenced_reflog=False, expect_branch="task/wt-result-no-target-probe",
        discard_generated_build_outputs=True,
    )

    assert not wt.exists()
    assert outcome.discarded_generated_caches == ("result",)
    assert result_target.is_dir()


def test_generated_build_output_selector_rejects_result_directory(repo: Path) -> None:
    add_generated_build_output_ignores(repo)
    wt = make_worktree(repo, "wt-result-directory")
    result_file = wt / "result" / "must-keep"
    result_file.parent.mkdir()
    result_file.write_text("preserve")

    result = run(str(wt), "--discard-generated-build-outputs")

    assert result.returncode == 1 and "root result is not a symlink" in result.stderr
    assert_untouched(wt)
    assert result_file.read_text() == "preserve"


def test_generated_build_output_flag_preserves_other_ignored_data(repo: Path) -> None:
    (repo / ".gitignore").write_text("rust/target/\nresult\nkeep.ignored\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore generated build outputs")
    wt = make_worktree(repo, "wt-build-output-and-user-data")
    target_file = wt / "rust" / "target" / "debug" / "artifact"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("build output")
    keep = wt / "keep.ignored"
    keep.write_text("preserve")

    result = run(str(wt), "--discard-generated-build-outputs")

    assert result.returncode == 1 and "keep.ignored" in result.stderr
    assert_untouched(wt)
    assert target_file.read_text() == "build output"
    assert keep.read_text() == "preserve"


def test_generated_build_outputs_restore_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    add_generated_build_output_ignores(repo)
    wt = make_worktree(repo, "wt-build-output-remove-refused")
    target_file = wt / "rust" / "target" / "debug" / "artifact"
    target_file.parent.mkdir(parents=True)
    target_file.write_text("build output")
    result_target = tmp_path / "preserved-result"
    result_target.mkdir()
    result_link = wt / "result"
    result_link.symlink_to(result_target)
    bin_dir = make_git_wrapper(tmp_path, refuse_remove=True)

    result = run_with_git_wrapper(wt, bin_dir, "--discard-generated-build-outputs")

    assert result.returncode == 1 and "simulated refusal" in result.stderr
    assert_untouched(wt)
    assert target_file.read_text() == "build output"
    assert result_link.is_symlink() and result_link.resolve() == result_target


def test_generated_cache_dry_run_enumerates_without_changes(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-dry-run")
    cache_files = make_generated_caches(wt)

    result = run(str(wt), "--discard-generated-caches", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "generated artifact paths would be discarded" in result.stdout
    assert ".pytest_cache, .ruff_cache," in result.stdout
    assert "scripts/__pycache__" in result.stdout
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    assert not (Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine").exists()


def test_preserves_generated_caches_and_nix_precommit_config_in_quarantine(repo: Path) -> None:
    (repo / ".gitignore").write_text(
        ".pytest_cache/\n.ruff_cache/\n__pycache__/\n.pre-commit-config.yaml\n"
    )
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore generated files")
    wt = make_worktree(repo, "wt-preserve-generated")
    cache_files = make_generated_caches(wt)
    config = wt / ".pre-commit-config.yaml"
    config.write_text(
        '# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{\n  "repos": []\n}\n',
        encoding="utf-8",
    )
    expected_config = config.read_bytes()

    result = run(str(wt), "--preserve-generated-artifacts", "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert result.stdout.count("preserved generated artifact quarantine at ") == len(cache_files) + 1
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    transaction = next(quarantine.iterdir())
    manifest = json.loads((transaction / "manifest.json").read_text())
    records = manifest["generated_caches"]
    config_record = next(record for record in records if record["path"] == ".pre-commit-config.yaml")
    assert Path(config_record["quarantine_path"]).read_bytes() == expected_config
    for cache_file in cache_files:
        relative = cache_file.relative_to(wt)
        record = next(
            item for item in records
            if relative == Path(item["path"]) or Path(item["path"]) in relative.parents
        )
        suffix = relative.relative_to(Path(record["path"]))
        assert (Path(record["quarantine_path"]) / suffix).read_bytes() == b"generated cache"
    assert manifest["phase"] == "completed_preserved"


def test_preserve_generated_artifacts_requires_nix_marker_for_precommit_config(repo: Path) -> None:
    (repo / ".gitignore").write_text(".pre-commit-config.yaml\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore generated config")
    wt = make_worktree(repo, "wt-unverified-precommit-config")
    config = wt / ".pre-commit-config.yaml"
    config.write_text("user data\n")

    result = run(str(wt), "--preserve-generated-artifacts")

    assert result.returncode == 1 and "not the generated git-hooks.nix file" in result.stderr
    assert_untouched(wt)
    assert config.read_text() == "user data\n"


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"])
def test_generated_precommit_signature_accepts_lf_and_crlf(tmp_path: Path, line_ending: bytes) -> None:
    config = tmp_path / ".pre-commit-config.yaml"
    config.write_bytes(line_ending.join((
        b"# DO NOT MODIFY",
        b"# This file was generated by git-hooks.nix",
        b"{}",
        b"",
    )))

    signature = HELPER.generated_precommit_config_signature(config, config.stat().st_dev)

    assert signature[0][1] == "file"
    assert len(signature[0][7]) == 64


def test_generated_precommit_signature_rejects_untrusted_symlink(tmp_path: Path) -> None:
    target = tmp_path / "outside.yaml"
    target.write_text("# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n")
    config = tmp_path / ".pre-commit-config.yaml"
    config.symlink_to(target)

    with pytest.raises(HELPER.RemovalError, match="not a symlink to a Nix-store"):
        HELPER.generated_precommit_config_signature(config, target.stat().st_dev)


def test_generated_precommit_signature_accepts_marked_nix_store_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store_root = tmp_path / "nix-store"
    store_root.mkdir()
    target = store_root / ("a" * 32 + "-pre-commit-config.json")
    target.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n")
    config = tmp_path / ".pre-commit-config.yaml"
    config.symlink_to(target)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store_root)

    signature = HELPER.generated_precommit_config_signature(config, config.lstat().st_dev)

    assert signature[0][1] == "symlink"
    assert signature[0][7] == str(target)


def test_generated_precommit_signature_rejects_link_swap_while_signing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store_root = tmp_path / "nix-store"
    store_root.mkdir()
    targets = [store_root / (f"{letter}" * 32 + "-pre-commit-config.json") for letter in ("a", "b")]
    for target in targets:
        target.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n")
    config = tmp_path / ".pre-commit-config.yaml"
    config.symlink_to(targets[0])
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store_root)
    original_signature = HELPER.direnv_tree_signature
    swapped = False

    def swap_before_signature(path: Path) -> tuple[tuple[object, ...], ...]:
        nonlocal swapped
        if path == config and not swapped:
            config.unlink()
            config.symlink_to(targets[1])
            swapped = True
        return original_signature(path)

    monkeypatch.setattr(HELPER, "direnv_tree_signature", swap_before_signature)

    with pytest.raises(HELPER.RemovalError, match="changed while signing"):
        HELPER.generated_precommit_config_signature(config, config.lstat().st_dev)

    assert swapped
    assert os.readlink(config) == str(targets[1])
    assert all(target.read_bytes().startswith(b"# DO NOT MODIFY\n") for target in targets)


def test_preserves_nix_store_precommit_symlink_without_touching_target(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    (repo / ".gitignore").write_text(".pre-commit-config.yaml\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore generated config")
    wt = make_worktree(repo, "wt-precommit-store-link")
    store_root = tmp_path / "nix-store"
    store_root.mkdir()
    target = store_root / ("b" * 32 + "-pre-commit-config.json")
    target.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n")
    config = wt / ".pre-commit-config.yaml"
    config.symlink_to(target)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store_root)

    outcome = HELPER.remove(
        str(wt), "main", delete_branch_too=False, lock_name=LOCK,
        allow_unreferenced_reflog=False, expect_branch="task/wt-precommit-store-link",
        preserve_generated_artifacts=True,
    )

    assert not wt.exists()
    assert target.read_bytes() == b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n"
    archive = outcome.preserved_generated_caches[0]
    assert archive.is_symlink()
    assert os.readlink(archive) == str(target)


def test_generated_precommit_signature_rejects_path_swap_before_open(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / ".pre-commit-config.yaml"
    config.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n")
    original = config.with_name("original-config")
    target = tmp_path / "external.yaml"
    target.write_text("external data")
    original_open = os.open
    swapped = False

    def swap_before_open(path: str | bytes | os.PathLike[str] | os.PathLike[bytes], flags: int, *args: object, **kwargs: object) -> int:
        nonlocal swapped
        if Path(path) == config and not swapped:
            config.rename(original)
            config.symlink_to(target)
            swapped = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(HELPER.os, "open", swap_before_open)

    with pytest.raises(HELPER.RemovalError):
        HELPER.generated_precommit_config_signature(config, config.stat().st_dev)

    assert swapped
    assert config.is_symlink()
    assert target.read_text() == "external data"
    assert original.read_bytes().startswith(b"# DO NOT MODIFY\n")


def test_generated_precommit_signature_rejects_content_change_during_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / ".pre-commit-config.yaml"
    config.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n")
    original_read = os.read
    changed = False

    def change_before_read(fd: int, count: int) -> bytes:
        nonlocal changed
        if not changed:
            config.write_bytes(b"# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n[]\n")
            changed = True
        return original_read(fd, count)

    monkeypatch.setattr(HELPER.os, "read", change_before_read)

    with pytest.raises(HELPER.RemovalError, match="changed while reading"):
        HELPER.generated_precommit_config_signature(config, config.stat().st_dev)

    assert changed


def test_discards_only_recognized_generated_caches_after_success(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-discard")
    cache_files = make_generated_caches(wt)

    result = run(str(wt), "--discard-generated-caches", "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert "discarded generated artifact paths" in result.stdout
    assert all(not path.exists() for path in cache_files)
    assert "task/wt-cache-discard" not in git(repo, "branch", "--list")
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_generated_cache_opt_in_does_not_allow_other_ignored_paths(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-and-other")
    cache_files = make_generated_caches(wt)
    keep = wt / "keep.ignored"
    keep.write_text("keep")

    result = run(str(wt), "--discard-generated-caches")

    assert result.returncode == 1 and "keep.ignored" in result.stderr
    assert_untouched(wt)
    assert keep.read_text() == "keep"
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    assert not (Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine").exists()


def test_preserve_generated_artifacts_does_not_allow_other_ignored_paths(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-preserve-and-other")
    cache_files = make_generated_caches(wt)
    keep = wt / "keep.ignored"
    keep.write_text("keep")

    result = run(str(wt), "--preserve-generated-artifacts")

    assert result.returncode == 1 and "keep.ignored" in result.stderr
    assert_untouched(wt)
    assert keep.read_text() == "keep"
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    assert not (Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine").exists()


def test_generated_cache_roots_are_deduplicated() -> None:
    status = [
        (b"!!", b".pytest_cache/"),
        (b"!!", b".pytest_cache/__pycache__/cache.pyc"),
        (b"!!", b"pkg/__pycache__/module.pyc"),
        (b"!!", b"pkg/__pycache__/nested/__pycache__/inner.pyc"),
        (b"!!", b".direnv/flake-inputs/__pycache__/input.pyc"),
    ]
    assert HELPER.generated_cache_candidates(status) == (b".pytest_cache", b"pkg/__pycache__")


def test_generated_build_output_candidates_are_exact() -> None:
    status = [
        (b"!!", b"result"),
        (b"??", b"rust/target/debug/file"),
        (b"!!", b"rust/other/file"),
        (b"!!", b".direnv/rust/target/cache"),
        (b"??", b"result-copy"),
    ]
    assert HELPER.generated_cache_candidates(status, caches=False, build_outputs=True) == (
        b"result", b"rust/target",
    )


def test_generated_cache_option_leaves_direnv_to_its_existing_policy(repo: Path) -> None:
    (repo / ".gitignore").write_text(".direnv/\n.pytest_cache/\n.ruff_cache/\n__pycache__/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore cache paths")
    wt = make_worktree(repo, "wt-cache-direnv")
    cache = wt / ".direnv" / "__pycache__" / "state.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"preserve")

    result = run(str(wt), "--discard-generated-caches")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    archive_line = next(line for line in result.stdout.splitlines() if line.startswith("preserved .direnv at "))
    archive = Path(archive_line.removeprefix("preserved .direnv at "))
    assert (archive / "__pycache__" / "state.pyc").read_bytes() == b"preserve"


def test_generated_cache_symlink_refuses_without_touching_target(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-symlink")
    cache = wt / ".pytest_cache"
    cache.mkdir()
    target = repo / "external-cache.txt"
    target.write_text("preserve")
    (cache / "linked").symlink_to(target)

    result = run(str(wt), "--discard-generated-caches")

    assert result.returncode == 1 and "symlink or special file" in result.stderr
    assert_untouched(wt)
    assert target.read_text() == "preserve"


def test_generated_cache_nested_git_repo_refuses(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-nested-git")
    nested = wt / ".ruff_cache" / "nested" / ".git"
    nested.mkdir(parents=True)
    (nested / "HEAD").write_text("ref: refs/heads/main\n")

    result = run(str(wt), "--discard-generated-caches")

    assert result.returncode == 1 and "nested Git repository" in result.stderr
    assert_untouched(wt)
    assert nested.exists()


def test_generated_cache_refuses_if_open_handles_cannot_be_checked(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-open-unknown")
    cache_files = make_generated_caches(wt)
    monkeypatch.setattr(HELPER, "lsof_open_paths", lambda paths: None)

    with pytest.raises(HELPER.RemovalError, match="could not verify open handles"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-open-unknown",
            discard_generated_caches=True,
        )

    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)


def test_generated_cache_refuses_when_open_handles_exist(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-open")
    cache_files = make_generated_caches(wt)
    monkeypatch.setattr(HELPER, "lsof_open_paths", lambda paths: {"123"})

    with pytest.raises(HELPER.RemovalError, match="processes still have generated cache files open"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-open",
            discard_generated_caches=True,
        )

    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)


def test_generated_cache_refuses_tracked_entries(repo: Path) -> None:
    add_generated_cache_ignores(repo)
    tracked = repo / ".pytest_cache" / "tracked"
    tracked.parent.mkdir()
    tracked.write_text("tracked")
    git(repo, "add", "-f", ".pytest_cache/tracked")
    git(repo, "commit", "--quiet", "-m", "track cache fixture")
    wt = make_worktree(repo, "wt-cache-tracked")
    extra = wt / ".pytest_cache" / "untracked"
    extra.write_text("preserve")

    result = run(str(wt), "--discard-generated-caches")

    assert result.returncode == 1 and "contains tracked files" in result.stderr
    assert_untouched(wt)
    assert (wt / ".pytest_cache" / "tracked").read_text() == "tracked"
    assert extra.read_text() == "preserve"


def test_generated_cache_refuses_mount_points(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-mount")
    cache_files = make_generated_caches(wt)
    cache_root = wt / ".pytest_cache"
    monkeypatch.setattr(HELPER, "mount_points", lambda: (cache_root.resolve(),))

    with pytest.raises(HELPER.RemovalError, match="mount point"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-mount",
            discard_generated_caches=True,
        )

    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)


def test_generated_caches_restore_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-remove-refused")
    cache_files = make_generated_caches(wt)
    bin_dir = make_git_wrapper(tmp_path, refuse_remove=True)

    result = run_with_git_wrapper(wt, bin_dir, "--discard-generated-caches")

    assert result.returncode == 1 and "simulated refusal" in result.stderr
    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_preserved_generated_config_restores_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    (repo / ".gitignore").write_text(".pre-commit-config.yaml\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore generated config")
    wt = make_worktree(repo, "wt-precommit-remove-refused")
    config = wt / ".pre-commit-config.yaml"
    config.write_text(
        '# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n',
        encoding="utf-8",
    )
    expected = config.read_bytes()
    bin_dir = make_git_wrapper(tmp_path, refuse_remove=True)

    result = run_with_git_wrapper(wt, bin_dir, "--preserve-generated-artifacts")

    assert result.returncode == 1 and "simulated refusal" in result.stderr
    assert_untouched(wt)
    assert config.read_bytes() == expected
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_generated_caches_restore_when_status_changes_after_quarantine(repo: Path, tmp_path: Path) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-status-race")
    cache_files = make_generated_caches(wt)
    late = wt / "keep.ignored"
    hook = f"Path({str(late)!r}).write_text('keep')"
    bin_dir = make_git_wrapper(tmp_path, hook_on_second_status=True, hook=hook)

    result = run_with_git_wrapper(wt, bin_dir, "--discard-generated-caches")

    assert result.returncode == 1 and "worktree changed after removing generated state" in result.stderr
    assert_untouched(wt)
    assert late.read_text() == "keep"
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)


def test_generated_caches_restore_after_partial_quarantine_failure(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-partial-move")
    cache_files = make_generated_caches(wt)
    original = HELPER.no_replace_rename

    def fail_second_cache(source: Path, destination: Path) -> None:
        if destination.name == "generated-cache-001":
            raise OSError("simulated cache move failure")
        original(source, destination)

    monkeypatch.setattr(HELPER, "no_replace_rename", fail_second_cache)
    with pytest.raises(OSError, match="simulated cache move failure"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-partial-move",
            discard_generated_caches=True,
        )

    assert_untouched(wt)
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_generated_cache_mutation_during_quarantine_is_restored(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-mutated-move")
    cache_files = make_generated_caches(wt)
    late = wt / ".pytest_cache" / "late-entry"
    original = HELPER.no_replace_rename

    def mutate_after_move(source: Path, destination: Path) -> None:
        original(source, destination)
        if destination.name == "generated-cache-000":
            (destination / "late-entry").write_text("preserve")

    monkeypatch.setattr(HELPER, "no_replace_rename", mutate_after_move)
    with pytest.raises(HELPER.RemovalError, match="changed during quarantine"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-mutated-move",
            discard_generated_caches=True,
        )

    assert_untouched(wt)
    assert late.read_text() == "preserve"
    assert all(path.read_bytes() == b"generated cache" for path in cache_files)
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_failed_cache_purge_retains_manifest_and_recovery_data(
    repo: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-purge-refused")
    make_generated_caches(wt)
    monkeypatch.setattr(HELPER, "purge_generated_cache", lambda *args: "simulated purge failure")

    outcome = HELPER.remove(
        str(wt), "main", delete_branch_too=False, lock_name=LOCK,
        allow_unreferenced_reflog=False, expect_branch="task/wt-cache-purge-refused",
        discard_generated_caches=True,
    )

    assert not wt.exists()
    assert outcome.discarded_generated_caches == ()
    assert len(outcome.preserved_generated_caches) == 3
    for archive in outcome.preserved_generated_caches:
        assert any(path.read_bytes() == b"generated cache" for path in archive.rglob("*" ) if path.is_file())
    operation_dir = outcome.preserved_generated_caches[0].parent
    manifest = json.loads((operation_dir / "manifest.json").read_text())
    assert manifest["phase"] == "completed_preserved"
    assert all(item["purge_state"] == "preserved" for item in manifest["generated_caches"])


def test_cache_purge_manifest_records_git_removal_before_purging(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-purge-journal")
    make_generated_caches(wt)
    original = HELPER.write_manifest

    def fail_after_removal(transaction: HELPER.RemovalTransaction, phase: str, *, create: bool = False) -> None:
        if phase == "worktree_removed":
            raise OSError("simulated interruption after Git removal")
        original(transaction, phase, create=create)

    monkeypatch.setattr(HELPER, "write_manifest", fail_after_removal)
    with pytest.raises(OSError, match="simulated interruption"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-purge-journal",
            discard_generated_caches=True,
        )

    assert not wt.exists()
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    operation_dir = next(quarantine.iterdir())
    manifest = json.loads((operation_dir / "manifest.json").read_text())
    assert manifest["phase"] == "recovery_required"
    assert all(Path(item["quarantine_path"]).exists() for item in manifest["generated_caches"])


def test_cache_purge_start_failure_keeps_journal_and_quarantine(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_generated_cache_ignores(repo)
    wt = make_worktree(repo, "wt-cache-purge-start-failure")
    make_generated_caches(wt)
    original = HELPER.write_manifest

    def fail_before_purge(transaction: HELPER.RemovalTransaction, phase: str, *, create: bool = False) -> None:
        if phase == "generated_cache_0_purge_started":
            raise OSError("simulated failure before cache purge")
        original(transaction, phase, create=create)

    monkeypatch.setattr(HELPER, "write_manifest", fail_before_purge)
    with pytest.raises(OSError, match="simulated failure before cache purge"):
        HELPER.remove(
            str(wt), "main", delete_branch_too=False, lock_name=LOCK,
            allow_unreferenced_reflog=False, expect_branch="task/wt-cache-purge-start-failure",
            discard_generated_caches=True,
        )

    assert not wt.exists()
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    operation_dir = next(quarantine.iterdir())
    manifest = json.loads((operation_dir / "manifest.json").read_text())
    assert manifest["phase"] == "recovery_required"
    assert all(Path(item["quarantine_path"]).exists() for item in manifest["generated_caches"])


def test_removes_canonical_db_symlink_without_touching_database(repo: Path) -> None:
    database = add_canonical_database(repo, b"preserve these bytes")
    wt = make_worktree(repo, "wt-db")
    link_canonical_database(repo, wt)

    result = run(str(wt), "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert database.read_bytes() == b"preserve these bytes"
    assert "task/wt-db" not in git(repo, "branch", "--list")


def test_uses_main_branch_not_worktree_list_order(repo: Path, tmp_path: Path) -> None:
    database = add_canonical_database(repo)
    other = make_worktree(repo, "wt-other-db")
    other_db = other / "cultura.db"
    other_db.write_bytes(b"not the canonical database")
    wt = make_worktree(repo, "wt-main-last")
    link_canonical_database(repo, wt)
    bin_dir = make_git_wrapper(tmp_path, reverse_worktrees=True)

    result = run_with_git_wrapper(wt, bin_dir, "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert database.read_bytes() == b"canonical database"
    assert other_db.read_bytes() == b"not the canonical database"


def test_refuses_removing_main_branch_worktree_without_session_owner(repo: Path) -> None:
    wt = make_worktree(repo, "wt-main-branch")
    git(repo, "checkout", "--quiet", "--detach")
    git(wt, "checkout", "--quiet", "main")

    result = run(str(wt))

    assert result.returncode == 1 and "session-owner metadata" in result.stderr
    assert_untouched(wt)
    assert repo.exists()
    assert git(repo, "branch", "--show-current") == ""


def test_refuses_duplicate_registered_main_worktrees(repo: Path, tmp_path: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-duplicate-main")
    link = link_canonical_database(repo, wt)
    bin_dir = make_git_wrapper(tmp_path, duplicate_main=True)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "not clean" in result.stderr
    assert link.is_symlink() and link.resolve() == database.resolve()
    assert database.read_bytes() == b"canonical database"


def test_refuses_database_symlink_without_registered_main_worktree(repo: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-no-registered-main")
    link = link_canonical_database(repo, wt)
    git(repo, "checkout", "--quiet", "--detach")

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert link.is_symlink() and link.resolve() == database.resolve()
    assert database.read_bytes() == b"canonical database"


@pytest.mark.parametrize("main_kind", ["missing", "directory", "symlink"])
def test_refuses_when_main_database_is_not_a_regular_file(repo: Path, main_kind: str) -> None:
    (repo / ".gitignore").write_text("cultura.db\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore database")
    database = repo / "cultura.db"
    backing = repo / "database-backing"
    if main_kind == "directory":
        database.mkdir()
    elif main_kind == "symlink":
        backing.write_bytes(b"database backing")
        database.symlink_to(backing)
    wt = make_worktree(repo, f"wt-main-{main_kind}")
    link = wt / "cultura.db"
    link.symlink_to(database)

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert link.is_symlink()
    if main_kind == "missing":
        assert not database.exists()
    elif main_kind == "directory":
        assert database.is_dir()
    else:
        assert database.is_symlink() and backing.read_bytes() == b"database backing"


def test_refuses_regular_ignored_worktree_database(repo: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-regular-db")
    local_data = wt / "cultura.db"
    local_data.write_bytes(b"do not delete")

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert local_data.read_bytes() == b"do not delete"
    assert database.read_bytes() == b"canonical database"


@pytest.mark.parametrize("target_kind", ["wrong", "dangling"])
def test_refuses_noncanonical_database_symlink(repo: Path, tmp_path: Path, target_kind: str) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, f"wt-db-{target_kind}")
    external = tmp_path / "external.db"
    external.write_bytes(b"external")
    link = wt / "cultura.db"
    link.symlink_to(external if target_kind == "wrong" else tmp_path / "missing.db")

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    assert link.is_symlink()
    assert database.read_bytes() == b"canonical database"
    assert external.read_bytes() == b"external"


def test_refuses_other_ignored_paths_alongside_canonical_db_symlink(repo: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-db-and-extra")
    link = link_canonical_database(repo, wt)
    extra = wt / "keep.ignored"
    extra.write_text("keep")

    result = run(str(wt))

    assert result.returncode == 1 and "keep.ignored" in result.stderr
    assert link.is_symlink() and link.resolve() == database.resolve()
    assert extra.read_text() == "keep"
    assert database.read_bytes() == b"canonical database"


def test_status_parser_preserves_special_ignored_paths(repo: Path) -> None:
    (repo / ".gitignore").write_text("*.ignored\ncultura.db/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore special names")
    wt = make_worktree(repo, "wt-special-names")
    names = ["line\nbreak.ignored", "tab\tname.ignored", 'quote"name.ignored', "back\\slash.ignored"]
    for name in names:
        (wt / name).write_text("keep")
    (wt / "cultura.db").mkdir()
    (wt / "cultura.db" / "child").write_text("keep nested data")

    result = run(str(wt))

    assert result.returncode == 1 and "not clean" in result.stderr
    for name in names:
        assert (wt / name).read_text() == "keep"
    assert (wt / "cultura.db" / "child").read_text() == "keep nested data"


@pytest.mark.parametrize("replacement", ["file", "directory", "dangling-symlink"])
def test_refuses_worktree_db_symlink_replaced_before_final_validation(
    repo: Path, tmp_path: Path, replacement: str,
) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, f"wt-link-race-{replacement}")
    link = link_canonical_database(repo, wt)
    hook = {
        "file": f"Path({str(link)!r}).unlink(); Path({str(link)!r}).write_text('new data')",
        "directory": f"Path({str(link)!r}).unlink(); Path({str(link)!r}).mkdir()",
        "dangling-symlink": f"Path({str(link)!r}).unlink(); Path({str(link)!r}).symlink_to({str(tmp_path / 'missing-target')!r})",
    }[replacement]
    bin_dir = make_git_wrapper(tmp_path, trigger=("rev-parse", "HEAD"), hook=hook)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "cultura.db symlink" in result.stderr
    assert database.read_bytes() == b"canonical database"
    if replacement == "file":
        assert link.read_text() == "new data"
    elif replacement == "directory":
        assert link.is_dir()
    else:
        assert link.is_symlink() and not link.exists()


@pytest.mark.parametrize("main_kind", ["missing", "directory", "symlink"])
def test_refuses_main_database_type_change_before_final_validation(
    repo: Path, tmp_path: Path, main_kind: str,
) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, f"wt-main-race-{main_kind}")
    link = link_canonical_database(repo, wt)
    saved = tmp_path / f"saved-main-db-{main_kind}"
    replacement = tmp_path / f"replacement-main-db-{main_kind}"
    replacement.write_bytes(b"replacement")
    if main_kind == "missing":
        hook = f"Path({str(database)!r}).rename({str(saved)!r})"
    elif main_kind == "directory":
        hook = f"Path({str(database)!r}).rename({str(saved)!r}); Path({str(database)!r}).mkdir()"
    else:
        hook = f"Path({str(database)!r}).unlink(); Path({str(database)!r}).symlink_to({str(replacement)!r})"
    bin_dir = make_git_wrapper(tmp_path, trigger=("rev-parse", "HEAD"), hook=hook)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "cultura.db symlink" in result.stderr
    assert link.is_symlink() and os.readlink(link) == str(database)
    if main_kind == "missing":
        assert not database.exists() and saved.read_bytes() == b"canonical database"
    elif main_kind == "directory":
        assert database.is_dir() and saved.read_bytes() == b"canonical database"
    else:
        assert database.is_symlink() and replacement.read_bytes() == b"replacement"


def test_restores_database_symlink_when_final_status_finds_new_file(repo: Path, tmp_path: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-late-file")
    link = link_canonical_database(repo, wt)
    late = wt / "late.ignored"
    bin_dir = make_git_wrapper(tmp_path, hook_on_second_status=True, hook=f"Path({str(late)!r}).write_text('keep')")

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "worktree changed" in result.stderr
    assert link.is_symlink() and link.resolve() == database.resolve()
    assert late.read_text() == "keep"
    assert database.read_bytes() == b"canonical database"


@pytest.mark.parametrize("replacement", ["file", "directory", "dangling-symlink"])
def test_does_not_overwrite_path_occupied_during_database_link_restore(
    repo: Path, tmp_path: Path, replacement: str,
) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, f"wt-restore-collision-{replacement}")
    link = link_canonical_database(repo, wt)
    hook = {
        "file": f"Path({str(link)!r}).write_text('preserve')",
        "directory": f"Path({str(link)!r}).mkdir()",
        "dangling-symlink": f"Path({str(link)!r}).symlink_to({str(tmp_path / 'dangling')!r})",
    }[replacement]
    bin_dir = make_git_wrapper(tmp_path, hook_on_second_status=True, hook=hook)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "path is occupied" in result.stderr
    assert str(database) in result.stderr
    assert database.read_bytes() == b"canonical database"
    if replacement == "file":
        assert link.read_text() == "preserve"
    elif replacement == "directory":
        assert link.is_dir()
    else:
        assert link.is_symlink() and not link.exists()


def test_restores_database_symlink_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    database = add_canonical_database(repo)
    wt = make_worktree(repo, "wt-db-remove-refusal")
    link = link_canonical_database(repo, wt)
    bin_dir = make_git_wrapper(tmp_path, refuse_remove=True)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "simulated refusal" in result.stderr
    assert link.is_symlink() and link.resolve() == database.resolve()
    assert database.read_bytes() == b"canonical database"


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_refuses_hidden_modifications(repo: Path, flag: str) -> None:
    wt = make_worktree(repo, "wt8")
    git(wt, "update-index", flag, "a.txt")
    (wt / "a.txt").write_text("edited and hidden")
    result = run(str(wt))
    assert result.returncode == 1 and "can hide edits" in result.stderr
    assert (wt / "a.txt").read_text() == "edited and hidden"


def test_refuses_unintegrated_commits(repo: Path) -> None:
    wt = make_worktree(repo, "wt9")
    commit(wt, "b.txt", "wip")
    result = run(str(wt))
    assert result.returncode == 1 and "not contained" in result.stderr
    assert_untouched(wt)


def test_refuses_reflog_only_commit_after_returning_to_owned_branch(repo: Path) -> None:
    wt = make_worktree(repo, "wt10")
    git(wt, "checkout", "--quiet", "--detach")
    lost = commit(wt, "lost.txt", "only in reflog")
    git(wt, "checkout", "--quiet", "task/wt10")
    result = run(str(wt))
    assert result.returncode == 1 and lost[:12] in result.stderr
    assert_untouched(wt)
    assert run(str(wt), "--allow-unreferenced-reflog").returncode == 0


def test_refuses_per_worktree_refs_and_in_progress_state(repo: Path) -> None:
    wt = make_worktree(repo, "wt11")
    git(wt, "update-ref", "refs/worktree/keep", "HEAD")
    result = run(str(wt))
    assert result.returncode == 1 and "per-worktree" in result.stderr
    git(wt, "update-ref", "-d", "refs/worktree/keep")
    (admin_of(wt) / "MERGE_HEAD").write_text(git(wt, "rev-parse", "HEAD") + "\n")
    result = run(str(wt))
    assert result.returncode == 1 and "MERGE_HEAD" in result.stderr
    assert_untouched(wt)


def test_refuses_main_worktree(repo: Path) -> None:
    result = run(str(repo))
    assert result.returncode == 1 and "main worktree" in result.stderr


def test_refuses_symlink_to_unrelated_directory(repo: Path) -> None:
    wt = make_worktree(repo, "wt12")
    elsewhere = repo.parent / "elsewhere"
    elsewhere.mkdir()
    (wt / ".git").unlink()
    os.symlink(str(elsewhere), wt / ".git")
    assert run(str(wt)).returncode != 0 and wt.exists()


def test_refuses_symlink_to_sibling_admin_dir(repo: Path) -> None:
    wt, other = make_worktree(repo, "wt13"), make_worktree(repo, "wt14")
    (wt / ".git").unlink()
    os.symlink(str(admin_of(other)), wt / ".git")
    result = run(str(wt))
    assert result.returncode != 0 and wt.exists() and other.exists()


def test_refuses_gitfile_naming_wrong_admin_dir(repo: Path) -> None:
    wt, other = make_worktree(repo, "wt15", symlink=False), make_worktree(repo, "wt16", symlink=False)
    (wt / ".git").write_text(f"gitdir: {admin_of(other)}\n")
    result = run(str(wt))
    assert result.returncode != 0 and wt.exists()


def test_refuses_edited_back_pointer(repo: Path) -> None:
    wt = make_worktree(repo, "wt17")
    (admin_of(wt) / "gitdir").write_text(str(repo.parent / "elsewhere" / ".git") + "\n")
    result = run(str(wt))
    assert result.returncode != 0 and wt.exists()


def test_refuses_locked_worktree_before_changing_anything(repo: Path) -> None:
    wt = make_worktree(repo, "wt18")
    git(repo, "worktree", "lock", str(wt))
    for args in ((), ("--dry-run",)):
        result = run(str(wt), *args)
        assert result.returncode == 1 and "locked" in result.stderr
    assert_untouched(wt)


def test_refuses_submodule_worktree(repo: Path, tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    git(sub, "init", "--quiet", "-b", "main")
    git(sub, "config", "user.name", "F")
    git(sub, "config", "user.email", "f@example.invalid")
    commit(sub, "s.txt", "sub")
    git(repo, "-c", "protocol.file.allow=always", "submodule", "add", "--quiet", str(sub), "vendor")
    git(repo, "commit", "--quiet", "-m", "add submodule")
    wt = make_worktree(repo, "wt19")
    result = run(str(wt))
    assert result.returncode == 1 and "submodule" in result.stderr
    assert_untouched(wt)


def test_refuses_when_process_cwd_is_inside(repo: Path) -> None:
    if shutil.which("lsof") is None:
        pytest.skip("lsof unavailable")
    wt = make_worktree(repo, "wt20")
    holder = subprocess.Popen(["sleep", "30"], cwd=wt)
    try:
        result = run(str(wt))
        assert result.returncode == 1 and "cwd inside" in result.stderr
        assert_untouched(wt)
    finally:
        holder.kill()
        holder.wait()


def test_refuses_when_lock_is_held_and_keeps_it(repo: Path) -> None:
    wt = make_worktree(repo, "wt21")
    lock = repo / ".git" / LOCK
    lock.mkdir()
    result = run(str(wt))
    assert result.returncode == 1 and "held by another actor" in result.stderr
    assert lock.exists()
    assert_untouched(wt)


def test_lock_released_after_failed_removal_and_symlink_restored(repo: Path) -> None:
    wt = make_worktree(repo, "wt22")
    (wt / "u.txt").write_text("u")
    assert run(str(wt)).returncode == 1
    assert not (repo / ".git" / LOCK).exists()
    assert_untouched(wt)


def test_rolls_back_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    wt = make_worktree(repo, "wt23")
    real_git = shutil.which("git")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    wrapper = bin_dir / "git"
    wrapper.write_text(f'#!/bin/sh\nfor a in "$@"; do [ "$a" = remove ] && {{ echo "fatal: simulated refusal" >&2; exit 128; }}; done\nexec {real_git} "$@"\n')
    wrapper.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    result = run(str(wt), env=env)
    assert result.returncode == 1 and "refused" in result.stderr
    assert_untouched(wt)
    assert not (repo / ".git" / LOCK).exists()


def test_missing_base_ref(repo: Path) -> None:
    wt = make_worktree(repo, "wt24")
    result = run(str(wt), "--base", "nope")
    assert result.returncode == 1
    assert_untouched(wt)
    assert run(str(wt), "--base=--upload-pack=x").returncode == 1


def test_delete_branch_refused_when_checked_out_elsewhere(repo: Path) -> None:
    wt = make_worktree(repo, "wt25")
    twin = repo.parent / "twin"
    git(repo, "worktree", "add", "--quiet", "--force", str(twin), "task/wt25")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 1 and "branch kept" in result.stderr
    assert not wt.exists()
    assert "task/wt25" in git(repo, "branch", "--list")


def test_fails_without_git_annex_when_repo_uses_it(repo: Path, tmp_path: Path) -> None:
    wt = make_worktree(repo, "wt26")
    git(repo, "config", "filter.annex.process", "git-annex filter-process")
    bin_dir = tmp_path / "nogitannex"
    bin_dir.mkdir()
    os.symlink(shutil.which("git"), bin_dir / "git")
    result = run(str(wt), env={"PATH": str(bin_dir), "HOME": str(tmp_path), "GIT_CONFIG_GLOBAL": os.devnull, "OPENCODE_SESSION_ID": SESSION})
    assert result.returncode == 1 and "git-annex is not on PATH" in result.stderr
    assert_untouched(wt)


def test_annex_call_order_and_gitfile_during_removal(repo: Path, tmp_path: Path) -> None:
    wt = make_worktree(repo, "wt27", symlink=False)
    git(repo, "config", "filter.annex.process", "git-annex filter-process")
    log = tmp_path / "annex.log"
    bin_dir = tmp_path / "stub"
    bin_dir.mkdir()
    stub = bin_dir / "git-annex"
    stub.write_text(
        "#!/bin/sh\n"
        f'if [ -L "{wt}/.git" ]; then k=symlink; else k=file; fi\n'
        f'echo "$1 $k" >> "{log}"\n'
        # emulate git-annex: it re-creates the symlink when it operates in the worktree
        f'if [ "$1" = restage ] && [ -f "{wt}/.git" ]; then a=$(sed "s/^gitdir: //" "{wt}/.git"); rm "{wt}/.git"; ln -s "$a" "{wt}/.git"; fi\n'
    )
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
    result = run(str(wt), env=env)
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == ["restage file"]
    assert not wt.exists()


def test_normalizes_annex_recreated_git_symlink_after_final_status(repo: Path, tmp_path: Path) -> None:
    wt = make_worktree(repo, "wt-annex-status-symlink", symlink=False)
    git(repo, "config", "filter.annex.process", "git-annex filter-process")
    admin = admin_of(wt)
    bin_dir = make_git_wrapper(
        tmp_path,
        hook_on_second_status=True,
        hook=(
            f"dotgit = Path({str(wt / '.git')!r})\n"
            "if dotgit.is_file():\n"
            "    admin = Path(dotgit.read_text().removeprefix('gitdir: ').strip()).resolve()\n"
            "    dotgit.unlink()\n"
            "    dotgit.symlink_to(admin)\n"
        ),
    )
    annex_stub = bin_dir / "git-annex"
    annex_stub.write_text("#!/bin/sh\nexit 0\n")
    annex_stub.chmod(0o755)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert not admin.exists()


def test_annex_symlink_from_final_status_is_restored_when_git_refuses_removal(
    repo: Path, tmp_path: Path,
) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-annex-status-refusal", symlink=False)
    git(repo, "config", "filter.annex.process", "git-annex filter-process")
    admin = admin_of(wt)
    user_state = wt / ".direnv" / "user-state.txt"
    user_state.parent.mkdir()
    user_state.write_text("preserve")
    bin_dir = make_git_wrapper(
        tmp_path,
        hook_on_second_status=True,
        refuse_remove=True,
        hook=(
            f"dotgit = Path({str(wt / '.git')!r})\n"
            "if dotgit.is_file():\n"
            "    admin = Path(dotgit.read_text().removeprefix('gitdir: ').strip()).resolve()\n"
            "    dotgit.unlink()\n"
            "    dotgit.symlink_to(admin)\n"
        ),
    )
    annex_stub = bin_dir / "git-annex"
    annex_stub.write_text("#!/bin/sh\nexit 0\n")
    annex_stub.chmod(0o755)

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "simulated refusal" in result.stderr
    assert_untouched(wt, symlink=True)
    assert (wt / ".git").resolve() == admin
    assert user_state.read_text() == "preserve"
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_parse_linux_mountinfo_detects_same_device_mountpoint() -> None:
    mounts = HELPER.parse_linux_mountinfo(
        "36 25 0:33 / /private/cache/flake-inputs rw,relatime shared:1 - apfs /dev/disk1 rw\n"
    )
    assert mounts == (Path("/private/cache/flake-inputs"),)


def test_parse_darwin_mount_output_preserves_escaped_spaces() -> None:
    mounts = HELPER.parse_darwin_mount_output(
        "/dev/disk1 on / (apfs, local)\n/dev/disk2 on /Volumes/Cache\\040Disk (apfs, local)\n"
    )
    assert mounts == (Path("/"), Path("/Volumes/Cache Disk"))


def test_nix_direnv_validator_rejects_same_device_nested_mountpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = tmp_path / "nix-store"
    store.mkdir()
    cache = tmp_path / "worktree" / ".direnv"
    make_nix_direnv_cache(cache.parent, store)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store)
    monkeypatch.setattr(HELPER, "mount_points", lambda: (cache / "flake-inputs",))

    assert HELPER.nix_direnv_cache_signature(cache) is None


def test_quarantines_unknown_direnv_and_removes_worktree(repo: Path, tmp_path: Path) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-unknown")
    user_file = wt / ".direnv" / "user-state.txt"
    user_file.parent.mkdir()
    user_file.write_text("preserve this state")

    result = run(str(wt), "--delete-branch")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    archive_line = next(line for line in result.stdout.splitlines() if line.startswith("preserved .direnv at "))
    archive = Path(archive_line.removeprefix("preserved .direnv at "))
    assert (archive / "user-state.txt").read_text() == "preserve this state"
    manifest = json.loads((archive.parent / "manifest.json").read_text())
    assert manifest["phase"] == "completed_preserved"
    assert "task/wt-direnv-unknown" not in git(repo, "branch", "--list")


def test_dry_run_reports_direnv_policy_without_moving_it(repo: Path, tmp_path: Path) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-dry-run")
    user_file = wt / ".direnv" / "user-state.txt"
    user_file.parent.mkdir()
    user_file.write_text("keep")

    result = run(str(wt), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert ".direnv would be quarantine and retain" in result.stdout
    assert user_file.read_text() == "keep"
    assert not (Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine").exists()


def test_discards_verified_nix_direnv_cache_after_success(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-discard")
    store = tmp_path / "nix-store"
    store.mkdir()
    make_nix_direnv_cache(wt, store)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store)
    monkeypatch.setattr(HELPER, "mount_points", lambda: ())
    monkeypatch.setattr(HELPER, "lsof_open_paths", lambda paths: set())

    outcome = HELPER.remove(
        str(wt), "main", delete_branch_too=True, lock_name=LOCK,
        allow_unreferenced_reflog=False, expect_branch="task/wt-direnv-discard", discard_direnv_cache=True,
    )

    assert outcome.discarded_direnv
    assert outcome.preserved_direnv is None
    assert not wt.exists()
    assert (store / f"{'a' * 32}-source").is_dir()
    assert (store / f"{'c' * 32}-nix-shell-env").is_dir()
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []
    assert "task/wt-direnv-discard" not in git(repo, "branch", "--list")


def test_discard_flag_keeps_unknown_direnv_instead_of_deleting(repo: Path, tmp_path: Path) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-unknown-discard")
    user_file = wt / ".direnv" / "user-state.txt"
    user_file.parent.mkdir()
    user_file.write_text("preserve this state")

    result = run(str(wt), "--discard-direnv-cache")

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    archive_line = next(line for line in result.stdout.splitlines() if line.startswith("preserved .direnv at "))
    archive = Path(archive_line.removeprefix("preserved .direnv at "))
    assert (archive / "user-state.txt").read_text() == "preserve this state"
    assert "layout is not a verified Nix-direnv" in result.stderr


def test_keeps_verified_direnv_cache_when_open_handles_cannot_be_checked(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-open-handles")
    store = tmp_path / "nix-store"
    store.mkdir()
    make_nix_direnv_cache(wt, store)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store)
    monkeypatch.setattr(HELPER, "mount_points", lambda: ())
    monkeypatch.setattr(HELPER, "lsof_open_paths", lambda paths: None)

    outcome = HELPER.remove(
        str(wt), "main", delete_branch_too=False, lock_name=LOCK,
        allow_unreferenced_reflog=False, expect_branch="task/wt-direnv-open-handles", discard_direnv_cache=True,
    )

    assert not wt.exists()
    assert not outcome.discarded_direnv
    assert outcome.preserved_direnv is not None
    assert (outcome.preserved_direnv / f"flake-profile-{'b' * 40}.rc").is_file()


def test_cache_mutation_after_validation_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = tmp_path / "nix-store"
    store.mkdir()
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    cache = make_nix_direnv_cache(worktree, store)
    monkeypatch.setattr(HELPER, "NIX_STORE_ROOT", store)
    monkeypatch.setattr(HELPER, "mount_points", lambda: ())
    signature = HELPER.nix_direnv_cache_signature(cache)
    assert signature is not None
    reload_script = cache / "bin" / "nix-direnv-reload"
    reload_script.write_text("#!/bin/sh\necho changed\n")

    reason = HELPER.purge_direnv_cache(cache, signature)

    assert reason is not None and "changed after inspection" in reason
    assert reload_script.exists()
    assert (cache / f"flake-profile-{'b' * 40}.rc").exists()


def test_direnv_exception_does_not_allow_other_ignored_paths(repo: Path) -> None:
    (repo / ".gitignore").write_text(".direnv/\nkeep.ignored\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "--quiet", "-m", "ignore runtime files")
    wt = make_worktree(repo, "wt-direnv-and-other")
    (wt / ".direnv").mkdir()
    (wt / ".direnv" / "state.txt").write_text("preserve")
    (wt / "keep.ignored").write_text("preserve")

    result = run(str(wt))

    assert result.returncode == 1 and "keep.ignored" in result.stderr
    assert (wt / ".direnv" / "state.txt").read_text() == "preserve"
    assert (wt / "keep.ignored").read_text() == "preserve"
    assert not (Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine").exists()


def test_restores_direnv_and_db_link_when_git_refuses_removal(repo: Path, tmp_path: Path) -> None:
    add_direnv_ignore(repo, include_database=True)
    database = repo / "cultura.db"
    database.write_bytes(b"canonical database")
    wt = make_worktree(repo, "wt-direnv-db-refused")
    link_canonical_database(repo, wt)
    user_file = wt / ".direnv" / "user-state.txt"
    user_file.parent.mkdir()
    user_file.write_text("keep")
    bin_dir = make_git_wrapper(tmp_path, refuse_remove=True)

    result = run_with_git_wrapper(wt, bin_dir, "--delete-branch")

    assert result.returncode == 1 and "refused" in result.stderr
    assert wt.exists() and (wt / ".direnv" / "user-state.txt").read_text() == "keep"
    assert (wt / "cultura.db").is_symlink() and (wt / "cultura.db").resolve() == database.resolve()
    assert database.read_bytes() == b"canonical database"
    assert (wt / ".git").is_symlink()
    quarantine = Path(os.environ["XDG_STATE_HOME"]) / repo.name / "worktrees" / ".removal-quarantine"
    assert list(quarantine.iterdir()) == []


def test_does_not_overwrite_direnv_recreated_during_refusal(repo: Path, tmp_path: Path) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-race")
    original = wt / ".direnv" / "original.txt"
    original.parent.mkdir()
    original.write_text("original")
    recreated = wt / ".direnv" / "recreated.txt"
    hook = f"Path({str(recreated.parent)!r}).mkdir(); Path({str(recreated)!r}).write_text('new')"
    bin_dir = make_git_wrapper(
        tmp_path, trigger=("worktree", "remove", str(wt)), hook=hook, refuse_remove=True,
    )

    result = run_with_git_wrapper(wt, bin_dir)

    assert result.returncode == 1 and "refused" in result.stderr
    assert recreated.read_text() == "new"
    recovery = [line for line in result.stderr.splitlines() if line.startswith("warning: preserved recovery state at ")]
    assert recovery
    operation_dir = Path(recovery[0].removeprefix("warning: preserved recovery state at "))
    assert (operation_dir / ".direnv" / "original.txt").read_text() == "original"


def test_unresolved_transaction_refuses_implicit_retry(repo: Path) -> None:
    add_direnv_ignore(repo)
    wt = make_worktree(repo, "wt-direnv-interrupted")
    user_file = wt / ".direnv" / "state.txt"
    user_file.parent.mkdir()
    user_file.write_text("keep")
    target = HELPER.inspect(wt)
    quarantine = HELPER.state_quarantine_root(target)
    operation_dir = quarantine / "interrupted-operation"
    operation_dir.mkdir(parents=True, mode=0o700)
    (operation_dir / "manifest.json").write_text(
        json.dumps({"worktree": str(wt.resolve()), "phase": "direnv_quarantined"})
    )

    result = run(str(wt))

    assert result.returncode == 1 and "interrupted removal transaction" in result.stderr
    assert user_file.read_text() == "keep"
    assert wt.exists()
