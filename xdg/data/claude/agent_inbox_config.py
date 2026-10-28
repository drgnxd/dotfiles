"""Safely merge only the user-scope agent-inbox MCP server setting."""

import hashlib
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


def _validate_directory(directory: Path) -> os.stat_result:
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ValueError("Claude config directory has unsafe owner, type, or mode")
    return info


def _validate_link(link: Path, target: Path) -> os.stat_result:
    info = link.lstat()
    if not stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid() or link.resolve(strict=False) != target.resolve(strict=False):
        raise ValueError("Claude config symlink does not target the managed file")
    return info


def _read_snapshot(target: Path):
    try:
        info = target.lstat()
    except FileNotFoundError:
        return None, None
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Claude config file has unsafe owner, type, or mode")
    fd = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise RuntimeError("Claude config changed while opening")
        content = stream.read()
    token = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, hashlib.sha256(content).digest(), stat.S_IMODE(info.st_mode))
    return content, token


def _acquire_lock(lock: Path) -> tuple[int, tuple[int, int]]:
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(fd)
        raise ValueError("Claude config lock has unsafe owner, type, or mode")
    return fd, (info.st_dev, info.st_ino)


def _release_lock(lock: Path, fd: int, identity: tuple[int, int]) -> None:
    try:
        os.close(fd)
    finally:
        try:
            info = lock.lstat()
            if (info.st_dev, info.st_ino) == identity and stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid():
                lock.unlink()
        except FileNotFoundError:
            pass


def update(target: Path, link: Path, command: str) -> None:
    """Update while Claude writers are stopped; the lock coordinates only this setup tool."""
    target = target.absolute()
    link = link.absolute()
    _validate_directory(target.parent)
    _validate_link(link, target)
    lock = target.with_name(f"{target.name}.agent-inbox.lock")
    lock_fd, lock_identity = _acquire_lock(lock)
    temporary = None
    try:
        _validate_directory(target.parent)
        _validate_link(link, target)
        original, original_token = _read_snapshot(target)
        data = {} if original is None else json.loads(original)
        merged = (json.dumps(merge_config(data, command), indent=2, ensure_ascii=False) + "\n").encode()
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        os.fchmod(fd, 0o600 if original_token is None else original_token[5])
        with os.fdopen(fd, "wb") as stream:
            stream.write(merged)
            stream.flush()
            os.fsync(stream.fileno())
        current, current_token = _read_snapshot(target)
        if current_token != original_token or current != original:
            raise RuntimeError("Claude config changed during MCP merge")
        _validate_link(link, target)
        os.replace(temporary, target)
        temporary = None
        directory_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        _release_lock(lock, lock_fd, lock_identity)


if __name__ == "__main__":
    import sys

    update(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
