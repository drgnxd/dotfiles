import contextlib
import glob
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wt_session

SESSION_VARS = ("OPENCODE_SESSION_ID", "CLAUDE_CODE_SESSION_ID")


def git_version():
    text = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout
    return tuple(int(part) for part in re.search(r"(\d+)\.(\d+)", text).groups())


def run(argv, **env):
    """Run main() with a clean session environment; return (code, stdout, stderr)."""
    saved = {var: os.environ.pop(var, None) for var in SESSION_VARS}
    os.environ.update(env)
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = wt_session.main(argv)
    finally:
        for var in SESSION_VARS:
            os.environ.pop(var, None)
            if saved[var] is not None:
                os.environ[var] = saved[var]
    return code, out.getvalue(), err.getvalue()


def fields(stdout):
    return dict(token.split("=", 1) for token in stdout.split() if "=" in token)


class WtSessionTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = os.path.realpath(tmp.name)
        self.repo = os.path.join(root, "proj")
        os.mkdir(self.repo)
        self.state = os.path.join(root, "state")
        for key in wt_session.GIT_ENV_DROP:
            self.addCleanup(self._restore, key, os.environ.pop(key, None))
        for key, value in (
            ("XDG_STATE_HOME", self.state),
            ("GIT_CONFIG_GLOBAL", os.devnull),
            ("GIT_CONFIG_SYSTEM", os.devnull),
        ):
            self.addCleanup(self._restore, key, os.environ.get(key))
            os.environ[key] = value
        self.git("init", "-q", "-b", "main")
        self.first = self.commit("seed")
        previous = os.getcwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(self.repo)

    @staticmethod
    def _restore(key, value):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(self, message):
        self.git(
            "-c", "user.name=t", "-c", "user.email=t@example.invalid",
            "commit", "-q", "--allow-empty", "-m", message,
        )
        return self.git("rev-parse", "HEAD")

    def create(self, *extra, **env):
        code, out, err = run(["create", "task", *extra], **env)
        self.assertEqual(code, 0, err)
        return fields(out)["path"]

    def marker(self, path):
        return os.path.join(wt_session.admin_dir(path), wt_session.MARKER)

    def test_create_records_opencode_session(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        self.assertTrue(path.startswith(os.path.join(self.state, "proj", "worktrees", "task-")))
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=path), self.git("rev-parse", "main"))
        code, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual((code, fields(out)["status"]), (0, "mine"))

    def test_create_records_claude_code_session(self):
        path = self.create(CLAUDE_CODE_SESSION_ID="claude-test-1")
        _, out, _ = run(["owner", path], CLAUDE_CODE_SESSION_ID="claude-test-1")
        self.assertEqual(fields(out)["status"], "mine")

    def test_other_session_and_tool(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        code, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_xyz")
        self.assertEqual((code, fields(out)["status"]), (1, "other"))
        _, out, _ = run(["owner", path], CLAUDE_CODE_SESSION_ID="ses_abc")
        self.assertEqual(fields(out)["status"], "other")

    def test_unknown_never_matches(self):
        path = self.create()
        code, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual((code, fields(out)["status"]), (3, "unknown"))
        code, out, _ = run(["owner", path])
        self.assertEqual((code, fields(out)["status"]), (3, "unknown"))
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        _, out, _ = run(["owner", path])
        self.assertEqual(fields(out)["status"], "unknown")

    def test_unrecorded_for_main_worktree(self):
        code, out, _ = run(["owner", self.repo], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual((code, fields(out)["status"]), (4, "unrecorded"))

    def test_both_session_ids_refused_before_creating(self):
        code, _, err = run(["create", "task"], OPENCODE_SESSION_ID="a", CLAUDE_CODE_SESSION_ID="b")
        self.assertEqual(code, 2)
        self.assertIn("refusing to guess", err)
        self.assertFalse(os.path.exists(self.state))

    def test_invalid_session_ids_refused(self):
        for value in ("bad id;", "unknown"):
            code, _, _ = run(["create", "task"], OPENCODE_SESSION_ID=value)
            self.assertEqual(code, 2, value)
        self.assertFalse(os.path.exists(self.state))

    def test_invalid_name_refused(self):
        code, _, _ = run(["create", "../escape"], OPENCODE_SESSION_ID="a")
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.state))

    def test_default_base_is_the_main_branch_not_a_tag(self):
        second = self.commit("second")
        self.git("tag", "main", self.first)
        path = self.create(OPENCODE_SESSION_ID="a")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=path), second)

    def test_explicit_base(self):
        self.commit("second")
        path = self.create("--base", self.first, OPENCODE_SESSION_ID="a")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=path), self.first)
        with open(self.marker(path), encoding="utf-8") as handle:
            self.assertIn(f"base={self.first}", handle.read())

    def test_inherited_git_dir_is_ignored(self):
        path = self.create(OPENCODE_SESSION_ID="a", GIT_DIR=os.devnull)
        self.assertTrue(os.path.isdir(path))
        os.environ.pop("GIT_DIR", None)

    def test_state_base_ignores_relative_xdg_state_home(self):
        with tempfile.TemporaryDirectory() as home, mock.patch.dict(
            os.environ, {"HOME": home, "XDG_STATE_HOME": "relative/state"}
        ):
            self.assertEqual(
                wt_session.state_base(), os.path.realpath(os.path.join(home, ".local/state"))
            )

    def test_marker_is_write_once(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        with self.assertRaises(FileExistsError):
            wt_session.write_marker(wt_session.admin_dir(path), {"version": "1"})

    def test_marker_copied_to_another_worktree_is_rejected(self):
        first = self.create(OPENCODE_SESSION_ID="ses_abc")
        second = self.create(OPENCODE_SESSION_ID="ses_xyz")
        with open(self.marker(first), encoding="utf-8") as handle:
            body = handle.read()
        with open(self.marker(second), "w", encoding="utf-8") as handle:
            handle.write(body)
        code, _, err = run(["owner", second], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("different path", err)

    def rewrite_marker(self, path, edit):
        with open(self.marker(path), encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        with open(self.marker(path), "w", encoding="utf-8") as handle:
            handle.write("\n".join(edit(lines)) + "\n")

    def assert_owner_error(self, path, text):
        code, out, err = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2, out)
        self.assertIn(text, err)

    def test_symlinked_marker_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        os.remove(self.marker(path))
        os.symlink(os.devnull, self.marker(path))
        self.assert_owner_error(path, "unsafe marker")

    def test_fifo_marker_is_rejected_without_blocking(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        os.remove(self.marker(path))
        os.mkfifo(self.marker(path))
        self.assert_owner_error(path, "not a regular file")

    def test_directory_marker_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        os.remove(self.marker(path))
        os.mkdir(self.marker(path))
        self.assert_owner_error(path, "not a regular file")

    def test_duplicate_key_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        self.rewrite_marker(path, lambda lines: [*lines, "session=other"])
        self.assert_owner_error(path, "malformed")

    def test_missing_field_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        self.rewrite_marker(path, lambda lines: [x for x in lines if not x.startswith("tool=")])
        self.assert_owner_error(path, "expected fields")

    def test_extra_field_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        self.rewrite_marker(path, lambda lines: [*lines, "status=mine"])
        self.assert_owner_error(path, "expected fields")

    def test_invalid_values_are_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        for old, new in (
            ("session=ses_abc", "session=x status=mine"),
            ("tool=opencode", "tool=other"),
            ("tool=opencode", "tool=unknown"),
        ):
            self.rewrite_marker(path, lambda lines, o=old, n=new: [n if x == o else x for x in lines])
            self.assert_owner_error(path, "invalid values")
            self.rewrite_marker(path, lambda lines, o=old, n=new: [o if x == n else x for x in lines])

    def test_non_utf8_marker_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        with open(self.marker(path), "wb") as handle:
            handle.write(b"version=1\n\xff\xfe\n")
        code, _, err = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_owner_requires_worktree_root(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        sub = os.path.join(path, "sub")
        os.mkdir(sub)
        self.assert_owner_error(sub, "not a worktree root")

    def test_owner_on_missing_path_is_an_error_not_a_traceback(self):
        self.assert_owner_error(os.path.join(self.state, "missing"), "error")

    def test_whoami(self):
        self.assertEqual(run(["whoami"])[0], 1)
        code, out, _ = run(["whoami"], CLAUDE_CODE_SESSION_ID="abc")
        self.assertEqual((code, out.strip()), (0, "tool=claude-code session=abc"))

    def test_removal_removes_the_record(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        admin = wt_session.admin_dir(path)
        self.git("worktree", "remove", path)
        self.assertFalse(os.path.exists(admin))

    def test_move_invalidates_the_record(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        moved = path + "-moved"
        self.git("worktree", "move", path, moved)
        self.assert_owner_error(moved, "different path")

    def test_failed_add_with_surviving_worktree_is_reported_as_preserved(self):
        hook = os.path.join(self.repo, ".git", "hooks", "post-checkout")
        with open(hook, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nexit 1\n")
        os.chmod(hook, 0o755)
        code, _, err = run(["create", "task"], OPENCODE_SESSION_ID="a")
        self.assertEqual(code, 2)
        created = glob.glob(os.path.join(self.state, "proj", "worktrees", "task-*"))
        self.assertEqual(len(created), 1)
        self.assertIn("preserved", err)

    def test_failure_after_add_is_reported_as_preserved(self):
        with mock.patch.object(wt_session, "write_marker", side_effect=PermissionError("denied")):
            code, _, err = run(["create", "task"], OPENCODE_SESSION_ID="a")
        self.assertEqual(code, 2)
        self.assertIn("unrecorded and preserved", err)
        self.assertEqual(len(glob.glob(os.path.join(self.state, "proj", "worktrees", "task-*"))), 1)

    def test_failed_add_without_worktree_is_a_plain_error(self):
        code, _, err = run(["create", "task", "--base", "no-such-rev"], OPENCODE_SESSION_ID="a")
        self.assertEqual(code, 2)
        self.assertNotIn("preserved", err)

    def test_symlinked_dot_git_pointing_to_its_own_admin_dir_verifies(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        admin = wt_session.admin_dir(path)
        os.remove(os.path.join(path, ".git"))
        os.symlink(admin, os.path.join(path, ".git"))
        wt_session.verify_pointers(path, admin)

    def test_admin_dir_naming_another_worktree_fails(self):
        first = self.create(OPENCODE_SESSION_ID="a")
        second = self.create(OPENCODE_SESSION_ID="b")
        admin = wt_session.admin_dir(first)
        with open(os.path.join(admin, "gitdir"), "w", encoding="utf-8") as handle:
            handle.write(os.path.join(second, ".git") + "\n")
        with self.assertRaises(wt_session.Failure):
            wt_session.verify_pointers(first, admin)

    @unittest.skipUnless(git_version() >= (2, 48), "needs --relative-paths")
    def test_relative_worktree_paths(self):
        self.git("config", "worktree.useRelativePaths", "true")
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        code, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual((code, fields(out)["status"]), (0, "mine"))


if __name__ == "__main__":
    unittest.main()
