from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import worktree_guard as guard

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
}


def sh(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env={**GIT_ENV, "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    tmp_path = tmp_path.resolve()
    main = tmp_path / "repo"
    main.mkdir()
    sh(main, "init", "-q", "-b", "main")
    (main / "tracked.txt").write_text("x\n")
    (main / ".gitignore").write_text("local.db\n.envrc\n")
    (main / "local.db").write_text("db\n")
    sh(main, "add", "tracked.txt", ".gitignore")
    sh(main, "commit", "-q", "-m", "init")
    task = tmp_path / "wt" / "task-a"
    sh(main, "worktree", "add", "-q", "-b", "task/a", str(task))
    config_home = tmp_path / "config"
    (config_home / "worktree-guard").mkdir(parents=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    write_config(config_home, mode="deny", repos=[str(main)], allow_paths=[str(main / "local.db")])
    return {"main": main, "task": task, "config": config_home, "state": tmp_path / "state", "tmp": tmp_path}


def write_config(config_home: Path, **data: object) -> None:
    (config_home / "worktree-guard" / "config.json").write_text(json.dumps(data))


def decide(tool: str, tool_input: dict, cwd: Path):
    return guard.run("claude", {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})


def bash(command: str, cwd: Path):
    return decide("Bash", {"command": command}, cwd)


def test_disabled_without_config(world: dict[str, Path]) -> None:
    (world["config"] / "worktree-guard" / "config.json").unlink()
    decision, blocked = decide("Write", {"file_path": str(world["main"] / "new.txt")}, world["main"])
    assert decision.action == "allow" and not blocked


@pytest.mark.parametrize("name", ["tracked.txt", "brand-new.txt", ".envrc", "sub/dir/new.md"])
def test_edit_in_main_is_denied(world: dict[str, Path], name: str) -> None:
    decision, blocked = decide("Write", {"file_path": str(world["main"] / name)}, world["task"])
    assert blocked and decision.rule == "main-checkout"


def test_edit_in_task_worktree_and_outside_is_allowed(world: dict[str, Path]) -> None:
    assert not decide("Edit", {"file_path": str(world["task"] / "tracked.txt")}, world["main"])[1]
    assert not decide("Write", {"file_path": str(world["tmp"] / "elsewhere.txt")}, world["main"])[1]


def test_allow_path_and_git_dir_and_guard_config(world: dict[str, Path]) -> None:
    assert not decide("Write", {"file_path": str(world["main"] / "local.db")}, world["main"])[1]
    assert decide("Write", {"file_path": str(world["main"] / ".git" / "hooks" / "pre-commit")}, world["task"])[0].rule == "git-dir"
    assert decide("Write", {"file_path": str(world["config"] / "worktree-guard" / "config.json")}, world["task"])[0].rule == "guard-config"


def test_symlink_from_task_into_main_is_denied(world: dict[str, Path]) -> None:
    link = world["task"] / "alias.txt"
    link.symlink_to(world["main"] / "tracked.txt")
    assert decide("Write", {"file_path": str(link)}, world["task"])[1]


def test_main_checked_out_in_linked_worktree_is_protected(world: dict[str, Path]) -> None:
    sh(world["main"], "checkout", "-q", "-b", "other")
    second = world["tmp"] / "wt" / "on-main"
    sh(world["main"], "worktree", "add", "-q", str(second), "main")
    assert decide("Write", {"file_path": str(second / "x.txt")}, world["task"])[1]


def test_patch_with_several_paths(world: dict[str, Path]) -> None:
    patch = (
        "*** Begin Patch\n"
        f"*** Update File: {world['task']}/tracked.txt\n"
        f"*** Add File: {world['main']}/added.txt\n"
        f"*** Move to: {world['task']}/moved.txt\n*** End Patch\n"
    )
    decision, blocked = decide("apply_patch", {"patchText": patch}, world["task"])
    assert blocked and decision.target.endswith("added.txt")


@pytest.mark.parametrize(
    "command, cwd, blocked",
    [
        ("git commit -m x", "main", True),
        ("git add -A && git commit -m x", "main", True),
        ("git status", "main", False),
        ("git branch --list", "main", False),
        ("git stash list", "main", False),
        ("git merge --ff-only --no-overwrite-ignore abc", "main", False),
        ("git merge task/a", "main", True),
        ("git -C {task} commit -m x", "main", False),
        ("cd {main} && git commit -m x", "task", True),
        ("cd {task} && git commit -m x", "main", False),
        ("nix develop path:. -c git commit -m x", "main", True),
        ("direnv exec . git add f", "main", True),
        ("git worktree add ../x -b y", "task", True),
        ("git worktree list", "main", False),
        ("git worktree remove {task}", "task", True),
        ("git commit --no-verify -m x", "task", True),
        ("git commit -n -m x", "task", True),
        ("git commit -m x", "task", False),
        ("git annex sync", "main", True),
        ("echo done; git log --oneline", "main", False),
        ("cat <<'EOF'\ngit add everything\nEOF\ngit status", "main", False),
        ("cat <<EOF\nnote\nEOF\ngit add f", "main", True),
        ("python3 safe-worktree-remove.py {task}", "main", False),
        ("echo git commit", "main", False),
        ("man git add", "main", False),
        ('WT={task}; git -C "$WT" commit -m x', "main", False),
        ('cd "$HOME/somewhere" && git commit -m x', "main", False),
        ("git config branch.task/x.description", "main", False),
        ("git config --global user.name x", "main", False),
        ("git config get foo.bar", "main", False),
        ("git config list", "main", False),
        ("git config branch.task/x.description text", "main", True),
        ("git branch --merged main", "main", False),
        ("git branch -av", "main", False),
        ("git branch newbranch", "main", True),
        ("git branch -D x", "main", True),
        ("git tag -n", "main", False),
        ("git tag --points-at HEAD", "main", False),
        ("git tag v1", "main", True),
        ("git apply --check p.diff", "main", False),
        ("# commit it\ngit commit -m x", "main", True),
        ("nix develop .#dev -c git commit -m x", "main", True),
        ("git -C {main} \\\ncommit -m x", "task", True),
        ("cat <<'EOF' >/tmp/m && git commit -F /tmp/m\nbody\nEOF", "main", True),
        ("cat <<'END-MSG'\nUse git commit hooks\nEND-MSG", "main", False),
        ("git commit -nm x", "task", True),
        ("git merge --no-verify x", "task", True),
        ("git -c core.hooksPath=/dev/null commit -m x", "task", True),
        ("env GIT_DIR={main}/.git GIT_WORK_TREE={main} git commit -m x", "task", True),
        ("(cd {task} && true); git commit -m x", "main", True),
        ("git format-patch -1", "main", True),
        ("git update-index --skip-worktree f", "main", True),
        ("git submodule update", "main", True),
        ("git annex get f", "main", True),
        ("bash -c 'git commit -m x'", "main", True),
    ],
)
def test_bash_cases(world: dict[str, Path], command: str, cwd: str, blocked: bool) -> None:
    text = command.format(main=world["main"], task=world["task"])
    assert bash(text, world[cwd])[1] is blocked


def test_unresolved_target_warns_but_does_not_block(world: dict[str, Path]) -> None:
    decision, blocked = bash(f"GIT_DIR={world['main']}/.git git commit -m x", world["main"])
    assert decision.action == "warn" and not blocked


def test_enter_worktree_denied_in_protected_repo(world: dict[str, Path]) -> None:
    assert decide("EnterWorktree", {}, world["main"])[1]
    assert not decide("EnterWorktree", {}, world["tmp"])[1]


def test_warn_mode_logs_but_never_blocks(world: dict[str, Path]) -> None:
    write_config(world["config"], mode="warn", repos=[str(world["main"])])
    decision, blocked = decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])
    assert decision.action == "deny" and not blocked
    log = (world["state"] / "worktree-guard" / "log.jsonl").read_text()
    record = json.loads(log.splitlines()[-1])
    assert record["mode"] == "warn" and record["rule"] == "main-checkout"
    assert "command" not in record and "content" not in record


def test_internal_failure_fails_open(world: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(guard, "evaluate", boom)
    decision, blocked = decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])
    assert decision.action == "allow" and not blocked
    assert "RuntimeError" in (world["state"] / "worktree-guard" / "log.jsonl").read_text()


