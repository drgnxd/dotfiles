"""Shared entrypoint helpers for Taskwarrior hook scripts."""

from update_cache import process_hook_input


def run_hook_entrypoint() -> None:
    process_hook_input()
