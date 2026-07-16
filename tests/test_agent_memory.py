from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "agent_memory" / "agent_memory.py"


class AgentMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.memory_dir = self.root / "memory"
        clean_environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("AGENT_MEMORY_")
        }
        self.environment = {
            **clean_environment,
            "AGENT_MEMORY_DIR": str(self.memory_dir),
            "AGENT_MEMORY_GIT": "0",
            "AGENT_MEMORY_OWNER_ID": "test-user",
            "AGENT_MEMORY_MAINTENANCE_DAYS": "0",
            "AGENT_MEMORY_MAINTENANCE_MIN_FACTS": "2",
        }

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_cli(
        self,
        *arguments: str,
        cwd: Path | None = None,
        input_text: str | None = None,
        environment: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(CLI), *arguments],
            cwd=cwd or self.root,
            env=environment or self.environment,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"command failed with {result.returncode}: {result.stderr}\n{result.stdout}"
            )
        return result

    def create_project(
        self, name: str, *, parent: Path | None = None, remote: str | None = None
    ) -> Path:
        project = (parent or self.root) / name
        project.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "--quiet", str(project)],
            check=True,
            capture_output=True,
            text=True,
        )
        if remote is not None:
            subprocess.run(
                ["git", "-C", str(project), "remote", "add", "origin", remote],
                check=True,
                capture_output=True,
                text=True,
            )
        return project

    def exported_events(self) -> list[dict[str, Any]]:
        result = self.run_cli("export")
        return [json.loads(line) for line in result.stdout.splitlines() if line]

    def test_migrates_legacy_without_guessing_project_identity(self) -> None:
        self.memory_dir.mkdir()
        (self.memory_dir / "memory.md").write_text(
            "- 2026-07-01T00:00:00Z User prefers concise answers.\n"
            "- 2026-07-02T00:00:00Z In alpha, use uv for Python.\n",
            encoding="utf-8",
        )
        project = self.create_project("alpha")

        result = self.run_cli("read", "--query", "uv Python", cwd=project)
        all_memories = self.run_cli("read", "--all")

        self.assertNotIn("In alpha, use uv for Python.", result.stdout)
        self.assertIn("In alpha, use uv for Python.", all_memories.stdout)
        self.assertTrue((self.memory_dir / "memory.sqlite3").is_file())
        self.assertTrue((self.memory_dir / "events.jsonl").is_file())
        event_types = [event["event_type"] for event in self.exported_events()]
        self.assertEqual(event_types, ["memory.imported", "memory.imported"])

        self.run_cli("rescope-legacy", "alpha", cwd=project)
        adopted = self.run_cli("read", "--query", "uv Python", cwd=project)
        self.assertIn("In alpha, use uv for Python.", adopted.stdout)

    def test_scoped_retrieval_and_duplicate_append(self) -> None:
        alpha = self.create_project("alpha")
        beta = self.create_project("beta")
        self.run_cli("append", "--scope", "global", "--pin", "Prefer concise output.")
        self.run_cli("append", "In alpha, use uv.", cwd=alpha)
        duplicate = self.run_cli("append", "In alpha, use uv.", cwd=alpha)

        alpha_read = self.run_cli("read", "--query", "uv", cwd=alpha)
        beta_read = self.run_cli("read", "--query", "uv", cwd=beta)

        self.assertIn("Memory already exists", duplicate.stdout)
        self.assertIn("In alpha, use uv.", alpha_read.stdout)
        self.assertIn("Prefer concise output.", alpha_read.stdout)
        self.assertNotIn("In alpha, use uv.", beta_read.stdout)
        self.assertIn("Prefer concise output.", beta_read.stdout)
        self.assertEqual(len(self.exported_events()), 2)

    def test_project_identity_uses_sanitized_remote_not_directory_name(self) -> None:
        first = self.create_project(
            "shared",
            parent=self.root / "one",
            remote="https://user:secret@example.com/org/one.git?token=value#fragment",
        )
        second = self.create_project(
            "shared",
            parent=self.root / "two",
            remote="https://example.com/org/two.git",
        )
        self.run_cli("append", "Private project fact.", cwd=first)
        subprocess.run(
            [
                "git",
                "-C",
                str(first),
                "remote",
                "set-url",
                "origin",
                "git@example.com:org/one.git",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        unrelated = self.run_cli("read", "--query", "Private project", cwd=second)
        same_project = self.run_cli("read", "--query", "Private project", cwd=first)
        event = self.exported_events()[0]
        serialized = json.dumps(event)

        self.assertNotIn("Private project fact.", unrelated.stdout)
        self.assertIn("Private project fact.", same_project.stdout)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("token=value", serialized)
        project_scope = next(
            scope for scope in event["scopes"] if scope["type"] == "project"
        )
        self.assertEqual(project_scope["id"], "example.com/org/one")

    def test_maintenance_retracts_omitted_fact_and_checks_generation(self) -> None:
        self.run_cli("append", "--scope", "global", "Keep this fact.")
        self.run_cli("append", "--scope", "global", "Remove this fact.")
        maintenance = self.run_cli("read", "--maintenance")
        generation_match = re.search(r"GENERATION: ([0-9a-f]{64})", maintenance.stderr)
        if generation_match is None:
            self.fail(f"missing generation token: {maintenance.stderr}")
        generation = generation_match.group(1)
        retained = next(
            line
            for line in maintenance.stdout.splitlines()
            if json.loads(line)["claim"] == "Keep this fact."
        )

        self.run_cli("maintain", generation, input_text=retained + "\n")
        active = self.run_cli("read", "--all")
        stale = self.run_cli(
            "maintain", generation, input_text=retained + "\n", check=False
        )

        self.assertIn("Keep this fact.", active.stdout)
        self.assertNotIn("Remove this fact.", active.stdout)
        self.assertEqual(stale.returncode, 75)
        self.assertIn(
            "memory.retracted",
            [event["event_type"] for event in self.exported_events()],
        )

    def test_maintenance_preserves_project_scope_when_claim_changes(self) -> None:
        alpha = self.create_project("alpha")
        beta = self.create_project("beta")
        self.run_cli("append", "Original project fact.", cwd=alpha)
        self.run_cli("append", "Other project fact.", cwd=beta)
        maintenance = self.run_cli("read", "--maintenance", cwd=alpha)
        self.assertNotIn("Other project fact.", maintenance.stdout)
        generation_match = re.search(r"GENERATION: ([0-9a-f]{64})", maintenance.stderr)
        if generation_match is None:
            self.fail(f"missing generation token: {maintenance.stderr}")
        replacement = json.loads(maintenance.stdout)
        replacement["claim"] = "Updated project fact."
        escaped = dict(replacement)
        escaped["scopes"] = [
            scope for scope in replacement["scopes"] if scope["type"] == "user"
        ]

        rejected = self.run_cli(
            "maintain",
            generation_match.group(1),
            input_text=json.dumps(escaped) + "\n",
            cwd=alpha,
            check=False,
        )

        self.run_cli(
            "maintain",
            generation_match.group(1),
            input_text=json.dumps(replacement) + "\n",
            cwd=alpha,
        )
        alpha_read = self.run_cli("read", "--query", "Updated project", cwd=alpha)
        beta_read = self.run_cli("read", "--query", "Updated project", cwd=beta)
        beta_preserved = self.run_cli("read", "--query", "Other project", cwd=beta)

        self.assertEqual(rejected.returncode, 64)
        self.assertIn("cannot move", rejected.stderr)
        self.assertIn("Updated project fact.", alpha_read.stdout)
        self.assertNotIn("Updated project fact.", beta_read.stdout)
        self.assertIn("Other project fact.", beta_preserved.stdout)

    def test_bundle_round_trip_and_dry_run(self) -> None:
        self.run_cli("append", "--scope", "global", "Portable fact.")
        bundle = self.root / "bundle"
        self.run_cli("export", "--output", str(bundle))

        self.assertTrue((bundle / "manifest.json").is_file())
        self.assertTrue((bundle / "events.jsonl").is_file())
        self.assertTrue((bundle / "checksums.sha256").is_file())
        destination_environment = {
            **self.environment,
            "AGENT_MEMORY_DIR": str(self.root / "destination"),
        }
        dry_run = self.run_cli(
            "import", str(bundle), "--dry-run", environment=destination_environment
        )
        empty = self.run_cli("read", "--all", environment=destination_environment)
        imported = self.run_cli(
            "import", str(bundle), environment=destination_environment
        )
        restored = self.run_cli("read", "--all", environment=destination_environment)

        self.assertIn("Validated 1 new events", dry_run.stdout)
        self.assertEqual(empty.stdout, "")
        self.assertIn("Imported 1 new events", imported.stdout)
        self.assertIn("Portable fact.", restored.stdout)

    def test_rejects_tampered_bundle(self) -> None:
        self.run_cli("append", "--scope", "global", "Portable fact.")
        bundle = self.root / "bundle"
        self.run_cli("export", "--output", str(bundle))
        with (bundle / "events.jsonl").open("a", encoding="utf-8") as output:
            output.write("{}\n")

        result = self.run_cli("import", str(bundle), check=False)

        self.assertEqual(result.returncode, 65)
        self.assertIn("checksum failed", result.stderr)

    def test_startup_repairs_missing_portable_mirror(self) -> None:
        self.run_cli("append", "--scope", "global", "Recoverable fact.")
        (self.memory_dir / "events.jsonl").unlink()

        self.run_cli("read", "--query", "Recoverable")

        restored = (self.memory_dir / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("Recoverable fact.", restored)

    def test_rejects_non_finite_confidence_and_orphan_update(self) -> None:
        confidence = self.run_cli(
            "append",
            "--scope",
            "global",
            "--confidence",
            "nan",
            "Invalid confidence.",
            check=False,
        )
        self.assertEqual(confidence.returncode, 64)

        self.run_cli("append", "--scope", "global", "Source fact.")
        orphan = self.exported_events()[0]
        orphan["event_id"] = str(uuid.uuid4())
        orphan["event_type"] = "memory.updated"
        orphan["memory_id"] = str(uuid.uuid4())
        orphan.pop("sequence")
        source = self.root / "orphan.jsonl"
        source.write_text(json.dumps(orphan) + "\n", encoding="utf-8")
        destination_environment = {
            **self.environment,
            "AGENT_MEMORY_DIR": str(self.root / "destination"),
        }

        result = self.run_cli(
            "import", str(source), environment=destination_environment, check=False
        )

        self.assertEqual(result.returncode, 64)
        self.assertIn("unknown memory", result.stderr)

    def test_rejects_multiline_fact(self) -> None:
        result = self.run_cli(
            "append", input_text="first line\nsecond line\n", check=False
        )

        self.assertEqual(result.returncode, 64)
        self.assertIn("single line", result.stderr)

    def test_parallel_appends_are_serialized(self) -> None:
        def append_fact(index: int) -> None:
            self.run_cli("append", "--scope", "global", f"Parallel fact {index}.")

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(append_fact, range(16)))

        events = self.exported_events()
        self.assertEqual(len(events), 16)
        self.assertEqual([event["sequence"] for event in events], list(range(1, 17)))

    def test_retrieval_prefers_latest_memory_and_honors_strict_budget(self) -> None:
        self.run_cli("append", "--scope", "global", "Old fact.")
        self.run_cli("append", "--scope", "global", "New fact.")

        result = self.run_cli("read", "--scope", "global", "--budget-tokens", "5")

        self.assertIn("New fact.", result.stdout)
        self.assertNotIn("Old fact.", result.stdout)

    def test_remote_memory_repository_excludes_operational_database(self) -> None:
        self.memory_dir.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", str(self.memory_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.memory_dir),
                "remote",
                "add",
                "origin",
                "https://example.com/private/memory.git",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        environment = {**self.environment, "AGENT_MEMORY_GIT": "1"}

        self.run_cli(
            "append",
            "--scope",
            "global",
            "Private fact.",
            environment=environment,
        )
        status = subprocess.run(
            ["git", "-C", str(self.memory_dir), "status", "--short"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        self.assertNotIn("memory.sqlite3", status)
        self.assertIn("events.jsonl", status)


if __name__ == "__main__":
    unittest.main()
