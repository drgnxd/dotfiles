from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

SOURCE_FILES = {
    "dot_config/opencode/mcp/agent-browser-mcp.test.ts",
    "dot_config/opencode/mcp/agent-browser-mcp.ts",
    "dot_config/opencode/skills/agent-browser/SKILL.md",
    "dot_config/opencode/skills/agent-browser/playwright-readonly.test.ts",
    "dot_config/opencode/skills/agent-browser/playwright-readonly.ts",
    "dot_config/opencode/tools/agent-browser.ts",
    "dot_local/share/claude/agents/Browser.md",
}
OUTPUTS = (
    ("file", "config", "opencode/tools/agent-browser.ts", "dot_config/opencode/tools/agent-browser.ts"),
    ("file", "config", "opencode/mcp/agent-browser-mcp.ts", "dot_config/opencode/mcp/agent-browser-mcp.ts"),
    ("dirlink", "config", "opencode/skills/agent-browser", "dot_config/opencode/skills/agent-browser"),
    ("dirlink", "data", "claude/skills/agent-browser", "dot_config/opencode/skills/agent-browser"),
    ("filelink", "data", "claude/agents/Browser.md", "dot_local/share/claude/agents/Browser.md"),
)
MAX_SOURCE_BYTES = 2_000_000
DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
READ_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)


class SyncError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SyncError(message)


def _uid() -> int:
    return os.getuid()


def _check_directory(fd: int, label: str, private: bool = False) -> None:
    info = os.fstat(fd)
    require(stat.S_ISDIR(info.st_mode), f"not a directory: {label}")
    require(info.st_uid == _uid(), f"wrong owner: {label}")
    require(info.st_mode & 0o022 == 0, f"group/world-writable directory: {label}")
    if private:
        require(stat.S_IMODE(info.st_mode) == 0o700, f"private directory mode is not 0700: {label}")


def _check_home(home: str) -> tuple[str, int]:
    absolute = os.path.abspath(home)
    fd = os.open("/", DIR_FLAGS)
    prefix = "/"
    components = Path(absolute).parts[1:]
    try:
        for index, component in enumerate(components):
            prefix = os.path.join(prefix, component)
            child = os.open(component, DIR_FLAGS, dir_fd=fd)
            info = os.fstat(child)
            require(stat.S_ISDIR(info.st_mode) and info.st_mode & 0o022 == 0, f"unsafe HOME ancestor: {prefix}")
            if index == len(components) - 1:
                require(info.st_uid == _uid(), "HOME must be owned by the current user")
            os.close(fd)
            fd = child
        _check_directory(fd, absolute)
        return absolute, fd
    except Exception:
        os.close(fd)
        raise


def _relative(home: str, path: str) -> list[str]:
    absolute = os.path.abspath(path)
    require(os.path.commonpath((home, absolute)) == home, f"path escapes HOME: {path}")
    relative = os.path.relpath(absolute, home)
    return [] if relative == "." else relative.split(os.sep)


def _open_dir(home_fd: int, home: str, path: str, create: bool = False, private_leaf: bool = False) -> int:
    parts = _relative(home, path)
    fd = os.dup(home_fd)
    prefix = home
    try:
        for index, part in enumerate(parts):
            require(part not in ("", ".", ".."), f"invalid directory path: {path}")
            prefix = os.path.join(prefix, part)
            try:
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise SyncError(f"missing directory: {prefix}")
                os.mkdir(part, 0o700 if private_leaf and index == len(parts) - 1 else 0o755, dir_fd=fd)
                child = os.open(part, DIR_FLAGS, dir_fd=fd)
            _check_directory(child, prefix, private_leaf and index == len(parts) - 1)
            os.close(fd)
            fd = child
        return fd
    except Exception:
        os.close(fd)
        raise


def _parent_fd(home_fd: int, home: str, root: str, relative: str, create: bool = False) -> tuple[int, str]:
    root_fd = _open_dir(home_fd, home, root, create=create)
    parts = relative.split("/")
    if len(parts) == 1:
        return root_fd, parts[0]
    parent_fd = os.dup(root_fd)
    os.close(root_fd)
    try:
        for part in parts[:-1]:
            try:
                child = os.open(part, DIR_FLAGS, dir_fd=parent_fd)
            except FileNotFoundError:
                if not create:
                    raise SyncError(f"missing target parent: {relative}")
                os.mkdir(part, 0o755, dir_fd=parent_fd)
                child = os.open(part, DIR_FLAGS, dir_fd=parent_fd)
            _check_directory(child, relative)
            os.close(parent_fd)
            parent_fd = child
        return parent_fd, parts[-1]
    except Exception:
        os.close(parent_fd)
        raise


