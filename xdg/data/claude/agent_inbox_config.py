#!/usr/bin/env python3
"""Safely merge only the user-scope agent-inbox MCP server setting."""

import json
import os
import stat
import tempfile
from pathlib import Path


def merge_config(data: object, command: str) -> dict:
    if not isinstance(data, dict):
        raise TypeError("Claude config must be a JSON object")
    result = dict(data)
    servers = result.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise TypeError("mcpServers must be a JSON object")
    result["mcpServers"] = dict(servers)
    result["mcpServers"]["agent-inbox"] = {"type": "stdio", "command": command, "args": ["mcp"]}
    return result


def update(target: Path, link: Path, command: str) -> None:
    target = target.absolute()
    link = link.absolute()
    directory_info = target.parent.lstat()
    if not stat.S_ISDIR(directory_info.st_mode) or directory_info.st_uid != os.getuid() or directory_info.st_mode & 0o022:
        raise ValueError("Claude config directory has unsafe owner, type, or mode")
    link_info = link.lstat()
    if not stat.S_ISLNK(link_info.st_mode) or link_info.st_uid != os.getuid() or link.resolve(strict=True) != target.resolve(strict=True):
        raise ValueError("Claude config symlink does not target the managed file")
    info = target.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Claude config file has unsafe owner, type, or mode")
    fd = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "r", encoding="utf-8") as stream:
        opened_info = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened_info.st_mode) or (opened_info.st_dev, opened_info.st_ino) != (info.st_dev, info.st_ino):
            raise ValueError("Claude config file changed while opening")
        raw = stream.read()
    merged = json.dumps(merge_config(json.loads(raw), command), indent=2, ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        os.fchmod(fd, stat.S_IMODE(info.st_mode))
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(merged)
            stream.flush()
            os.fsync(stream.fileno())
        current = target.lstat()
        current_link = link.lstat()
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino) or not stat.S_ISLNK(current_link.st_mode) or link.resolve(strict=True) != target.resolve(strict=True):
            raise ValueError("Claude config target changed before atomic update")
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


if __name__ == "__main__":
    import sys

    update(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
