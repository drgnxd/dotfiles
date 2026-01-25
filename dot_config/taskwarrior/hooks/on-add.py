#!/usr/bin/env python3
"""
Taskwarrior on-add hook.

This hook is triggered when a task is added.
It forwards the new task JSON to Taskwarrior and updates the cache.
"""

import sys
import os

# Add hooks directory to Python path for imports
hooks_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, hooks_dir)

from update_cache import process_hook_input  # noqa: E402

if __name__ == "__main__":
    process_hook_input()