def _read_at(parent_fd: int, name: str, maximum: int = MAX_SOURCE_BYTES) -> tuple[bytes, os.stat_result]:
    fd = os.open(name, READ_FLAGS, dir_fd=parent_fd)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode), f"not a regular file: {name}")
        require(info.st_uid == _uid() and info.st_nlink == 1, f"unsafe file owner/link count: {name}")
        require(info.st_mode & 0o022 == 0 and stat.S_IMODE(info.st_mode) in (0o600, 0o644, 0o700), f"unsafe file mode: {name}")
        require(info.st_size <= maximum, f"file exceeds size limit: {name}")
        chunks = []
        while True:
            block = os.read(fd, min(65536, maximum + 1))
            if not block:
                break
            chunks.append(block)
            require(sum(map(len, chunks)) <= maximum, f"file exceeds size limit: {name}")
        return b"".join(chunks), info
    finally:
        os.close(fd)


def _read_relative(home_fd: int, home: str, root: str, relative: str) -> bytes:
    parent_fd, name = _parent_fd(home_fd, home, root, relative)
    try:
        return _read_at(parent_fd, name)[0]
    finally:
        os.close(parent_fd)


def _write_atomic(parent_fd: int, name: str, data: bytes, mode: int = 0o600) -> None:
    temporary = "." + name + "." + secrets.token_hex(8) + ".tmp"
    fd = os.open(temporary, WRITE_FLAGS, mode, dir_fd=parent_fd)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.rename(temporary, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    os.fsync(parent_fd)


def _write_json(home_fd: int, home: str, root: str, relative: str, value: dict[str, Any], exclusive: bool = False) -> None:
    parent_fd, name = _parent_fd(home_fd, home, root, relative, create=True)
    try:
        data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if exclusive:
            fd = os.open(name, WRITE_FLAGS, 0o600, dir_fd=parent_fd)
            try:
                os.write(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent_fd)
        else:
            try:
                info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_uid == _uid() and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o600, f"unsafe state file: {relative}")
            _write_atomic(parent_fd, name, data, 0o600)
    finally:
        os.close(parent_fd)


def _generation_id(manifest: dict[str, Any]) -> str:
    schema = manifest.get("schema")
    entries = sorted(manifest.get("files", []), key=lambda item: item["path"])
    if schema == 1:
        canonical = b"".join(item["path"].encode() + b"\0" + item["gitMode"].encode() + b"\0" + item["gitBlobOid"].encode() + b"\n" for item in entries)
    elif schema == 2:
        canonical = b"".join(item["path"].encode() + b"\0" + item["gitMode"].encode() + b"\0" + item["sha256"].encode() + b"\n" for item in entries)
    else:
        raise SyncError("unsupported private manifest schema")
    return hashlib.sha256(canonical).hexdigest()


def _load_generation(home_fd: int, home: str, data_home: str, generation: str) -> tuple[dict[str, Any], dict[str, bytes], str]:
    require(re.fullmatch(r"[0-9a-f]{64}", generation) is not None, "invalid generation id")
    source_root = os.path.join(data_home, "opencode-local", "agent-browser")
    generation_root = os.path.join(source_root, "generations")
    generation_fd = _open_dir(home_fd, home, os.path.join(generation_root, generation))
    try:
        manifest_raw = _read_relative(home_fd, home, os.path.join(generation_root, generation), "manifest.json")
        manifest = json.loads(manifest_raw)
        entries = manifest.get("files")
        require(isinstance(entries, list), "invalid private manifest files")
        names = {entry.get("path") for entry in entries}
        require(names == SOURCE_FILES, "private manifest source set differs")
        require(_generation_id(manifest) == generation, "private generation id mismatch")
        contents = {}
        for entry in entries:
            rel = entry["path"]
            data = _read_relative(home_fd, home, os.path.join(generation_root, generation), rel)
            require(len(data) == entry["size"] and hashlib.sha256(data).hexdigest() == entry["sha256"], f"private source checksum mismatch: {rel}")
            if entry.get("privateMode") != "0600":
                raise SyncError(f"unexpected private mode metadata: {rel}")
            contents[rel] = data
        return manifest, contents, hashlib.sha256(manifest_raw).hexdigest()
    finally:
        os.close(generation_fd)