def test_missing_repo_fails_open(world: dict[str, Path]) -> None:
    write_config(world["config"], mode="deny", repos=[str(world["tmp"] / "does-not-exist")])
    assert not decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])[1]


def test_main_exit_codes(world: dict[str, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(world["main"] / "x.txt")}, "cwd": str(world["task"])}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main(["--client", "claude"]) == 2
    assert "worktree-guard" in capsys.readouterr().err
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool": "write", "args": payload["tool_input"], "cwd": payload["cwd"]})))
    assert guard.main(["--client", "opencode"]) == 0
    assert json.loads(capsys.readouterr().out)["block"] is True
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert guard.main(["--client", "claude"]) == 0


def test_aliases_are_expanded(world: dict[str, Path]) -> None:
    sh(world["main"], "config", "alias.ci", "commit")
    assert bash("git ci -m x", world["main"])[1]
    assert bash("git -c alias.zz=commit zz", world["main"])[1]
    assert not bash("git ci -m x", world["task"])[1]


def test_opencode_workdir_selects_the_repository(world: dict[str, Path]) -> None:
    def call(cwd: Path, workdir: Path) -> bool:
        payload = {"tool": "bash", "args": {"command": "git commit -m x", "workdir": str(workdir)}, "cwd": str(cwd)}
        return guard.run("opencode", payload)[1]

    assert not call(world["main"], world["task"])
    assert call(world["task"], world["main"])


