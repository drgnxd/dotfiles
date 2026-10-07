from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("safe-worktree-remove.py")
LOCK = "main-integration.lock"


@pytest.fixture(autouse=True)
def isolated_git_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("HOME", str(tmp_path))


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def run(*args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False, env=env, cwd=cwd)


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
    if symlink:
        admin = admin_of(wt)
        (wt / ".git").unlink()
        os.symlink(os.path.relpath(admin, wt), wt / ".git")
    return wt


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
    git(repo, "config", "branch.task/wt-desc.description", "fix x; base abc; client=claude")
    result = run(str(wt))
    assert result.returncode == 0, result.stderr
    assert "owner: fix x; base abc; client=claude" in result.stderr.splitlines()
    assert result.stdout == f"removed {wt.resolve()}\n"


def test_delete_branch_drops_only_its_own_config_section(repo: Path) -> None:
    wt = make_worktree(repo, "wt-desc")
    git(repo, "branch", "task/wt-desc-x")
    git(repo, "config", "branch.task/wt-desc.description", "d")
    git(repo, "config", "branch.task/wt-desc.remote", "origin")
    git(repo, "config", "branch.task/wt-desc-x.description", "sibling")
    assert run(str(wt), "--delete-branch").returncode == 0
    assert config_keys(repo, r"^branch\.task/wt-desc\.") == ""
    assert git(repo, "config", "--get", "branch.task/wt-desc-x.description") == "sibling"


def test_delete_branch_drops_section_without_description(repo: Path) -> None:
    wt = make_worktree(repo, "wt-upstream")
    git(repo, "config", "branch.task/wt-upstream.merge", "refs/heads/task/wt-upstream")
    assert run(str(wt), "--delete-branch").returncode == 0
    assert config_keys(repo, r"^branch\.task/wt-upstream\.") == ""


def test_unusual_branch_name_section_is_removed(repo: Path) -> None:
    wt = repo.parent / "wt-dotted"
    git(repo, "worktree", "add", "--quiet", "-b", "task/Foo.v2", str(wt))
    git(repo, "config", "branch.task/Foo.v2.description", "dotted")
    assert run(str(wt), "--delete-branch").returncode == 0
    assert config_keys(repo, r"^branch\.") == ""


def test_dry_run_prints_owner_and_keeps_description(repo: Path) -> None:
    wt = make_worktree(repo, "wt-desc2")
    git(repo, "config", "branch.task/wt-desc2.description", "task two")
    result = run(str(wt), "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "owner: task two" in result.stderr.splitlines()
    assert git(repo, "config", "--get", "branch.task/wt-desc2.description") == "task two"


def test_refusal_still_reports_owner(repo: Path) -> None:
    wt = make_worktree(repo, "wt-refused")
    git(repo, "config", "branch.task/wt-refused.description", "refused task")
    (wt / "new.txt").write_text("x")
    result = run(str(wt))
    assert result.returncode == 1 and "not clean" in result.stderr
    assert "owner: refused task" in result.stderr.splitlines()


def test_multiline_description_is_one_escaped_line(repo: Path) -> None:
    wt = make_worktree(repo, "wt-multi")
    git(repo, "config", "branch.task/wt-multi.description", "line1\nline2\x1b[31m")
    result = run(str(wt))
    assert result.returncode == 0, result.stderr
    owners = [line for line in result.stderr.splitlines() if line.startswith("owner:")]
    assert owners == ["owner: line1\\nline2\\x1b[31m"]
    assert "\x1b" not in result.stderr


def test_japanese_description_is_kept_readable(repo: Path) -> None:
    wt = make_worktree(repo, "wt-ja")
    git(repo, "config", "branch.task/wt-ja.description", "worktree命名の記録; client=claude")
    result = run(str(wt))
    assert "owner: worktree命名の記録; client=claude" in result.stderr.splitlines()


def test_description_from_env_config_does_not_fail_the_cleanup(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wt = make_worktree(repo, "wt-env")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "branch.task/wt-env.description")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "from env")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert not wt.exists()
    assert "task/wt-env" not in git(repo, "branch", "--list")


