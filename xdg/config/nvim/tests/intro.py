import fcntl
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import termios
import time

config = Path(__file__).resolve().parent.parent
master, slave = pty.openpty()
fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
process = subprocess.Popen(
    ["nvim", "--cmd", f"set runtimepath^={config}", "-u", str(config / "init.lua")],
    stdin=slave,
    stdout=slave,
    stderr=slave,
    env={**os.environ, "TERM": "xterm-256color"},
)
os.close(slave)
output = bytearray()
try:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], 0.2)
        if ready:
            output.extend(os.read(master, 65536))
        if b"NVIM v" in output and b"\x1b[38;2;133;153;0m" in output:
            break
    assert b"NVIM v" in output, "intro screen was not rendered"
    assert b"\x1b[38;2;133;153;0m" in output, "intro Statement is not Solarized green"
    assert b"\x1b[38;2;7;54;66m" not in output, "dark-on-dark foreground appeared in intro"
    print("Solarized intro terminal regression passed")
finally:
    process.kill()
    process.wait(timeout=5)
    os.close(master)
