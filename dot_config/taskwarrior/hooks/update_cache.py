#!/usr/bin/env -S uv run --quiet --script
"""
Taskwarrior cache update module.

This module provides functionality to update the local cache of task IDs and descriptions
for use by shell integrations (Nushell prompt preview, legacy Zsh highlighting).

Run this script directly to refresh the cache or via Taskwarrior hooks for automatic updates.

Cache files (default under XDG_CACHE_HOME):
    ${XDG_CACHE_HOME:-~/.cache}/taskwarrior/ids.list: Task IDs (one per line)
    ${XDG_CACHE_HOME:-~/.cache}/taskwarrior/desc.list: Task descriptions (format: ID:description)
"""

from dataclasses import dataclass, field
import json
import os
import subprocess
import sys
import time
from typing import List, Optional, Tuple


CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "taskwarrior",
)
IDS_CACHE_PATH = os.path.join(CACHE_DIR, "ids.list")
DESC_CACHE_PATH = os.path.join(CACHE_DIR, "desc.list")
LAST_UPDATE_PATH = os.path.join(CACHE_DIR, ".last_update")
MIN_UPDATE_INTERVAL_SECONDS = 5


@dataclass(frozen=True)
class Task:
    id: int
    description: str
    status: str
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def should_skip_update(now: float) -> bool:
    try:
        last_update = os.path.getmtime(LAST_UPDATE_PATH)
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return now - last_update < MIN_UPDATE_INTERVAL_SECONDS


def touch_update_marker(now: float) -> None:
    with open(LAST_UPDATE_PATH, "a"):
        os.utime(LAST_UPDATE_PATH, (now, now))


def write_if_changed(path: str, content: str) -> None:
    try:
        with open(path, "r") as existing_file:
            if existing_file.read() == content:
                return
    except FileNotFoundError:
        pass

    with open(path, "w") as target_file:
        target_file.write(content)


def task_from_dict(data: dict) -> Optional[Task]:
    if not isinstance(data, dict):
        return None

    task_id = data.get("id")
    description = data.get("description")
    status = data.get("status")

    if not isinstance(task_id, int) or task_id <= 0:
        return None
    if not isinstance(description, str) or not description:
        return None
    if not isinstance(status, str) or not status:
        return None

    project = data.get("project")
    if project is not None and not isinstance(project, str):
        project = None

    tags_value = data.get("tags") or []
    if not isinstance(tags_value, list):
        tags_value = []
    tags = [tag for tag in tags_value if isinstance(tag, str)]

    return Task(
        id=task_id,
        description=description,
        status=status,
        project=project,
        tags=tags,
    )


def load_tasks() -> List[Task]:
    output = subprocess.check_output(
        ["task", "status:pending", "-WAITING", "export"],
        stderr=subprocess.DEVNULL,
    )
    raw_tasks = json.loads(output)
    tasks: List[Task] = []
    for entry in raw_tasks:
        task = task_from_dict(entry)
        if task is not None:
            tasks.append(task)
    return tasks


def build_cache_contents(tasks: List[Task]) -> Tuple[str, str]:
    ids: List[str] = []
    descs: List[str] = []

    for task in tasks:
        task_id_str = str(task.id)
        ids.append(task_id_str)
        descs.append(f"{task_id_str}:{task.description}")

    return "\n".join(ids), "\n".join(descs)


def update_cache() -> None:
    """
    Update the Taskwarrior cache files with current pending tasks.

    Reads all pending non-waiting tasks from Taskwarrior and updates two cache files:
    - ids.list: Contains only task IDs
    - desc.list: Contains task IDs and descriptions in "ID:description" format

    The cache is used by:
    - Nushell prompt preview (autoload/08-taskwarrior.nu)
    - Legacy Zsh integration (archived under archive/zsh)

    Note:
        Uses -WAITING filter to match 'task list' behavior (excludes currently waiting tasks).
        Silently fails if task command fails to prevent blocking task operations.
        Skips refresh if the last update was recent to reduce hook latency.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    now = time.time()

    if should_skip_update(now):
        return

    try:
        # Get pending tasks in JSON format
        # Use -WAITING (virtual tag) to match 'task list' behavior
        # -wait excludes tasks with wait attribute set (even if past)
        # -WAITING excludes only currently waiting tasks
        tasks = load_tasks()
        ids_content, descs_content = build_cache_contents(tasks)

        write_if_changed(IDS_CACHE_PATH, ids_content)
        write_if_changed(DESC_CACHE_PATH, descs_content)
        touch_update_marker(now)

    except subprocess.CalledProcessError:
        # Task command failed - silently ignore to prevent blocking task operations
        pass
    except json.JSONDecodeError:
        # Invalid JSON from task command - silently ignore
        pass
    except Exception:
        # Any other error - silently ignore to ensure hooks don't break task operations
        pass


def process_hook_input() -> None:
    """
    Process Taskwarrior hook input and output the appropriate JSON.

    Taskwarrior hooks receive JSON input via stdin:
    - on-add: Receives 1 JSON object (new task)
    - on-modify: Receives 2 JSON objects (old task, new task)

    This function:
    1. Reads all input
    2. Outputs the last JSON object (the new/modified task)
    3. Triggers cache update

    The output is required for Taskwarrior to complete the operation.
    """
    stdin_data = sys.stdin.read()
    lines = [line for line in stdin_data.split("\n") if line.strip()]

    if lines:
        # Output the last JSON object (new task for on-add, modified task for on-modify)
        sys.stdout.write(lines[-1].rstrip("\n") + "\n")
        sys.stdout.flush()

    # Update cache after outputting (non-blocking)
    update_cache()


def main() -> None:
    if "--update-only" in sys.argv[1:]:
        update_cache()
        return

    if sys.stdin.isatty():
        update_cache()
        return

    process_hook_input()


if __name__ == "__main__":
    main()
