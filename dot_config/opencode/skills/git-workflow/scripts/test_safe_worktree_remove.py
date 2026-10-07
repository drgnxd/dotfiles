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


def test_uses_another_worktree_for_git_admin_when_target_holds_main_branch(repo: Path) -> None:
    wt = make_worktree(repo, "wt-main-branch")
    git(repo, "checkout", "--quiet", "--detach")
    git(wt, "checkout", "--quiet", "main")

    result = run(str(wt))

    assert result.returncode == 0, result.stderr
    assert not wt.exists()
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
