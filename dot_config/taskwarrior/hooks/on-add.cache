#!/usr/bin/env python3
import sys
import json
import os

def update_cache():
    cache_dir = os.path.expanduser("~/.cache/taskwarrior")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Run task command to get pending IDs and descriptions
    import subprocess
    try:
        # Get pending tasks in JSON format
        # Use -WAITING (virtual tag) to match 'task list' behavior
        # -wait excludes tasks with wait attribute set (even if past)
        # -WAITING excludes only currently waiting tasks
        output = subprocess.check_output(["task", "status:pending", "-WAITING", "export"], stderr=subprocess.DEVNULL)
        tasks = json.loads(output)
        
        ids = []
        descs = []
        for t in tasks:
            if "id" in t and t["id"] != 0:
                ids.append(str(t["id"]))
                descs.append(f"{t['id']}:{t['description']}")
        
        with open(os.path.join(cache_dir, "ids.list"), "w") as f:
            f.write("\n".join(ids))
        with open(os.path.join(cache_dir, "desc.list"), "w") as f:
            f.write("\n".join(descs))
    except Exception:
        pass

if __name__ == "__main__":
    # Taskwarrior on-add receives 1 JSON; on-modify receives 2 (old, new).
    # Output only the new task JSON (last object) to stdout, then refresh cache.
    stdin_data = sys.stdin.read()
    lines = [l for l in stdin_data.split('\n') if l.strip()]

    if lines:
        sys.stdout.write(lines[-1].rstrip('\n') + "\n")
        sys.stdout.flush()

    update_cache()

