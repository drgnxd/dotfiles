#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
import os
import subprocess
import sys
from pathlib import Path

PID_FILE = Path.home() / ".local/state/swiftbar/caffeine.pid"
CAFFEINATE = "/usr/bin/caffeinate"


def running_pid():
    # A stale pid file can name an unrelated process after a reboot or crash.
    try:
        pid = int(PID_FILE.read_text())
        comm = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "comm="],
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, ValueError):
        return None
    return pid if comm == CAFFEINATE else None


def toggle():
    pid = running_pid()
    if pid:
        os.kill(pid, 15)
        PID_FILE.unlink(missing_ok=True)
        return
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [CAFFEINATE, "-di"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PID_FILE.write_text(str(proc.pid))


if len(sys.argv) > 1 and sys.argv[1] == "toggle":
    toggle()
    sys.exit(0)

active = running_pid() is not None
print("☕️" if active else "💤")
print("---")
label = "スリープ抑止を停止" if active else "スリープ抑止を開始"
print(f'{label} | bash="{os.path.realpath(sys.argv[0])}" param1=toggle terminal=false refresh=true')
