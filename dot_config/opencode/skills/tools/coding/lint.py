#!/usr/bin/env python3
"""Run lint checks using the local style script."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run lint checks for Python and shell files."
    )
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Skip missing lint tools instead of failing",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    check_script = script_dir / "check_style.sh"

    if not check_script.exists():
        print(f"Missing script: {check_script}")
        return 1

    command = [str(check_script)]
    if args.allow_missing:
        command.append("--allow-missing")
    command.append(args.target)

    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
