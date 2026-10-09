#!/usr/bin/env python3
"""Report the owner and liveness of every linked worktree. Read-only.

States, in precedence order:
  ACTIVE         a positive liveness signal: the recorded agent process is alive
                 with the recorded start time, or the recorded session changed
                 within --active-hours.
  UNKNOWN        no description, detached HEAD, `session=unknown`, or the session
                 lookup failed. A failed lookup is never evidence of idleness.
  LEGACY         a description without a `session=` trailer (created before
                 session tracking); owner text only.
  IDLE-MERGED    liveness known to be negative, HEAD has commits beyond the
                 recorded base and is contained in --base, and tracked/untracked
                 state is clean. Prints a dry-run `safe-worktree-remove.py` command.
  IDLE-UNMERGED  liveness known to be negative but the work is not contained in
                 --base, or is dirty. Never gets a removal command.

Every git call uses --no-optional-locks semantics (GIT_OPTIONAL_LOCKS=0), so a
running agent's index is never locked. The audit does not take
`main-integration.lock`. Squash- or rebase-integrated work is not detected as
merged. A worktree created by a subagent records the child session id; the
lookup follows OpenCode parent/child sessions, but Claude Code subagent ids
are unverified.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worktree_meta as meta

REMOVE_HELPER = "safe-worktree-remove.py"


@dataclass
class Row:
    path: str
    branch: str | None
    state: str
    reason: str
    client: str | None = None
    session: str | None = None
    session_idle_hours: float | None = None
    ahead_of_base: bool | None = None
    contained_in_base: bool | None = None
    changes: dict[str, int] = field(default_factory=dict)
    command: list[str] | None = None


def claude_roots(env: dict[str, str]) -> list[Path]:
    roots = [env.get("CLAUDE_CONFIG_DIR"), str(Path.home() / ".claude")]
    data = env.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    roots.append(str(Path(data) / "claude"))
    return [Path(r) for r in roots if r]


def claude_last_activity(session: str, env: dict[str, str]) -> float | None:
    times = [
        hit.stat().st_mtime
        for root in claude_roots(env)
        for hit in (root / "projects").glob(f"*/{session}.jsonl")
    ]
    return max(times) if times else None


def opencode_last_activity(session: str, env: dict[str, str]) -> float | None:
    data = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "opencode"
    best: float | None = None
    for name in ("opencode.db", "opencode-stable.db"):
        db = data / name
        if not db.is_file():
            continue
        try:
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2) as conn:
                rows = conn.execute(
                    """
                    WITH RECURSIVE up(id, parent_id, t) AS (
                        SELECT id, parent_id, time_updated FROM session WHERE id = ?
                        UNION SELECT s.id, s.parent_id, s.time_updated
                        FROM session s JOIN up ON s.id = up.parent_id),
                    down(id, t) AS (
                        SELECT id, time_updated FROM session WHERE id = ?
                        UNION SELECT s.id, s.time_updated
                        FROM session s JOIN down ON s.parent_id = down.id)
                    SELECT max(t) FROM (SELECT t FROM up UNION ALL SELECT t FROM down)
                    """,
                    (session, session),
                ).fetchall()
        except sqlite3.Error:
            continue
        value = rows[0][0] if rows else None
        if value is not None:
            seconds = value / 1000.0
            best = seconds if best is None else max(best, seconds)
    return best


def session_age_hours(client: str, session: str, env: dict[str, str], now: float) -> float | None:
    lookup = {"claude": claude_last_activity, "opencode": opencode_last_activity}.get(client)
    if lookup is None or not meta.SESSION_RE[client].match(session):
        return None
    last = lookup(session, env)
    return None if last is None else max(0.0, (now - last) / 3600.0)


def pid_state(token: str | None, now: float) -> str:
    """'alive' (positive), 'dead' (known negative), or 'none' (nothing recorded/unparsable)."""
    if not token or "@" not in token:
        return "none"
    pid_text, _, start_text = token.partition("@")
    if not (pid_text.isdigit() and start_text.isdigit()):
        return "none"
    start = meta.process_start_epoch(int(pid_text), now)
    if start is not None and abs(start - int(start_text)) <= meta.PID_START_TOLERANCE:
        return "alive"
    return "dead"


def worktrees(repo: Path) -> list[dict[str, str]]:
    out = meta.git(repo, "worktree", "list", "--porcelain").stdout
    entries: list[dict[str, str]] = []
    for block in out.strip().split("\n\n"):
        entry: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            entry[key] = value
        if "worktree" in entry:
            entries.append(entry)
    return entries[1:]  # the first entry is the main worktree


def change_counts(path: str) -> dict[str, int]:
    out = meta.git(
        path, "status", "--porcelain", "--untracked-files=all", "--ignored=matching", check=False
    ).stdout
    counts = {"tracked": 0, "untracked": 0, "ignored": 0}
    for line in out.splitlines():
        counts["ignored" if line.startswith("!!") else "untracked" if line.startswith("??") else "tracked"] += 1
    return counts


def audit(repo: Path, base: str, active_hours: float, env: dict[str, str], now: float, helper: str) -> list[Row]:
    rows: list[Row] = []
    for entry in worktrees(repo):
        path, ref = entry["worktree"], entry.get("branch")
        branch = ref.removeprefix("refs/heads/") if ref else None
        row = Row(path=path, branch=branch, state="UNKNOWN", reason="")
        rows.append(row)
        if branch is None:
            row.reason = "detached HEAD"
            continue
        text = meta.git(repo, "config", "--get", f"branch.{branch}.description", check=False).stdout.strip()
        task, trailer = meta.parse_description(text)
        row.client, row.session = trailer.get("client"), trailer.get("session")
        if not text:
            row.reason = "no branch description"
            continue
        row.changes = change_counts(path)

        pid = pid_state(trailer.get("pid"), now)
        age = None
        if row.client and row.session and row.session != meta.UNKNOWN:
            age = session_age_hours(row.client, row.session, env, now)
        row.session_idle_hours = None if age is None else round(age, 1)
        if pid == "alive" or (age is not None and age < active_hours):
            row.state, row.reason = "ACTIVE", "agent process alive" if pid == "alive" else "session recently updated"
            continue
        if row.session is None:
            row.state, row.reason = "LEGACY", "description has no session trailer"
            continue
        if age is None:
            row.reason = "session unknown or lookup failed"
            continue

        base_oid = trailer.get("base")
        head = entry.get("HEAD", "")
        row.ahead_of_base = bool(base_oid) and head != base_oid and (
            meta.git(repo, "merge-base", "--is-ancestor", base_oid, head, check=False).returncode == 0
        )
        row.contained_in_base = (
            meta.git(repo, "merge-base", "--is-ancestor", head, base, check=False).returncode == 0
        )
        clean = row.changes.get("tracked", 0) == 0 and row.changes.get("untracked", 0) == 0
        if row.ahead_of_base and row.contained_in_base and clean:
            row.state, row.reason = "IDLE-MERGED", f"session idle {row.session_idle_hours}h"
            row.command = [
                sys.executable, str(Path(helper) / REMOVE_HELPER), path,
                "--expect-owner", task, "--base", base, "--dry-run",
            ]
        else:
            row.state, row.reason = "IDLE-UNMERGED", f"session idle {row.session_idle_hours}h"
    return rows


def render(rows: list[Row]) -> str:
    if not rows:
        return "no linked worktrees"
    lines = []
    for row in rows:
        extra = []
        if row.changes and any(row.changes.values()):
            extra.append("changes=" + ",".join(f"{k}:{v}" for k, v in row.changes.items() if v))
        lines.append(f"{row.state:<14} {row.branch or '(detached)'}  {row.path}")
        lines.append(f"{'':<14} client={row.client or '-'} session={row.session or '-'} {row.reason} {' '.join(extra)}".rstrip())
        if row.command:
            lines.append(f"{'':<14} dry-run: {' '.join(shlex.quote(part) for part in row.command)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="any path inside the repository (default: cwd)")
    parser.add_argument("--base", default="main", help="integration branch (default: main)")
    parser.add_argument("--active-hours", type=float, default=2.0)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    if meta.git(repo, "rev-parse", "--verify", f"refs/heads/{args.base}", check=False).returncode != 0:
        print(f"error: local branch {args.base!r} does not exist; pass --base", file=sys.stderr)
        return 2
    rows = audit(repo, args.base, args.active_hours, dict(os.environ), time.time(), str(Path(__file__).resolve().parent))
    print(json.dumps([asdict(r) for r in rows], indent=2) if args.json else render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
