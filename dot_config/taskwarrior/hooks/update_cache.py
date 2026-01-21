#!/usr/bin/env python3
"""
Taskwarrior cache update module.

This module provides functionality to update the local cache of task IDs and descriptions
for use by Zsh integration (syntax highlighting, completion, preview).

Cache files:
    ~/.cache/taskwarrior/ids.list: Task IDs (one per line)
    ~/.cache/taskwarrior/desc.list: Task descriptions (format: ID:description)
"""

import json
import os
import subprocess
import sys
from typing import List, Tuple


def update_cache() -> None:
    """
    Update the Taskwarrior cache files with current pending tasks.
    
    Reads all pending non-waiting tasks from Taskwarrior and updates two cache files:
    - ids.list: Contains only task IDs
    - desc.list: Contains task IDs and descriptions in "ID:description" format
    
    The cache is used by:
    - Zsh fast-syntax-highlighting (chroma-task.ch) for ID validation
    - Zsh functions (.functions) for task preview and completion
    
    Note:
        Uses -WAITING filter to match 'task list' behavior (excludes currently waiting tasks).
        Silently fails if task command fails to prevent blocking task operations.
    """
    cache_dir = os.path.expanduser("~/.cache/taskwarrior")
    os.makedirs(cache_dir, exist_ok=True)
    
    try:
        # Get pending tasks in JSON format
        # Use -WAITING (virtual tag) to match 'task list' behavior
        # -wait excludes tasks with wait attribute set (even if past)
        # -WAITING excludes only currently waiting tasks
        output = subprocess.check_output(
            ["task", "status:pending", "-WAITING", "export"],
            stderr=subprocess.DEVNULL
        )
        tasks = json.loads(output)
        
        ids: List[str] = []
        descs: List[str] = []
        
        for task in tasks:
            if "id" in task and task["id"] != 0:
                task_id = str(task["id"])
                ids.append(task_id)
                descs.append(f"{task_id}:{task['description']}")
        
        # Write cache files
        with open(os.path.join(cache_dir, "ids.list"), "w") as f:
            f.write("\n".join(ids))
        
        with open(os.path.join(cache_dir, "desc.list"), "w") as f:
            f.write("\n".join(descs))
            
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
    lines = [line for line in stdin_data.split('\n') if line.strip()]
    
    if lines:
        # Output the last JSON object (new task for on-add, modified task for on-modify)
        sys.stdout.write(lines[-1].rstrip('\n') + "\n")
        sys.stdout.flush()
    
    # Update cache after outputting (non-blocking)
    update_cache()


if __name__ == "__main__":
    process_hook_input()