def test_one_broken_repo_does_not_disable_the_others(world: dict[str, Path]) -> None:
    broken = world["tmp"] / "not-a-repo"
    broken.mkdir()
    write_config(world["config"], mode="deny", repos=[str(broken), str(world["main"])])
    assert decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])[1]
    assert "load_repo" in (world["state"] / "worktree-guard" / "log.jsonl").read_text()


def test_malformed_config_values_do_not_allow_everything(world: dict[str, Path]) -> None:
    write_config(world["config"], mode="deny", repos=[str(world["main"])], allow_paths="*")
    assert decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])[1]
    write_config(world["config"], mode="deny", repos=str(world["main"]))
    assert not decide("Write", {"file_path": str(world["main"] / "x.txt")}, world["task"])[1]


def test_allow_path_with_home_and_symlinked_root(world: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    link = world["tmp"] / "link-to-main"
    link.symlink_to(world["main"])
    write_config(world["config"], mode="deny", repos=[str(link)], allow_paths=[str(link / "local.db")])
    assert not decide("Write", {"file_path": str(world["main"] / "local.db")}, world["task"])[1]
    assert decide("Write", {"file_path": str(world["main"] / "other.txt")}, world["task"])[1]


@pytest.mark.skipif(sys.platform != "darwin", reason="case-insensitive filesystem")
def test_case_differing_path_is_still_protected(world: dict[str, Path]) -> None:
    upper = Path(str(world["main"] / "x.txt").upper())
    if not upper.parent.exists():
        pytest.skip("filesystem is case-sensitive")
    assert decide("Write", {"file_path": str(upper)}, world["task"])[1]


def test_detached_task_worktree_is_protected(world: dict[str, Path]) -> None:
    sh(world["task"], "checkout", "-q", "--detach")
    assert decide("Write", {"file_path": str(world["task"] / "x.txt")}, world["main"])[1]


def test_non_guarded_tools_skip_git_entirely(world: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: object) -> None:
        raise AssertionError("must not load repos")

    monkeypatch.setattr(guard, "load_repos", boom)
    assert not decide("Read", {"file_path": str(world["main"] / "tracked.txt")}, world["main"])[1]
    assert not bash("ls -la", world["main"])[1]
