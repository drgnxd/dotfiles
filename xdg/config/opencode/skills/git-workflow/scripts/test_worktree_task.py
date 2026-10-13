from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location("worktree_task", Path(__file__).with_name("worktree-task.py"))
assert spec is not None and spec.loader is not None
task = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = task
spec.loader.exec_module(task)

SESSION = "ses_" + "a" * 26


def git(cwd: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, input=input_text, text=True,
        capture_output=True, check=True,
    )
    return result.stdout.strip()


class WorktreeTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.old_env = os.environ.copy()
        for name in (
            "CLAUDE_CODE_SESSION_ID", "CLAUDE_PID", "OPENCODE_PID", "GIT_DIR",
            "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        ):
            os.environ.pop(name, None)
        self.state = self.root / "state"
        self.data = self.root / "data"
        os.environ.update({
            "HOME": str(self.root / "home"),
            "XDG_STATE_HOME": str(self.state),
            "XDG_DATA_HOME": str(self.data),
            "OPENCODE_SESSION_ID": SESSION,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        })
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-q", "-m", "root")

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)
        self.temp.cleanup()

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = task.main(argv)
        return code, out.getvalue(), err.getvalue()

    def start(self, slug: str = "fix-feature", source: str = "main") -> tuple[str, Path]:
        code, stdout, stderr = self.invoke([
            "start", "--repo", str(self.repo), "--slug", slug,
            "--client", "opencode", "--task", "test lifecycle", "--from", source, "--json",
        ])
        self.assertEqual(code, 0, msg=stderr + stdout)
        record = json.loads(stdout)
        return record["branch"], Path(record["worktree"])

    def finish(self, branch: str, *extra: str) -> tuple[int, str, str]:
        return self.invoke([
            "finish", "--repo", str(self.repo), "--branch", branch,
            "--external-writers-quiesced", "--json", *extra,
        ])

    def hooks_dir(self) -> Path:
        hooks = Path(git(self.repo, "rev-parse", "--git-path", "hooks"))
        return hooks if hooks.is_absolute() else self.repo / hooks

    def commit_file(self, cwd: Path, name: str, text: str, message: str, *, force: bool = False) -> str:
        path = cwd / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if force:
            git(cwd, "add", "-f", "--", name)
        else:
            git(cwd, "add", "--", name)
        git(cwd, "commit", "-q", "-m", message)
        return git(cwd, "rev-parse", "HEAD")

    def test_start_requires_explicit_repo_and_valid_session_before_create(self) -> None:
        with patch.dict(os.environ, {"OPENCODE_SESSION_ID": "bad"}):
            code, stdout, _ = self.invoke([
                "start", "--repo", str(self.repo), "--slug", "fix-feature",
                "--client", "opencode", "--task", "test lifecycle",
            ])
        self.assertEqual(code, 1)
        self.assertIn("session-unavailable", stdout)
        self.assertEqual(len(task.worktree_entries(self.repo)), 1)

    def test_start_uses_explicit_repo_and_preserves_creator_fields(self) -> None:
        branch, worktree = self.start()
        self.assertTrue(worktree.is_dir())
        self.assertEqual(Path(git(worktree, "rev-parse", "--show-toplevel")).resolve(), worktree.resolve())
        description = git(self.repo, "config", "--get", f"branch.{branch}.description")
        self.assertIn(f"client=opencode session={SESSION}", description)

    def test_creator_partial_status_is_reported_without_cleanup(self) -> None:
        fake = subprocess.CompletedProcess([], 3, "worktree=/missing\nbranch=task/partial\n", "owner metadata failed\n")
        with patch.object(task, "create_worktree", return_value=fake):
            code, stdout, _ = self.invoke([
                "start", "--repo", str(self.repo), "--slug", "fix-feature",
                "--client", "opencode", "--task", "test lifecycle", "--json",
            ])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(stdout)["status"], "partial-creation")

    def test_finish_refuses_without_external_writer_assertion(self) -> None:
        branch, worktree = self.start()
        before = git(self.repo, "rev-parse", "HEAD")
        code, stdout, _ = self.invoke(["finish", "--repo", str(self.repo), "--branch", branch, "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "external-writers-not-confirmed")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), before)
        self.assertTrue(worktree.is_dir())

    def test_start_requires_opt_in_for_post_checkout_hook(self) -> None:
        marker = self.root / "post-checkout.log"
        hook = self.hooks_dir() / "post-checkout"
        hook.write_text(f"#!/bin/sh\nprintf 'called\\n' >> '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)
        argv = [
            "start", "--repo", str(self.repo), "--slug", "fix-feature",
            "--client", "opencode", "--task", "test lifecycle", "--json",
        ]

        code, stdout, stderr = self.invoke(argv)

        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stdout)["status"], "creation-failed")
        self.assertIn("post-checkout hooks", stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(len(task.worktree_entries(self.repo)), 1)

        code, stdout, stderr = self.invoke([*argv[:-1], "--allow-repository-hooks", "--json"])

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(marker.read_text(encoding="utf-8"), "called\n")
        self.assertEqual(len(task.worktree_entries(self.repo)), 2)

    def test_finish_fast_forwards_and_removes_task_worktree(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        code, stdout, stderr = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 0, msg=stderr + stdout)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "removed")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), tip)
        self.assertFalse(worktree.exists())
        self.assertNotEqual(subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=self.repo, check=False).returncode, 0)

    def test_finish_preserves_generated_artifacts_before_removing_worktree(self) -> None:
        (self.repo / ".gitignore").write_text(".ruff_cache/\n.pre-commit-config.yaml\ntarget/\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-q", "-m", "ignore generated files")
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        cache_file = worktree / ".ruff_cache" / "content"
        cache_file.parent.mkdir()
        cache_file.write_bytes(b"cache bytes")
        config = worktree / ".pre-commit-config.yaml"
        config.write_text(
            '# DO NOT MODIFY\n# This file was generated by git-hooks.nix\n{}\n',
            encoding="utf-8",
        )
        expected_config = config.read_bytes()
        target_artifact = worktree / "target" / "debug" / "artifact"
        target_artifact.parent.mkdir(parents=True)
        target_artifact.write_bytes(b"build output")

        code, stdout, stderr = self.finish(branch, "--preserve-generated-artifacts")

        self.assertEqual(code, 0, msg=stderr + stdout)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "removed")
        self.assertFalse(worktree.exists())
        quarantine = self.state / self.repo.name / "worktrees" / ".removal-quarantine"
        transaction = next(quarantine.iterdir())
        manifest = json.loads((transaction / "manifest.json").read_text(encoding="utf-8"))
        artifacts = {item["path"]: Path(item["quarantine_path"]) for item in manifest["generated_caches"]}
        self.assertEqual((artifacts[".ruff_cache"] / "content").read_bytes(), b"cache bytes")
        self.assertEqual(artifacts[".pre-commit-config.yaml"].read_bytes(), expected_config)
        self.assertEqual((artifacts["target"] / "debug" / "artifact").read_bytes(), b"build output")
        self.assertEqual(manifest["phase"], "completed_preserved")

    def test_finish_ignores_active_dirty_unrelated_worktree(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        other = self.root / "other"
        other_branch = "task/unrelated-writer"
        git(self.repo, "worktree", "add", "-q", "-b", other_branch, str(other), "main")
        base = git(other, "rev-parse", "HEAD")
        description = task.meta.format_description("unrelated active task", "opencode", SESSION, base, os.getpid(), None)
        git(self.repo, "config", "--local", f"branch.{other_branch}.description", description)
        (other / "untracked.txt").write_text("preserve\n", encoding="utf-8")

        code, stdout, stderr = self.finish(branch, "--delete-branch")

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(git(self.repo, "rev-parse", "main"), tip)
        self.assertFalse(worktree.exists())
        self.assertTrue(other.is_dir())
        self.assertEqual((other / "untracked.txt").read_text(encoding="utf-8"), "preserve\n")
        self.assertEqual(git(other, "branch", "--show-current"), other_branch)

    def test_finish_uses_integration_worktree_when_main_advanced(self) -> None:
        branch, task_wt = self.start()
        task_tip = self.commit_file(task_wt, "task.txt", "task\n", "task")
        main_tip = self.commit_file(self.repo, "main.txt", "main\n", "main progress")
        code, stdout, stderr = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 0, msg=stderr + stdout)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "removed")
        self.assertEqual(result["plan"], "integration-worktree-merge")
        self.assertTrue(task.ancestor(self.repo, task_tip, "main"))
        self.assertTrue(task.ancestor(self.repo, main_tip, "main"))
        self.assertTrue((self.repo / "task.txt").is_file())
        self.assertTrue((self.repo / "main.txt").is_file())
        branches = git(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/integration").splitlines()
        self.assertEqual(branches, [])
        self.assertEqual(len(task.worktree_entries(self.repo)), 1)

    def test_integration_preflight_ignores_main_only_filtered_paths(self) -> None:
        branch, worktree = self.start()
        task_tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        (self.repo / ".gitattributes").write_text("*.annex filter=annex\n", encoding="utf-8")
        git(self.repo, "add", ".gitattributes")
        git(self.repo, "commit", "-q", "-m", "add annex filter")
        self.commit_file(self.repo, "main-only.annex", "annex metadata\n", "main annex file")

        code, stdout, stderr = self.finish(branch)

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(json.loads(stdout)["plan"], "integration-worktree-merge")
        self.assertTrue(task.ancestor(self.repo, task_tip, "main"))
        self.assertEqual((self.repo / "main-only.annex").read_text(encoding="utf-8"), "annex metadata\n")
        self.assertTrue((self.repo / "task.txt").is_file())
        self.assertFalse(worktree.exists())

    def test_finish_uses_repository_specific_integration_message(self) -> None:
        branch, worktree = self.start()
        task_tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        self.commit_file(self.repo, "main.txt", "main\n", "main progress")

        code, stdout, stderr = self.finish(branch, "--integration-message", "chore: 作業ブランチを統合")

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(git(self.repo, "log", "-1", "--format=%s"), "chore: 作業ブランチを統合")
        self.assertTrue(task.ancestor(self.repo, task_tip, "main"))

    def test_finish_rejects_multiline_integration_message_before_mutation(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        self.commit_file(self.repo, "main.txt", "main\n", "main progress")
        main_tip = git(self.repo, "rev-parse", "main")

        code, stdout, _ = self.finish(branch, "--integration-message", "subject\nbody")

        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "invalid-options")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_finish_recognizes_already_integrated_task(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        git(self.repo, "merge", "--ff-only", branch)
        code, stdout, stderr = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 0, msg=stderr + stdout)
        result = json.loads(stdout)
        self.assertEqual(result["plan"], "already-integrated")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), tip)
        self.assertFalse(worktree.exists())

    def test_finish_removes_empty_already_integrated_worktree_without_hooks(self) -> None:
        branch, worktree = self.start()
        hook = self.hooks_dir() / "post-merge"
        marker = self.root / "post-merge-ran"
        hook.write_text(f"#!/bin/sh\nprintf called > '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)

        code, stdout, stderr = self.finish(branch, "--delete-branch")

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(json.loads(stdout)["plan"], "already-integrated")
        self.assertEqual(git(self.repo, "rev-parse", "main"), git(self.repo, "rev-parse", "HEAD"))
        self.assertFalse(marker.exists())
        self.assertFalse(worktree.exists())

    def test_finish_rejects_unrelated_history(self) -> None:
        main_tip = git(self.repo, "rev-parse", "main")
        git(self.repo, "checkout", "--orphan", "unrelated")
        (self.repo / "independent.txt").write_text("unrelated\n", encoding="utf-8")
        git(self.repo, "add", "independent.txt")
        git(self.repo, "commit", "-q", "-m", "unrelated root")
        git(self.repo, "checkout", "main")
        branch, worktree = self.start(source="unrelated")
        self.commit_file(worktree, "task.txt", "task\n", "task")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "histories-diverged")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_finish_rejects_dirty_task_worktree(self) -> None:
        branch, worktree = self.start()
        (worktree / "untracked.txt").write_text("unfinished\n", encoding="utf-8")
        main_tip = git(self.repo, "rev-parse", "main")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "dirty-worktree")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_finish_rejects_assume_unchanged_index_entries(self) -> None:
        branch, _ = self.start()
        git(self.repo, "update-index", "--assume-unchanged", "README.md")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "index-flags")
        git(self.repo, "update-index", "--no-assume-unchanged", "README.md")

    def test_finish_rejects_replace_refs(self) -> None:
        branch, worktree = self.start()
        replacement = self.commit_file(worktree, "task.txt", "task\n", "task")
        main_tip = git(self.repo, "rev-parse", "main")
        git(self.repo, "update-ref", f"refs/replace/{main_tip}", replacement)
        code, stdout, _ = self.finish(branch, "--delete-branch")
        git(self.repo, "update-ref", "-d", f"refs/replace/{main_tip}")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "replace-refs")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_finish_rejects_ignored_path_collision(self) -> None:
        (self.repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "-q", "-m", "ignore generated file")
        (self.repo / "ignored.txt").write_text("preserve\n", encoding="utf-8")
        branch, worktree = self.start()
        self.commit_file(worktree, "ignored.txt", "task\n", "task", force=True)
        main_tip = git(self.repo, "rev-parse", "main")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "path-collision")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertEqual((self.repo / "ignored.txt").read_text(encoding="utf-8"), "preserve\n")
        self.assertTrue(worktree.is_dir())

    def test_finish_rejects_filter_added_by_task_tree(self) -> None:
        branch, worktree = self.start()
        (worktree / ".gitattributes").write_text("*.txt filter=custom\n", encoding="utf-8")
        (worktree / "task.txt").write_text("task\n", encoding="utf-8")
        git(worktree, "add", ".gitattributes", "task.txt")
        git(worktree, "commit", "-q", "-m", "add custom filter")
        main_tip = git(self.repo, "rev-parse", "main")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "filters-present")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_finish_rejects_existing_submodule_gitlink_oid_update(self) -> None:
        submodule = self.root / "submodule-source"
        submodule.mkdir()
        git(submodule, "init", "-q", "-b", "main")
        (submodule / "README.md").write_text("before\n", encoding="utf-8")
        git(submodule, "add", "README.md")
        git(submodule, "commit", "-q", "-m", "submodule before")
        before = git(submodule, "rev-parse", "HEAD")
        (submodule / "README.md").write_text("after\n", encoding="utf-8")
        git(submodule, "add", "README.md")
        git(submodule, "commit", "-q", "-m", "submodule after")
        after = git(submodule, "rev-parse", "HEAD")
        (self.repo / ".gitmodules").write_text(
            f'[submodule "module"]\n\tpath = vendor/module\n\turl = {submodule}\n',
            encoding="utf-8",
        )
        git(self.repo, "add", ".gitmodules")
        git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{before},vendor/module")
        git(self.repo, "-c", "protocol.file.allow=always", "submodule", "update", "--init", "--", "vendor/module")
        git(self.repo, "commit", "-q", "-m", "add submodule")
        branch, worktree = self.start()
        git(worktree, "-c", "protocol.file.allow=always", "submodule", "update", "--init", "--", "vendor/module")
        git(worktree, "update-index", "--cacheinfo", f"160000,{after},vendor/module")
        git(worktree, "-c", "protocol.file.allow=always", "submodule", "update", "--init", "--", "vendor/module")
        git(worktree, "commit", "-q", "-m", "update submodule")
        main_tip = git(self.repo, "rev-parse", "main")

        code, stdout, _ = self.finish(branch, "--delete-branch")

        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "submodule-change", stdout)
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(worktree.is_dir())

    def test_safe_removal_refusal_reports_integrated_cleanup_pending(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        failure = subprocess.CompletedProcess([], 1, "", "helper refused\n")
        with patch.object(task, "safe_remove", return_value=failure):
            code, stdout, _ = self.finish(branch, "--delete-branch")
        result = json.loads(stdout)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "cleanup-partial")
        self.assertEqual(result["main_tip"], tip)
        self.assertTrue(result["worktree_registered"])
        self.assertTrue(worktree.is_dir())

    def test_cleanup_tip_change_after_postcheck_is_detected_before_removal(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        tree = git(self.repo, "rev-parse", f"{tip}^{{tree}}")
        changed_tip = git(self.repo, "commit-tree", tree, "-p", tip, "-m", "unexpected branch update")
        original_postcheck = task.postcheck

        def move_branch_after_postcheck(repo, main, expected, task_branch, task_tip, integration_branch, integration_tip):
            result = original_postcheck(repo, main, expected, task_branch, task_tip, integration_branch, integration_tip)
            git(repo, "update-ref", f"refs/heads/{branch}", changed_tip)
            return result

        with patch.object(task, "postcheck", side_effect=move_branch_after_postcheck), patch.object(task, "safe_remove") as remove:
            code, stdout, _ = self.finish(branch, "--delete-branch")

        result = json.loads(stdout)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "cleanup-pending")
        self.assertEqual(result["main_tip"], tip)
        self.assertEqual(git(self.repo, "rev-parse", f"refs/heads/{branch}"), changed_tip)
        self.assertTrue(worktree.is_dir())
        remove.assert_not_called()

    def test_safe_remove_refuses_branch_tip_change_after_cleanup_check(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        tree = git(self.repo, "rev-parse", f"{tip}^{{tree}}")
        changed_tip = git(self.repo, "commit-tree", tree, "-p", tip, "-m", "unexpected branch update")
        original_remove = task.safe_remove

        def move_branch_during_removal(repo, target, target_branch, args, delete_branch):
            git(repo, "update-ref", f"refs/heads/{branch}", changed_tip)
            return original_remove(repo, target, target_branch, args, delete_branch)

        with patch.object(task, "safe_remove", side_effect=move_branch_during_removal):
            code, stdout, _ = self.finish(branch, "--delete-branch")

        result = json.loads(stdout)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "cleanup-partial")
        self.assertEqual(result["main_tip"], tip)
        self.assertEqual(git(self.repo, "rev-parse", f"refs/heads/{branch}"), changed_tip)
        self.assertTrue(worktree.is_dir())

    def test_keep_worktree_integrates_without_removal(self) -> None:
        branch, worktree = self.start()
        tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        code, stdout, stderr = self.finish(branch, "--keep-worktree")
        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(json.loads(stdout)["status"], "integrated-kept")
        self.assertEqual(git(self.repo, "rev-parse", "main"), tip)
        self.assertTrue(worktree.is_dir())

    def test_integration_conflict_preserves_main_and_worktrees(self) -> None:
        branch, task_wt = self.start()
        self.commit_file(task_wt, "README.md", "task change\n", "task change")
        main_tip = self.commit_file(self.repo, "README.md", "main change\n", "main change")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "integration-conflict")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(task_wt.is_dir())
        self.assertGreaterEqual(len(task.worktree_entries(self.repo)), 3)

    def test_merged_tree_alias_is_checked_before_main_update(self) -> None:
        branch, task_wt = self.start()
        task_tip = self.commit_file(task_wt, "folder/task.txt", "task\n", "task")
        main_tip = self.commit_file(self.repo, "Folder/main.txt", "main\n", "main progress")
        code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "path-collision")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertTrue(task_wt.is_dir())
        self.assertFalse(task.ancestor(self.repo, task_tip, git(self.repo, "rev-parse", "HEAD")))
        self.assertGreaterEqual(len(task.worktree_entries(self.repo)), 3)

    def test_postcheck_failure_reports_actual_main_and_preserves_task(self) -> None:
        branch, worktree = self.start()
        task_tip = self.commit_file(worktree, "task.txt", "task\n", "task")
        with patch.object(task, "postcheck", return_value={"ok": False, "failures": ["test failure"]}):
            code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "integration-verification-failed")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), task_tip)
        self.assertTrue(worktree.is_dir())
        self.assertEqual(subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=self.repo, check=False).returncode, 0)

    def assert_integration_creator_partial(self, helper_exit: int) -> None:
        branch, _ = self.start(slug=f"fix-partial{helper_exit}")
        self.commit_file(task.worktree_for_branch(self.repo, branch), f"task-{helper_exit}.txt", "task\n", "task")
        main_tip = self.commit_file(self.repo, f"main-{helper_exit}.txt", "main\n", "main progress")
        fake = subprocess.CompletedProcess(
            [], helper_exit,
            f"worktree=/missing-{helper_exit}\nbranch=integration/partial-{helper_exit}\n",
            f"partial creator failure {helper_exit}\n",
        )
        with patch.object(task, "create_worktree", return_value=fake):
            code, stdout, _ = self.finish(branch, "--delete-branch")
        self.assertEqual(code, 1)
        result = json.loads(stdout)
        self.assertEqual(result["status"], "integration-worktree-create-partial")
        self.assertEqual(result["helper_exit"], helper_exit)
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertEqual(len(task.worktree_entries(self.repo)), 2)

    def test_integration_creator_exit_3_is_reported(self) -> None:
        self.assert_integration_creator_partial(3)

    def test_integration_creator_exit_4_is_reported(self) -> None:
        self.assert_integration_creator_partial(4)

    def test_commit_hooks_are_required_only_for_merge_commits(self) -> None:
        _, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        hooks = Path(git(self.repo, "rev-parse", "--git-path", "hooks"))
        if not hooks.is_absolute():
            hooks = self.repo / hooks
        hook = hooks / "commit-msg"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hook.chmod(0o755)
        self.assertIsNone(task.require_no_hooks(self.repo, merge_commit=False))
        with self.assertRaises(task.TaskError) as caught:
            task.require_no_hooks(self.repo, merge_commit=True)
        self.assertEqual(caught.exception.status, "hooks-present")
        self.assertIsNone(task.require_no_hooks(self.repo, merge_commit=True, allow_repository_hooks=True))

    def test_commit_signing_is_detected_before_creating_integration_worktree(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        main_tip = self.commit_file(self.repo, "main.txt", "main\n", "main progress")
        git(self.repo, "config", "commit.gpgsign", "true")

        code, stdout, _ = self.finish(branch)

        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "commit-signing")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertEqual(git(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/integration"), "")
        self.assertTrue(worktree.is_dir())

    def test_commit_signing_requires_explicit_opt_in(self) -> None:
        git(self.repo, "config", "commit.gpgsign", "true")

        with self.assertRaises(task.TaskError) as caught:
            task.require_no_hooks(self.repo, merge_commit=True)
        self.assertEqual(caught.exception.status, "commit-signing")
        self.assertIsNone(task.require_no_hooks(self.repo, merge_commit=True, allow_commit_signing=True))

    def test_post_merge_hook_requires_explicit_opt_in(self) -> None:
        hook = self.hooks_dir() / "post-merge"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hook.chmod(0o755)

        with self.assertRaises(task.TaskError) as caught:
            task.require_no_hooks(self.repo, merge_commit=False)

        self.assertEqual(caught.exception.status, "hooks-present")
        self.assertIsNone(task.require_no_hooks(self.repo, merge_commit=False, allow_repository_hooks=True))

    def test_finish_runs_reviewed_post_merge_hook_on_fast_forward(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        marker = self.root / "post-merge.log"
        hook = self.hooks_dir() / "post-merge"
        hook.write_text(f"#!/bin/sh\nprintf 'called\\n' >> '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)

        code, stdout, stderr = self.finish(branch, "--allow-repository-hooks")

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(json.loads(stdout)["status"], "removed")
        self.assertEqual(marker.read_text(encoding="utf-8"), "called\n")
        self.assertFalse(worktree.exists())

    def test_finish_runs_reviewed_post_merge_hook_for_integration_and_fast_forward(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        self.commit_file(self.repo, "main.txt", "main\n", "main progress")
        hooks = self.hooks_dir()
        post_merge_log = self.root / "post-merge.log"
        post_merge = hooks / "post-merge"
        post_merge.write_text(f"#!/bin/sh\nprintf 'called\\n' >> '{post_merge_log}'\n", encoding="utf-8")
        post_merge.chmod(0o755)
        post_checkout_log = self.root / "post-checkout.log"
        post_checkout = hooks / "post-checkout"
        post_checkout.write_text(f"#!/bin/sh\nprintf 'called\\n' >> '{post_checkout_log}'\n", encoding="utf-8")
        post_checkout.chmod(0o755)

        code, stdout, stderr = self.finish(branch, "--allow-repository-hooks")

        self.assertEqual(code, 0, msg=stderr + stdout)
        self.assertEqual(json.loads(stdout)["plan"], "integration-worktree-merge")
        self.assertEqual(post_merge_log.read_text(encoding="utf-8"), "called\ncalled\n")
        self.assertEqual(post_checkout_log.read_text(encoding="utf-8"), "called\n")
        self.assertFalse(worktree.exists())

    def test_reference_transaction_hook_blocks_fast_forward_before_running(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        main_tip = git(self.repo, "rev-parse", "main")
        hooks = Path(git(self.repo, "rev-parse", "--git-path", "hooks"))
        if not hooks.is_absolute():
            hooks = self.repo / hooks
        sentinel = self.root / "reference-transaction-ran"
        hook = hooks / "reference-transaction"
        hook.write_text(f"#!/bin/sh\nprintf called > '{sentinel}'\n", encoding="utf-8")
        hook.chmod(0o755)

        code, stdout, _ = self.finish(branch, "--delete-branch", "--allow-repository-hooks")

        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "hooks-present")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertFalse(sentinel.exists())
        self.assertTrue(worktree.is_dir())

    def test_reference_transaction_hook_blocks_integration_before_running(self) -> None:
        branch, worktree = self.start()
        self.commit_file(worktree, "task.txt", "task\n", "task")
        main_tip = self.commit_file(self.repo, "main.txt", "main\n", "main progress")
        hooks = Path(git(self.repo, "rev-parse", "--git-path", "hooks"))
        if not hooks.is_absolute():
            hooks = self.repo / hooks
        sentinel = self.root / "reference-transaction-ran"
        hook = hooks / "reference-transaction"
        hook.write_text(f"#!/bin/sh\nprintf called > '{sentinel}'\n", encoding="utf-8")
        hook.chmod(0o755)

        code, stdout, _ = self.finish(branch, "--delete-branch", "--allow-repository-hooks")

        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)["status"], "hooks-present")
        self.assertEqual(git(self.repo, "rev-parse", "main"), main_tip)
        self.assertEqual(git(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/integration"), "")
        self.assertFalse(sentinel.exists())
        self.assertTrue(worktree.is_dir())

    def test_filter_attribute_is_rejected(self) -> None:
        (self.repo / ".gitattributes").write_text("*.txt filter=custom\n", encoding="utf-8")
        git(self.repo, "add", ".gitattributes")
        git(self.repo, "commit", "-q", "-m", "filter attribute")
        with self.assertRaises(task.TaskError) as caught:
            task.require_no_filters(self.repo, ["sample.txt"])
        self.assertEqual(caught.exception.status, "filters-present")

    def test_annex_filter_requires_opt_in_and_verified_commands(self) -> None:
        (self.repo / ".gitattributes").write_text("*.annex filter=annex\n", encoding="utf-8")
        git(self.repo, "add", ".gitattributes")
        git(self.repo, "commit", "-q", "-m", "annex attributes")
        for name, value in task.ANNEX_FILTER_COMMANDS.items():
            git(self.repo, "config", name, value)

        with self.assertRaises(task.TaskError) as caught:
            task.require_no_filters(self.repo, ["sample.annex"])
        self.assertEqual(caught.exception.status, "filters-present")

        original_git = task.meta.git

        def with_annex_version(cwd: Path, *args: str, **kwargs):
            if args == ("annex", "version"):
                return subprocess.CompletedProcess(args, 0, "git-annex test version\n", "")
            return original_git(cwd, *args, **kwargs)

        with patch.object(task.meta, "git", side_effect=with_annex_version):
            self.assertIsNone(task.require_no_filters(self.repo, ["sample.annex"], allow_annex_filter=True))
            git(self.repo, "config", "filter.annex.process", "untrusted command")
            with self.assertRaises(task.TaskError) as caught:
                task.require_no_filters(self.repo, ["sample.annex"], allow_annex_filter=True)
        self.assertEqual(caught.exception.status, "filters-present")

    def test_final_tree_checker_detects_case_alias_from_two_input_trees(self) -> None:
        _, task_wt = self.start()
        self.commit_file(task_wt, "folder/task.txt", "task\n", "task")
        self.commit_file(self.repo, "Folder/main.txt", "main\n", "main progress")
        base_tip = git(self.repo, "rev-parse", "main")
        blob = git(self.repo, "hash-object", "-w", "--stdin", input_text="merged\n")
        a_tree = git(self.repo, "mktree", input_text=f"100644 blob {blob}\tfile.txt\n")
        b_tree = git(self.repo, "mktree", input_text=f"100644 blob {blob}\tfile.txt\n")
        root_tree = git(self.repo, "mktree", input_text=f"040000 tree {a_tree}\tFolder\n040000 tree {b_tree}\tfolder\n")
        synthetic = git(self.repo, "commit-tree", root_tree, "-p", base_tip, "-m", "synthetic merge tree")
        with self.assertRaises(task.TaskError) as caught:
            task.check_tree_paths(self.repo, base_tip, synthetic)
        self.assertEqual(caught.exception.status, "path-collision")
        self.assertTrue(task_wt.is_dir())


if __name__ == "__main__":
    unittest.main()
