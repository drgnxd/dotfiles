#!/usr/bin/env -S uv run --quiet --script
"""
Taskwarrior on-add hook.

Delegates to the shared hook entrypoint implementation.
"""

from hook_entrypoint import run_hook_entrypoint

if __name__ == "__main__":
    run_hook_entrypoint()
