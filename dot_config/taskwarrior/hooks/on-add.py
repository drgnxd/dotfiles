#!/usr/bin/env -S uv run --quiet --script
"""
Taskwarrior on-add/on-modify hook.

This entrypoint is shared by both on-add.py and on-modify.py.
It forwards the newest task JSON to Taskwarrior and updates the cache.
"""

import sys
import os

# Add hooks directory to Python path for imports
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, hooks_dir)

from update_cache import process_hook_input  # noqa: E402

if __name__ == "__main__":
    process_hook_input()
