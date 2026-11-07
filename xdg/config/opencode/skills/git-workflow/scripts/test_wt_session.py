import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wt_session

SESSION_VARS = ("OPENCODE_SESSION_ID", "CLAUDE_CODE_SESSION_ID")


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
    return dict(
        pair.split("=", 1) for line in stdout.split() for pair in [line] if "=" in pair
    )


class WtSessionTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = os.path.realpath(tmp.name)
        self.repo = os.path.join(root, "proj")
        os.mkdir(self.repo)
        self.git("init", "-q", "-b", "main")
        self.git(
            "-c", "user.name=t", "-c", "user.email=t@example.invalid",
            "commit", "-q", "--allow-empty", "-m", "seed",
        )
        self.state = os.path.join(root, "state")
        for key, value in (
            ("XDG_STATE_HOME", self.state),
            ("GIT_CONFIG_GLOBAL", os.devnull),
            ("GIT_CONFIG_SYSTEM", os.devnull),
        ):
            self.addCleanup(self._restore, key, os.environ.get(key))
            os.environ[key] = value
        previous = os.getcwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(self.repo)

    @staticmethod
    def _restore(key, value):
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def create(self, **env):
        code, out, err = run(["create", "task"], **env)
        self.assertEqual(code, 0, err)
        return fields(out)["path"]

    def test_create_records_opencode_session(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        self.assertTrue(path.startswith(os.path.join(self.state, "proj", "worktrees", "task-")))
        self.assertEqual(
            subprocess.run(
                ["git", "-C", path, "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip(),
            self.git("rev-parse", "main"),
        )
        code, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual((code, fields(out)["status"]), (0, "mine"))

    def test_create_records_claude_code_session(self):
        path = self.create(CLAUDE_CODE_SESSION_ID="1f25cac1-96ad")
        _, out, _ = run(["owner", path], CLAUDE_CODE_SESSION_ID="1f25cac1-96ad")
        self.assertEqual(fields(out)["status"], "mine")

    def test_other_session_and_tool(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        _, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_xyz")
        self.assertEqual(fields(out)["status"], "other")
        _, out, _ = run(["owner", path], CLAUDE_CODE_SESSION_ID="ses_abc")
        self.assertEqual(fields(out)["status"], "other")

    def test_unknown_when_either_side_has_no_session(self):
        path = self.create()
        _, out, _ = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(fields(out)["status"], "unknown")
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        _, out, _ = run(["owner", path])
        self.assertEqual(fields(out)["status"], "unknown")

    def test_unrecorded_for_main_worktree(self):
        _, out, _ = run(["owner", self.repo], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(fields(out)["status"], "unrecorded")

    def test_both_session_ids_refused_before_creating(self):
        code, _, err = run(
            ["create", "task"], OPENCODE_SESSION_ID="a", CLAUDE_CODE_SESSION_ID="b"
        )
        self.assertEqual(code, 2)
        self.assertIn("refusing to guess", err)
        self.assertFalse(os.path.exists(self.state))

    def test_invalid_session_id_refused(self):
        code, _, _ = run(["create", "task"], OPENCODE_SESSION_ID="bad id;")
        self.assertEqual(code, 2)

    def test_invalid_name_refused(self):
        code, _, _ = run(["create", "../escape"], OPENCODE_SESSION_ID="a")
        self.assertEqual(code, 2)
        self.assertFalse(os.path.exists(self.state))

    def test_marker_is_write_once(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        with self.assertRaises(FileExistsError):
            wt_session.write_marker(wt_session.admin_dir(path), {"version": "1"})

    def test_marker_copied_to_another_worktree_is_rejected(self):
        first = self.create(OPENCODE_SESSION_ID="ses_abc")
        second = self.create(OPENCODE_SESSION_ID="ses_xyz")
        source = os.path.join(wt_session.admin_dir(first), wt_session.MARKER)
        target = os.path.join(wt_session.admin_dir(second), wt_session.MARKER)
        with open(source, encoding="utf-8") as handle:
            body = handle.read()
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(body)
        code, _, err = run(["owner", second], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("different path", err)

    def test_symlinked_marker_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        marker = os.path.join(wt_session.admin_dir(path), wt_session.MARKER)
        os.remove(marker)
        os.symlink(os.devnull, marker)
        code, _, err = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("unsafe marker", err)

    def test_malformed_marker_is_rejected(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        marker = os.path.join(wt_session.admin_dir(path), wt_session.MARKER)
        with open(marker, "w", encoding="utf-8") as handle:
            handle.write("version=1\nsession=a\nsession=b\n")
        code, _, err = run(["owner", path], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("malformed", err)

    def test_owner_requires_worktree_root(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        sub = os.path.join(path, "sub")
        os.mkdir(sub)
        code, _, err = run(["owner", sub], OPENCODE_SESSION_ID="ses_abc")
        self.assertEqual(code, 2)
        self.assertIn("not a worktree root", err)

    def test_whoami(self):
        self.assertEqual(run(["whoami"])[0], 1)
        code, out, _ = run(["whoami"], CLAUDE_CODE_SESSION_ID="abc")
        self.assertEqual((code, out.strip()), (0, "tool=claude-code session=abc"))

    def test_removal_removes_the_record(self):
        path = self.create(OPENCODE_SESSION_ID="ses_abc")
        admin = wt_session.admin_dir(path)
        self.git("worktree", "remove", path)
        self.assertFalse(os.path.exists(admin))


if __name__ == "__main__":
    unittest.main()