def test_busy_config_only_warns_after_removal(repo: Path) -> None:
    wt = make_worktree(repo, "wt-busy")
    git(repo, "config", "branch.task/wt-busy.description", "busy")
    (repo / ".git" / "config.lock").write_text("")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert not wt.exists() and "task/wt-busy" not in git(repo, "branch", "--list")
    assert "warning: refs/heads/task/wt-busy removed, but config section" in result.stderr


def test_without_description_reports_none_and_still_removes(repo: Path) -> None:
    wt = make_worktree(repo, "wt-nodesc")
    result = run(str(wt), "--delete-branch")
    assert result.returncode == 0, result.stderr
    assert "owner: none" in result.stderr
    assert not wt.exists()


def test_detached_worktree_reports_none(repo: Path) -> None:
    wt = repo.parent / "wt-detached"
    git(repo, "worktree", "add", "--quiet", "--detach", str(wt))
    result = run(str(wt))
    assert result.returncode == 0, result.stderr
    assert "owner: none" in result.stderr
    assert not wt.exists()


def test_description_kept_when_branch_is_kept(repo: Path) -> None:
    wt = make_worktree(repo, "wt-keep")
    git(repo, "config", "branch.task/wt-keep.description", "still on the branch")
    assert run(str(wt)).returncode == 0
    assert "task/wt-keep" in git(repo, "branch", "--list")
    assert git(repo, "config", "--get", "branch.task/wt-keep.description") == "still on the branch"


def test_plain_gitfile_worktree_is_also_removed(repo: Path) -> None:
    wt = make_worktree(repo, "wt2", symlink=False)
    assert run(str(wt)).returncode == 0
    assert not wt.exists()


def test_expect_owner_match_removes(repo: Path) -> None:
    wt = make_worktree(repo, "wt-own1")
    git(repo, "config", "branch.task/wt-own1.description", "rename helper; client=claude")
    result = run(str(wt), "--expect-owner", "rename helper")
    assert result.returncode == 0, result.stderr
    assert not wt.exists()


def test_expect_owner_mismatch_refuses_and_keeps_everything(repo: Path) -> None:
    wt = make_worktree(repo, "wt-own2")
    git(repo, "config", "branch.task/wt-own2.description", "someone else's task; client=opencode")
    result = run(str(wt), "--delete-branch", "--expect-owner", "rename helper")
    assert result.returncode == 1 and "owner mismatch" in result.stderr
    assert_untouched(wt)
    assert git(repo, "config", "--get", "branch.task/wt-own2.description").startswith("someone")
    assert not (repo / ".git" / LOCK).exists()


def test_expect_owner_without_description_refuses(repo: Path) -> None:
    wt = make_worktree(repo, "wt-own3")
    result = run(str(wt), "--expect-owner", "anything")
    assert result.returncode == 1 and "owner mismatch" in result.stderr
    assert_untouched(wt)


def test_expect_owner_is_enforced_in_dry_run(repo: Path) -> None:
    wt = make_worktree(repo, "wt-own4")
    git(repo, "config", "branch.task/wt-own4.description", "other")
    result = run(str(wt), "--dry-run", "--expect-owner", "mine")
    assert result.returncode == 1 and "owner mismatch" in result.stderr
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


def test_refuses_reflog_only_commit_on_detached_head(repo: Path) -> None:
    wt = make_worktree(repo, "wt10")
    git(wt, "checkout", "--quiet", "--detach")
    lost = commit(wt, "lost.txt", "only in reflog")
    git(wt, "checkout", "--quiet", "--detach", "main")
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
    result = run(str(wt), env={"PATH": str(bin_dir), "HOME": str(tmp_path), "GIT_CONFIG_GLOBAL": os.devnull})
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
