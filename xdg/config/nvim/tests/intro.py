import fcntl
import os
from pathlib import Path
import pty
import re
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


def screen_cells(data):
    foreground = None
    cells = {}
    row = column = 0
    for token in re.findall(rb"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\([^\x00-\x1f]|[^\x1b]+|\x1b.", data):
        if token.startswith(b"\x1b[") and token.endswith(b"m") and b"?" not in token:
            params = [int(value.split(b":")[0]) if value else 0 for value in token[2:-1].split(b";")]
            index = 0
            while index < len(params):
                if params[index] in (0, 39):
                    foreground = None
                elif params[index : index + 2] == [38, 2] and index + 4 < len(params):
                    foreground = tuple(params[index + 2 : index + 5])
                    index += 4
                index += 1
        elif token.startswith(b"\x1b[") and token.endswith((b"H", b"f")):
            params = token[2:-1].split(b";")
            row = int(params[0] or b"1") - 1
            column = int(params[1] or b"1") - 1 if len(params) > 1 else 0
        elif token.startswith(b"\x1b[") and token.endswith(b"X"):
            count = int(token[2:-1] or b"1")
            for offset in range(count):
                cells.pop((row, column + offset), None)
        elif not token.startswith(b"\x1b"):
            for char in token.decode("utf-8", errors="replace"):
                if char == "\r":
                    column = 0
                elif char == "\n":
                    row += 1
                elif char >= " ":
                    cells[row, column] = (char, foreground)
                    column += 1
    return cells


try:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], 0.2)
        if ready:
            output.extend(os.read(master, 65536))
        cells = screen_cells(output)
        if any(
            all(cells.get((row, column + i)) == (char, (42, 161, 152)) for i, char in enumerate("NVIM v"))
            for row, column in cells
        ):
            break
    assert any(
        all(cells.get((row, column + i)) == (char, (42, 161, 152)) for i, char in enumerate("NVIM v"))
        for row, column in cells
    ), (
        "intro version text was not rendered in Solarized cyan"
    )
    assert any(char == "╲" and fg == (42, 161, 152) for char, fg in cells.values()), (
        "intro logo was not rendered in Solarized cyan"
    )
    print("Solarized intro terminal regression passed")
finally:
    process.kill()
    process.wait(timeout=5)
    os.close(master)