def _process_start(pid: int, ps_path: str) -> str | None:
    result = subprocess.run(
        [ps_path, "-p", str(pid), "-o", "lstart="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return None
    return result.stdout.strip() or None


def _ancestor_pids(pid: int, ps_path: str) -> set[int]:
    result = subprocess.run(
        [ps_path, "-axo", "pid=,ppid="],
        check=True,
        capture_output=True,
        text=True,
    )
    parents = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2:
            parents[int(fields[0])] = int(fields[1])
    result_set = {os.getpid(), pid}
    current = os.getpid()
    while current in parents and parents[current] not in result_set and parents[current] != current:
        current = parents[current]
        result_set.add(current)
    current = pid
    while current in parents and parents[current] not in result_set and parents[current] != current:
        current = parents[current]
        result_set.add(current)
    return result_set


def _running_clients(
    home: str, config_home: str, data_home: str, activation_pid: int, ps_path: str
) -> list[int]:
    result = subprocess.run(
        [ps_path, "-axo", "pid=,ppid=,comm=,args="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise SyncError("unable to inspect running OpenCode/Claude processes")
    skipped = _ancestor_pids(activation_pid, ps_path)
    paths = [
        os.path.join(config_home, "opencode/tools/agent-browser.ts"),
        os.path.join(config_home, "opencode/tools/agent-browser-mcp"),
        os.path.join(config_home, "opencode/mcp/agent-browser-mcp.ts"),
    ]
    matches=[]
    for line in result.stdout.splitlines():
        fields=line.split(None,3)
        if len(fields)<3: continue
        pid=int(fields[0])
        if pid in skipped: continue
        comm=os.path.basename(fields[2]).lower()
        args=fields[3] if len(fields)>3 else ""
        if comm in {"opencode","claude"} or any(path in args for path in paths):
            matches.append(pid)
    return matches


def _open_state(home_fd: int, home: str) -> int:
    return _open_dir(home_fd, home, os.path.join(home, ".local/state/opencode/agent-browser"), create=True, private_leaf=True)


def _lock(state_fd: int) -> int:
    try:
        fd=os.open("deploy.lock", os.O_RDWR|os.O_CREAT|getattr(os,"O_NOFOLLOW",0),0o600,dir_fd=state_fd)
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==_uid() and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==0o600,"unsafe deployment lock")
        fcntl.lockf(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return fd
    except BlockingIOError as exc:
        raise SyncError("another local Browser deployment is active") from exc


def _state_json(state_fd: int, name: str) -> dict[str, Any] | None:
    try:
        raw,_=_read_at(state_fd,name,65536)
    except FileNotFoundError:
        return None
    return json.loads(raw)


def _write_state(state_fd: int, name: str, value: dict[str, Any], exclusive: bool=False) -> None:
    data=(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n").encode()
    if exclusive:
        fd=os.open(name,WRITE_FLAGS,0o600,dir_fd=state_fd)
        try: os.write(fd,data); os.fsync(fd)
        finally: os.close(fd)
        os.fsync(state_fd)
    else:
        _write_atomic(state_fd,name,data,0o600)


def _unlink_owned(state_fd: int, name: str, transaction: str) -> None:
    marker=_state_json(state_fd,name)
    require(marker is not None and marker.get("transaction")==transaction,"marker ownership mismatch")
    os.unlink(name,dir_fd=state_fd)
    os.fsync(state_fd)


def _source_target(data_home: str, generation: str, relative: str) -> str:
    return os.path.join(data_home,"opencode-local/agent-browser/generations",generation,relative)


def _write_private_file(home_fd: int, home: str, root: str, relative: str, data: bytes, allowed_hashes: set[str]) -> None:
    parent_fd,name=_parent_fd(home_fd,home,root,relative,create=True)
    try:
        try:
            current,_=_read_at(parent_fd,name)
        except FileNotFoundError:
            current=None
        if current is not None:
            require(hashlib.sha256(current).hexdigest() in allowed_hashes,"refusing modified Browser target")
        temporary="."+name+".sync-"+secrets.token_hex(8)
        fd=os.open(temporary,WRITE_FLAGS,0o600,dir_fd=parent_fd)
        try:
            view=memoryview(data)
            while view:
                n=os.write(fd,view); view=view[n:]
            os.fsync(fd)
        finally: os.close(fd)
        os.rename(temporary,name,src_dir_fd=parent_fd,dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally: os.close(parent_fd)


def _write_private_link(home_fd: int, home: str, root: str, relative: str, target: str, source: str, data_home: str, allowed_generations: list[tuple[str,dict[str,bytes]]]) -> None:
    parent_fd,name=_parent_fd(home_fd,home,root,relative,create=True)
    try:
        try:
            info=os.stat(name,dir_fd=parent_fd,follow_symlinks=False)
            require(stat.S_ISLNK(info.st_mode) and info.st_uid==_uid(),"refusing unknown Browser link target")
            existing=os.readlink(name,dir_fd=parent_fd)
            allowed=any(existing==_source_target(data_home,generation,source) or _verify_nix_target(existing,source,files) for generation,files in allowed_generations)
            require(allowed,"refusing modified Browser link")
        except FileNotFoundError:
            pass
        temporary="."+name+".sync-"+secrets.token_hex(8)
        os.symlink(target,temporary,dir_fd=parent_fd)
        os.rename(temporary,name,src_dir_fd=parent_fd,dst_dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally: os.close(parent_fd)


def _output_map(home: str, config_home: str, data_home: str, generation: str) -> list[dict[str, str]]:
    return [
        {"kind":"file","root":"config","path":"opencode/tools/agent-browser.ts","source":"dot_config/opencode/tools/agent-browser.ts"},
        {"kind":"file","root":"config","path":"opencode/mcp/agent-browser-mcp.ts","source":"dot_config/opencode/mcp/agent-browser-mcp.ts"},
        {"kind":"dirlink","root":"config","path":"opencode/skills/agent-browser","source":"dot_config/opencode/skills/agent-browser"},
        {"kind":"dirlink","root":"data","path":"claude/skills/agent-browser","source":"dot_config/opencode/skills/agent-browser"},
        {"kind":"filelink","root":"data","path":"claude/agents/Browser.md","source":"dot_local/share/claude/agents/Browser.md"},
    ]


def _verify_nix_target(target: str, source_rel: str, files: dict[str,bytes]) -> bool:
    if not target.startswith("/nix/store/"): return False
    resolved=os.path.realpath(target)
    if not resolved.startswith("/nix/store/"): return False
    path=Path(resolved)
    try: info=os.lstat(path)
    except OSError: return False
    if info.st_uid not in (0,_uid()) or info.st_mode & 0o022: return False
    if source_rel=="dot_config/opencode/skills/agent-browser":
        prefix=source_rel+"/"
        related={k[len(prefix):]:v for k,v in files.items() if k.startswith(prefix)}
        if not stat.S_ISDIR(info.st_mode): return False
        for rel,data in related.items():
            entry=Path(os.path.realpath(path/rel))
            try: entry_info=os.lstat(entry)
            except OSError: return False
            if not str(entry).startswith("/nix/store/") or not stat.S_ISREG(entry_info.st_mode) or entry_info.st_uid not in (0,_uid()) or entry_info.st_mode & 0o022:
                return False
            if hashlib.sha256(entry.read_bytes()).digest()!=hashlib.sha256(data).digest(): return False
        return True
    source=files.get(source_rel)
    if source is None or not stat.S_ISREG(info.st_mode): return False
    return hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(source).digest()


def _target_matches(home_fd: int, home: str, config_home: str, data_home: str, spec: dict[str,str], generations: list[tuple[str,dict[str,bytes]]], allow_nix: bool) -> bool:
    root=config_home if spec["root"]=="config" else data_home
    try:
        parent_fd,name=_parent_fd(home_fd,home,root,spec["path"])
    except SyncError as exc:
        if "missing" in str(exc): return False
        raise
    try:
        try: info=os.stat(name,dir_fd=parent_fd,follow_symlinks=False)
        except FileNotFoundError: return False
        for generation,files in generations:
            target=_source_target(data_home,generation,spec["source"])
            if spec["kind"]=="file":
                if stat.S_ISREG(info.st_mode):
                    data,_=_read_at(parent_fd,name)
                    if hashlib.sha256(data).hexdigest()==hashlib.sha256(files[spec["source"]]).hexdigest(): return True
            elif stat.S_ISLNK(info.st_mode):
                link=os.readlink(name,dir_fd=parent_fd)
                if link==target: return True
                if allow_nix and _verify_nix_target(link,spec["source"],files): return True
        return False
    finally: os.close(parent_fd)


def _verify_targets(home_fd: int, home: str, config_home: str, data_home: str, generation: str, files: dict[str,bytes], allow_missing: bool, allowed_generations: list[tuple[str,dict[str,bytes]]], allow_nix: bool) -> None:
    missing=[]
    for spec in _output_map(home,config_home,data_home,generation):
        if not _target_matches(home_fd,home,config_home,data_home,spec,allowed_generations,allow_nix):
            root=config_home if spec["root"]=="config" else data_home
            try:
                parent_fd,name=_parent_fd(home_fd,home,root,spec["path"])
            except SyncError as exc:
                if allow_missing and "missing" in str(exc):
                    missing.append(spec["path"])
                    continue
                raise
            try:
                try: os.stat(name,dir_fd=parent_fd,follow_symlinks=False)
                except FileNotFoundError: missing.append(spec["path"]); continue
            finally: os.close(parent_fd)
            raise SyncError(f"unrecognized Browser output: {spec['path']}")
    if missing and not allow_missing:
        raise SyncError("expected Browser outputs are missing: "+", ".join(missing))


def _install_generation(home_fd: int, home: str, config_home: str, data_home: str, generation: str, files: dict[str,bytes], allowed_generations: list[tuple[str,dict[str,bytes]]]) -> None:
    for spec in _output_map(home,config_home,data_home,generation):
        root=config_home if spec["root"]=="config" else data_home
        target=_source_target(data_home,generation,spec["source"])
        if spec["kind"]=="file":
            allowed={hashlib.sha256(g[1][spec["source"]]).hexdigest() for g in allowed_generations if spec["source"] in g[1]}
            _write_private_file(home_fd,home,root,spec["path"],files[spec["source"]],allowed)
        else:
            _write_private_link(home_fd,home,root,spec["path"],target,spec["source"],data_home,allowed_generations)


def _load_selector(home_fd: int, home: str, data_home: str) -> tuple[dict[str,Any],dict[str,bytes],str] | None:
    root=os.path.join(data_home,"opencode-local/agent-browser")
    try:
        raw = _read_relative(home_fd, home, root, "current.json")
    except FileNotFoundError:
        return None
    except SyncError as exc:
        if "missing directory" in str(exc):
            return None
        raise
    selector = json.loads(raw)
    _, files, manifest_sha = _load_generation(home_fd, home, data_home, selector["generation"])
    require(selector.get("manifestSha256") == manifest_sha, "selector manifest digest mismatch")
    return selector,files,manifest_sha


def _transaction_owner_live(marker: dict[str,Any], ps_path: str) -> bool:
    start=_process_start(int(marker["activationPid"]), ps_path)
    return start is not None and start==marker.get("activationStart")


def _write_deployment_state(home_fd: int, home: str, state_root: str, generation: str, manifest_sha: str) -> None:
    _write_json(home_fd,home,state_root,"deployment.json",{"schema":1,"generation":generation,"manifestSha256":manifest_sha})


def _finish_deploy(home_fd: int, home: str, config_home: str, data_home: str, state_fd: int, marker: dict[str,Any], activation_pid: int, process_probe: Callable[...,list[int]]) -> None:
    generation=marker["targetGeneration"]
    _,files,manifest_sha=_load_generation(home_fd,home,data_home,generation)
    require(marker.get("targetManifestSha256")==manifest_sha,"pending marker source manifest mismatch")
    previous=[]
    if marker.get("previousGeneration"):
        _,previous_files,previous_sha=_load_generation(home_fd,home,data_home,marker["previousGeneration"])
        previous.append((marker["previousGeneration"],previous_files,previous_sha))
    previous.append((generation,files,manifest_sha))
    clients=process_probe(home,config_home,data_home,activation_pid)
    if clients: raise SyncError("Browser clients appeared during deployment: "+", ".join(map(str,clients)))
    _install_generation(home_fd,home,config_home,data_home,generation,files,[(gid,fs) for gid,fs,_ in previous])
    _verify_targets(home_fd,home,config_home,data_home,generation,files,False,[(generation,files)],False)
    _write_deployment_state(home_fd,home,os.path.join(home,".local/state/opencode/agent-browser"),generation,manifest_sha)
    _unlink_owned(state_fd,"deploy-pending",marker["transaction"])


def _prepare(args: argparse.Namespace, process_probe: Callable[...,list[int]] | None = None) -> str:
    process_probe = process_probe or (
        lambda home, config_home, data_home, activation_pid: _running_clients(
            home, config_home, data_home, activation_pid, args.ps
        )
    )
    home,home_fd=_check_home(args.home)
    try:
        state_root=os.path.join(home,".local/state/opencode/agent-browser")
        state_fd=_open_dir(home_fd,home,state_root,create=True,private_leaf=True)
        try:
            lock_fd=_lock(state_fd)
            try:
                marker=_state_json(state_fd,"deploy-pending")
                if marker:
                    if _transaction_owner_live(marker, args.ps):
                        raise SyncError("another Home Manager activation owns the Browser marker")
                    _finish_deploy(home_fd,home,args.config_home,args.data_home,state_fd,marker,args.activation_pid,process_probe)
                loaded=_load_selector(home_fd,home,args.data_home)
                deployment=_state_json(state_fd,"deployment.json")
                if loaded is None:
                    if deployment:
                        raise SyncError("private Browser source is missing for a prior deployment")
                    return "skip"
                selector,files,manifest_sha=loaded
                generation=selector["generation"]
                previous=deployment.get("generation") if deployment else selector.get("previousGeneration")
                allowed=[]
                if previous:
                    _,old_files,_=_load_generation(home_fd,home,args.data_home,previous)
                    allowed.append((previous,old_files))
                    _verify_targets(home_fd,home,args.config_home,args.data_home,previous,old_files,deployment is None,[(previous,old_files)],True)
                else:
                    _verify_targets(home_fd,home,args.config_home,args.data_home,generation,files,True,[(generation,files)],True)
                clients=process_probe(home,args.config_home,args.data_home,args.activation_pid)
                if clients: raise SyncError("close OpenCode/Claude before Home Manager activation: "+", ".join(map(str,clients)))
                transaction=secrets.token_hex(16)
                marker_value={"schema":1,"transaction":transaction,"activationPid":args.activation_pid,"activationStart":_process_start(args.activation_pid, args.ps),"previousGeneration":previous,"targetGeneration":generation,"targetManifestSha256":manifest_sha,"phase":"prepared"}
                _write_state(state_fd,"deploy-pending",marker_value,exclusive=True)
                clients=process_probe(home,args.config_home,args.data_home,args.activation_pid)
                if clients:
                    _unlink_owned(state_fd,"deploy-pending",transaction)
                    raise SyncError("Browser client started during activation preparation: "+", ".join(map(str,clients)))
                return transaction
            finally: os.close(lock_fd)
        finally: os.close(state_fd)
    finally: os.close(home_fd)


def _deploy(args: argparse.Namespace, process_probe: Callable[...,list[int]] | None = None) -> None:
    process_probe = process_probe or (
        lambda home, config_home, data_home, activation_pid: _running_clients(
            home, config_home, data_home, activation_pid, args.ps
        )
    )
    if args.transaction=="skip": return
    home,home_fd=_check_home(args.home)
    try:
        state_root=os.path.join(home,".local/state/opencode/agent-browser")
        state_fd=_open_dir(home_fd,home,state_root)
        try:
            lock_fd=_lock(state_fd)
            try:
                marker=_state_json(state_fd,"deploy-pending")
                require(marker is not None and marker.get("transaction")==args.transaction,"activation marker mismatch")
                require(marker.get("activationPid")==args.activation_pid and marker.get("activationStart")==_process_start(args.activation_pid, args.ps),"activation owner mismatch")
                marker["phase"]="deploying"
                _write_json(home_fd,home,state_root,"deploy-pending",marker)
                _finish_deploy(home_fd,home,args.config_home,args.data_home,state_fd,marker,args.activation_pid,process_probe)
            finally: os.close(lock_fd)
        finally: os.close(state_fd)
    finally: os.close(home_fd)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=("prepare","deploy"))
    parser.add_argument("--home",default=os.environ.get("HOME"))
    parser.add_argument("--config-home",required=True)
    parser.add_argument("--data-home",required=True)
    parser.add_argument("--activation-pid",type=int,required=True)
    parser.add_argument("--ps",required=True)
    parser.add_argument("--transaction")
    args=parser.parse_args()
    try:
        if args.phase=="prepare":
            print(_prepare(args))
        else:
            require(args.transaction is not None,"deploy needs a transaction id")
            _deploy(args)
        return 0
    except (SyncError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"local Browser sync failed: {exc}",file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
