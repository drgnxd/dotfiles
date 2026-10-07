#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
import json
import subprocess
from pathlib import Path

MARKER_DIR = Path.home() / ".local/state/automation-failures"
LABEL_PREFIX = "com.drgnxd."

# launchctl list: PID, last exit status, label
rows = subprocess.run(
    ["/bin/launchctl", "list"], capture_output=True, text=True
).stdout.splitlines()[1:]
jobs = {}
for row in rows:
    parts = row.split("\t")
    if len(parts) == 3 and parts[2].startswith(LABEL_PREFIX):
        jobs[parts[2].removeprefix(LABEL_PREFIX)] = parts[1]

markers = {}
for path in sorted(MARKER_DIR.glob("*.json")):
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        data = {}
    markers[data.get("job", path.stem)] = data.get("timestamp", "?")

failing = set(markers) | {j for j, status in jobs.items() if status not in ("0", "-")}
print(f"⚠ {len(failing)}" if failing else "✓")
print("---")
for job in sorted(jobs.keys() | markers.keys()):
    status = jobs.get(job)
    notes = []
    if job in markers:
        notes.append(f"marker {markers[job][:16]}")
    if status is None:
        notes.append("launchd未登録")
    elif status not in ("0", "-"):
        notes.append(f"exit {status}")
    print(f"{'⚠' if job in failing else '✓'} {job}" + (f"  ({', '.join(notes)})" if notes else ""))
