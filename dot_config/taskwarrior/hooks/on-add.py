#!/usr/bin/env python3
"""
Taskwarrior on-add hook.

Delegates to the shared hook entrypoint implementation.
"""

import os
import shutil
import sys


def maybe_reexec_with_uv() -> None:
    if os.environ.get("UV_RUN_RECURSION_DEPTH"):
        return
    if shutil.which("uv") is None:
        return
    os.execvp("uv", ["uv", "run", "--quiet", "--script", __file__, *sys.argv[1:]])


if __name__ == "__main__":
    maybe_reexec_with_uv()
    from hook_entrypoint import run_hook_entrypoint

    run_hook_entrypoint()
