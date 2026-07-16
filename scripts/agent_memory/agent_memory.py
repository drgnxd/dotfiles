#!/usr/bin/env python3
"""Portable, event-sourced persistent memory for local AI agents."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 1
EVENT_SCHEMA_URI = "https://drgnxd.local/agent-memory/event-v1.schema.json"
DEFAULT_BUDGET_TOKENS = 1500
DEFAULT_MAINTENANCE_DAYS = 30
DEFAULT_MAINTENANCE_MIN_FACTS = 25
MEMORY_TYPES = {"semantic", "episodic", "procedural"}
ACTIVE_STATUS = "active"
KNOWN_EVENT_FIELDS = {
    "$schema",
    "schema_version",
    "sequence",
    "event_id",
    "event_type",
    "memory_id",
    "occurred_at",
    "recorded_at",
    "actor",
    "scopes",
    "content",
    "derived_from",
    "supersedes",
    "retention",
}


class MemoryCliError(RuntimeError):
    """An expected command-line failure with a stable exit status."""

    def __init__(self, message: str, exit_code: int = 64) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class StorePaths:
    memory_dir: Path
    database: Path
    events: Path
    legacy_memory: Path
    legacy_maintenance: Path
    event_schema: Path


def utc_now() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def utc_from_epoch(epoch: int) -> str:
    return (
        datetime.fromtimestamp(epoch, timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def uuid7() -> str:
    timestamp_ms = int(time.time_ns() // 1_000_000) & ((1 << 48) - 1)
    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)
    value = (
        (timestamp_ms << 80) | (0x7 << 76) | (random_a << 64) | (0b10 << 62) | random_b
    )
    return str(uuid.UUID(int=value))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def strict_json_loads(value: str) -> Any:
    def reject_constant(constant: str) -> None:
        raise ValueError(f"non-standard JSON constant: {constant}")

    return json.loads(value, parse_constant=reject_constant)


def resolve_paths() -> StorePaths:
    data_home = Path(
        os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    ).expanduser()
    memory_dir = Path(
        os.environ.get("AGENT_MEMORY_DIR", str(data_home / "agent-memory"))
    ).expanduser()
    database = Path(
        os.environ.get("AGENT_MEMORY_DB", str(memory_dir / "memory.sqlite3"))
    ).expanduser()
    events = Path(
        os.environ.get("AGENT_MEMORY_EVENTS", str(memory_dir / "events.jsonl"))
    ).expanduser()
    legacy_memory = Path(
        os.environ.get("AGENT_MEMORY_FILE", str(memory_dir / "memory.md"))
    ).expanduser()
    return StorePaths(
        memory_dir=memory_dir,
        database=database,
        events=events,
        legacy_memory=legacy_memory,
        legacy_maintenance=memory_dir / ".last-maintained",
        event_schema=Path(__file__).with_name("memory_event_v1.schema.json"),
    )


def prepare_memory_dir(paths: StorePaths) -> None:
    os.umask(0o077)
    paths.memory_dir.mkdir(parents=True, exist_ok=True)
    paths.memory_dir.chmod(0o700)
    paths.database.parent.mkdir(parents=True, exist_ok=True)
    paths.events.parent.mkdir(parents=True, exist_ok=True)


@contextlib.contextmanager
def memory_lock(paths: StorePaths, timeout_seconds: float = 10.0) -> Iterator[None]:
    lock_digest = hashlib.sha256(str(paths.database.resolve()).encode()).hexdigest()[
        :16
    ]
    lock_path = (
        Path(tempfile.gettempdir()) / f"agent-memory-{os.getuid()}-{lock_digest}.lock"
    )
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as error:
                if time.monotonic() >= deadline:
                    raise MemoryCliError("memory store is busy", 75) from error
                time.sleep(0.05)
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def connect_database(paths: StorePaths) -> sqlite3.Connection:
    connection = sqlite3.connect(paths.database, timeout=10)
    paths.database.chmod(0o600)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            schema_uri TEXT NOT NULL,
            schema_version INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            memory_id TEXT,
            occurred_at TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            actor_json TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            content_json TEXT NOT NULL,
            derived_from_json TEXT NOT NULL,
            supersedes_json TEXT NOT NULL,
            retention_json TEXT NOT NULL,
            extensions_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS events_type_idx
            ON events(event_type, sequence);
        CREATE INDEX IF NOT EXISTS events_memory_idx
            ON events(memory_id, sequence);

        CREATE TABLE IF NOT EXISTS memories (
            memory_id TEXT PRIMARY KEY,
            claim TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            status TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0,
            scopes_json TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            valid_from TEXT,
            valid_to TEXT,
            confidence REAL,
            created_event_id TEXT NOT NULL,
            updated_event_id TEXT NOT NULL,
            updated_sequence INTEGER NOT NULL,
            derived_from_json TEXT NOT NULL,
            retention_json TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS memories_status_idx
            ON memories(status, recorded_at);
        """
    )
    memory_columns = {
        str(row["name"]) for row in connection.execute("PRAGMA table_info(memories)")
    }
    if "updated_sequence" not in memory_columns:
        connection.execute(
            "ALTER TABLE memories ADD COLUMN updated_sequence INTEGER NOT NULL DEFAULT 0"
        )
        connection.execute(
            "UPDATE memories SET updated_sequence = COALESCE(("
            "SELECT sequence FROM events WHERE events.event_id = memories.updated_event_id"
            "), 0)"
        )
    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                memory_id UNINDEXED,
                claim,
                scope_text,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        set_metadata(connection, "fts_enabled", "1")
    except sqlite3.OperationalError:
        set_metadata(connection, "fts_enabled", "0")
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()


def get_metadata(connection: sqlite3.Connection, key: str) -> str | None:
    row = connection.execute(
        "SELECT value FROM metadata WHERE key = ?", (key,)
    ).fetchone()
    return None if row is None else str(row["value"])


def set_metadata(connection: sqlite3.Connection, key: str, value: str) -> None:
    connection.execute(
        """
        INSERT INTO metadata(key, value) VALUES(?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def validate_timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MemoryCliError(f"event {field} must be a non-empty RFC 3339 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise MemoryCliError(
            f"event {field} is not a valid RFC 3339 timestamp"
        ) from error
    if parsed.tzinfo is None:
        raise MemoryCliError(f"event {field} must include a timezone")
    return value


def normalize_scopes(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MemoryCliError("event scopes must be an array")
    scopes: dict[tuple[str, str], dict[str, Any]] = {}
    for scope in value:
        if not isinstance(scope, dict):
            raise MemoryCliError("each event scope must be an object")
        scope_type = scope.get("type")
        scope_id = scope.get("id")
        if not isinstance(scope_type, str) or not scope_type:
            raise MemoryCliError("each event scope requires a type")
        if not isinstance(scope_id, str) or not scope_id:
            raise MemoryCliError("each event scope requires an id")
        key = (scope_type, scope_id)
        if key in scopes:
            raise MemoryCliError(f"duplicate event scope: {scope_type}:{scope_id}")
        scopes[key] = dict(scope)
    return [scopes[key] for key in sorted(scopes)]


def validate_event(raw_event: Any) -> dict[str, Any]:
    if not isinstance(raw_event, dict):
        raise MemoryCliError("each event must be a JSON object")
    event = dict(raw_event)
    required = {
        "$schema",
        "schema_version",
        "event_id",
        "event_type",
        "memory_id",
        "occurred_at",
        "recorded_at",
        "actor",
        "scopes",
        "content",
        "derived_from",
        "supersedes",
        "retention",
    }
    missing = sorted(required - event.keys())
    if missing:
        raise MemoryCliError(f"event is missing required fields: {', '.join(missing)}")
    if event["$schema"] != EVENT_SCHEMA_URI:
        raise MemoryCliError(f"unsupported event schema: {event['$schema']}")
    if (
        isinstance(event["schema_version"], bool)
        or not isinstance(event["schema_version"], int)
        or event["schema_version"] != SCHEMA_VERSION
    ):
        raise MemoryCliError(
            f"unsupported event schema_version: {event['schema_version']}"
        )
    if not isinstance(event["event_id"], str):
        raise MemoryCliError("event event_id must be a UUID string")
    try:
        uuid.UUID(event["event_id"])
    except (ValueError, AttributeError) as error:
        raise MemoryCliError("event event_id must be a UUID") from error
    if not isinstance(event["event_type"], str) or not re.fullmatch(
        r"[a-z][a-z0-9_.-]+", event["event_type"]
    ):
        raise MemoryCliError("event event_type is invalid")
    memory_id = event.get("memory_id")
    if memory_id is not None:
        if not isinstance(memory_id, str):
            raise MemoryCliError("event memory_id must be a UUID string or null")
        try:
            uuid.UUID(memory_id)
        except (ValueError, AttributeError) as error:
            raise MemoryCliError("event memory_id must be a UUID or null") from error
    event["occurred_at"] = validate_timestamp(event["occurred_at"], "occurred_at")
    event["recorded_at"] = validate_timestamp(event["recorded_at"], "recorded_at")
    if (
        not isinstance(event["actor"], dict)
        or not isinstance(event["actor"].get("type"), str)
        or not event["actor"]["type"]
    ):
        raise MemoryCliError("event actor requires a type")
    actor_id = event["actor"].get("id")
    if actor_id is not None and (not isinstance(actor_id, str) or not actor_id):
        raise MemoryCliError("event actor id must be a non-empty string")
    event["scopes"] = normalize_scopes(event["scopes"])
    if not isinstance(event["content"], dict):
        raise MemoryCliError("event content must be an object")
    for field in ("derived_from", "supersedes"):
        if not isinstance(event[field], list) or not all(
            isinstance(item, str) and item for item in event[field]
        ):
            raise MemoryCliError(f"event {field} must be an array of strings")
        if len(event[field]) != len(set(event[field])):
            raise MemoryCliError(f"event {field} must not contain duplicates")
    if not isinstance(event["retention"], dict):
        raise MemoryCliError("event retention must be an object")
    classification = event["retention"].get("classification")
    if classification is not None and not isinstance(classification, str):
        raise MemoryCliError("event retention classification must be a string")
    retention_until = event["retention"].get("retention_until")
    if retention_until is not None:
        validate_timestamp(retention_until, "retention_until")
    if event["event_type"].startswith("memory.") and not any(
        scope["type"] == "user" for scope in event["scopes"]
    ):
        raise MemoryCliError("memory events require a user scope")
    if event["event_type"] in {"memory.created", "memory.imported", "memory.updated"}:
        claim = event["content"].get("claim")
        memory_type = event["content"].get("memory_type")
        if memory_id is None:
            raise MemoryCliError(f"{event['event_type']} requires memory_id")
        validate_claim(claim)
        if memory_type not in MEMORY_TYPES:
            raise MemoryCliError(f"unsupported memory type: {memory_type}")
        confidence = event["content"].get("confidence")
        if confidence is not None and (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence)
            or not 0.0 <= confidence <= 1.0
        ):
            raise MemoryCliError("memory confidence must be between 0.0 and 1.0")
        if "pinned" in event["content"] and not isinstance(
            event["content"]["pinned"], bool
        ):
            raise MemoryCliError("memory pinned must be a boolean")
        for field in ("valid_from", "valid_to"):
            if event["content"].get(field) is not None:
                validate_timestamp(event["content"][field], field)
    if (
        event["event_type"] in {"memory.retracted", "memory.expired"}
        and memory_id is None
    ):
        raise MemoryCliError(f"{event['event_type']} requires memory_id")
    sequence = event.get("sequence")
    if sequence is not None and (
        isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1
    ):
        raise MemoryCliError("event sequence must be a positive integer")
    return event


def validate_claim(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MemoryCliError("memory fact must not be empty")
    claim = value.strip()
    if "\n" in claim or "\r" in claim:
        raise MemoryCliError("memory fact must be a single line")
    return claim


def row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    event = json.loads(row["extensions_json"])
    event.update(
        {
            "$schema": row["schema_uri"],
            "schema_version": row["schema_version"],
            "sequence": row["sequence"],
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "memory_id": row["memory_id"],
            "occurred_at": row["occurred_at"],
            "recorded_at": row["recorded_at"],
            "actor": json.loads(row["actor_json"]),
            "scopes": json.loads(row["scopes_json"]),
            "content": json.loads(row["content_json"]),
            "derived_from": json.loads(row["derived_from_json"]),
            "supersedes": json.loads(row["supersedes_json"]),
            "retention": json.loads(row["retention_json"]),
        }
    )
    return event


def event_without_sequence(event: dict[str, Any]) -> dict[str, Any]:
    comparable = dict(event)
    comparable.pop("sequence", None)
    return comparable


def fts_enabled(connection: sqlite3.Connection) -> bool:
    return get_metadata(connection, "fts_enabled") == "1"


def delete_fts_memory(connection: sqlite3.Connection, memory_id: str) -> None:
    if fts_enabled(connection):
        connection.execute("DELETE FROM memory_fts WHERE memory_id = ?", (memory_id,))


def scope_text(scopes: list[dict[str, Any]]) -> str:
    return " ".join(
        " ".join(
            str(value)
            for key, value in sorted(scope.items())
            if key in {"type", "id", "name", "uri"}
        )
        for scope in scopes
    )


def upsert_fts_memory(
    connection: sqlite3.Connection,
    memory_id: str,
    claim: str,
    scopes: list[dict[str, Any]],
) -> None:
    if not fts_enabled(connection):
        return
    delete_fts_memory(connection, memory_id)
    connection.execute(
        "INSERT INTO memory_fts(memory_id, claim, scope_text) VALUES(?, ?, ?)",
        (memory_id, claim, scope_text(scopes)),
    )


def apply_event_projection(
    connection: sqlite3.Connection, event: dict[str, Any]
) -> None:
    event_type = event["event_type"]
    memory_id = event.get("memory_id")
    if event_type in {"memory.created", "memory.imported", "memory.updated"}:
        assert isinstance(memory_id, str)
        content = event["content"]
        claim = validate_claim(content["claim"])
        memory_type = content["memory_type"]
        existing = connection.execute(
            "SELECT created_event_id, status FROM memories WHERE memory_id = ?",
            (memory_id,),
        ).fetchone()
        if event_type == "memory.updated" and (
            existing is None or existing["status"] != ACTIVE_STATUS
        ):
            raise MemoryCliError(
                f"cannot update inactive or unknown memory: {memory_id}"
            )
        if event_type != "memory.updated" and existing is not None:
            raise MemoryCliError(f"memory_id already exists: {memory_id}", 65)

        for superseded_id in event["supersedes"]:
            if superseded_id == memory_id:
                continue
            superseded = connection.execute(
                "SELECT status FROM memories WHERE memory_id = ?", (superseded_id,)
            ).fetchone()
            if superseded is None or superseded["status"] != ACTIVE_STATUS:
                raise MemoryCliError(
                    f"cannot supersede inactive or unknown memory: {superseded_id}"
                )
            connection.execute(
                "UPDATE memories SET status = 'superseded', updated_event_id = ? "
                "WHERE memory_id = ?",
                (event["event_id"], superseded_id),
            )
            delete_fts_memory(connection, superseded_id)

        created_event_id = (
            event["event_id"] if existing is None else str(existing["created_event_id"])
        )
        connection.execute(
            """
            INSERT INTO memories(
                memory_id, claim, memory_type, status, pinned, scopes_json,
                occurred_at, recorded_at, valid_from, valid_to, confidence,
                created_event_id, updated_event_id, updated_sequence, derived_from_json,
                retention_json
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                claim = excluded.claim,
                memory_type = excluded.memory_type,
                status = excluded.status,
                pinned = excluded.pinned,
                scopes_json = excluded.scopes_json,
                occurred_at = excluded.occurred_at,
                recorded_at = excluded.recorded_at,
                valid_from = excluded.valid_from,
                valid_to = excluded.valid_to,
                confidence = excluded.confidence,
                updated_event_id = excluded.updated_event_id,
                updated_sequence = excluded.updated_sequence,
                derived_from_json = excluded.derived_from_json,
                retention_json = excluded.retention_json
            """,
            (
                memory_id,
                claim,
                memory_type,
                ACTIVE_STATUS,
                int(bool(content.get("pinned", False))),
                canonical_json(event["scopes"]),
                event["occurred_at"],
                event["recorded_at"],
                content.get("valid_from"),
                content.get("valid_to"),
                content.get("confidence"),
                created_event_id,
                event["event_id"],
                event["sequence"],
                canonical_json(event["derived_from"]),
                canonical_json(event["retention"]),
            ),
        )
        upsert_fts_memory(connection, memory_id, claim, event["scopes"])
        return

    if event_type in {"memory.retracted", "memory.expired"} and memory_id:
        existing = connection.execute(
            "SELECT status FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if existing is None or existing["status"] != ACTIVE_STATUS:
            raise MemoryCliError(
                f"cannot retire inactive or unknown memory: {memory_id}"
            )
        status = "retracted" if event_type == "memory.retracted" else "expired"
        connection.execute(
            "UPDATE memories SET status = ?, updated_event_id = ? WHERE memory_id = ?",
            (status, event["event_id"], memory_id),
        )
        delete_fts_memory(connection, memory_id)
        return

    if event_type == "maintenance.completed":
        scope_key = str(event["content"].get("scope_key", "all"))
        set_metadata(
            connection, f"last_maintained_at:{scope_key}", event["occurred_at"]
        )


def insert_event(connection: sqlite3.Connection, raw_event: Any) -> bool:
    event = validate_event(raw_event)
    existing = connection.execute(
        "SELECT * FROM events WHERE event_id = ?", (event["event_id"],)
    ).fetchone()
    if existing is not None:
        if canonical_json(
            event_without_sequence(row_to_event(existing))
        ) != canonical_json(event_without_sequence(event)):
            raise MemoryCliError(
                f"event_id has conflicting content: {event['event_id']}", 65
            )
        return False

    extensions = {
        key: value for key, value in event.items() if key not in KNOWN_EVENT_FIELDS
    }
    cursor = connection.execute(
        """
        INSERT INTO events(
            event_id, schema_uri, schema_version, event_type, memory_id,
            occurred_at, recorded_at, actor_json, scopes_json, content_json,
            derived_from_json, supersedes_json, retention_json, extensions_json
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["event_id"],
            event["$schema"],
            event["schema_version"],
            event["event_type"],
            event.get("memory_id"),
            event["occurred_at"],
            event["recorded_at"],
            canonical_json(event["actor"]),
            canonical_json(event["scopes"]),
            canonical_json(event["content"]),
            canonical_json(event["derived_from"]),
            canonical_json(event["supersedes"]),
            canonical_json(event["retention"]),
            canonical_json(extensions),
        ),
    )
    if cursor.lastrowid is None:
        raise MemoryCliError("database did not assign an event sequence", 70)
    event["sequence"] = cursor.lastrowid
    apply_event_projection(connection, event)
    return True


def make_event(
    event_type: str,
    *,
    memory_id: str | None,
    scopes: list[dict[str, Any]],
    content: dict[str, Any],
    occurred_at: str | None = None,
    actor_type: str = "agent",
    derived_from: Sequence[str] = (),
    supersedes: Sequence[str] = (),
    retention: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = utc_now()
    return {
        "$schema": EVENT_SCHEMA_URI,
        "schema_version": SCHEMA_VERSION,
        "event_id": uuid7(),
        "event_type": event_type,
        "memory_id": memory_id,
        "occurred_at": occurred_at or timestamp,
        "recorded_at": timestamp,
        "actor": {"type": actor_type},
        "scopes": normalize_scopes(scopes),
        "content": content,
        "derived_from": list(derived_from),
        "supersedes": list(supersedes),
        "retention": (
            retention if retention is not None else {"classification": "private"}
        ),
    }


def owner_scope() -> dict[str, str]:
    return {
        "type": "user",
        "id": os.environ.get("AGENT_MEMORY_OWNER_ID", "local-user"),
    }


def run_git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def sanitize_git_remote(value: str) -> str | None:
    remote = value.strip()
    if not remote:
        return None
    if "://" not in remote:
        scp_match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", remote)
        if scp_match is None:
            return None
        host, path = scp_match.groups()
        remote = f"ssh://{host}/{path}"
    parsed = urlsplit(remote)
    if parsed.scheme not in {"git", "http", "https", "ssh"} or parsed.hostname is None:
        return None
    try:
        port = parsed.port
    except ValueError as error:
        raise MemoryCliError("git remote has an invalid port") from error
    default_ports = {"git": 9418, "http": 80, "https": 443, "ssh": 22}
    if port == default_ports.get(parsed.scheme.lower()):
        port = None
    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port is not None else host
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path:
        return None
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))


def project_id_from_remote(uri: str) -> str:
    parsed = urlsplit(uri)
    return f"{parsed.netloc.lower()}{parsed.path}"


def detect_project(cwd: Path, memory_dir: Path) -> dict[str, str] | None:
    override = os.environ.get("AGENT_MEMORY_PROJECT_ID")
    if override:
        return {"type": "project", "id": override}
    if shutil.which("git") is None:
        return None
    result = run_git(["rev-parse", "--show-toplevel"], cwd)
    if result.returncode != 0:
        return None
    root = Path(result.stdout.strip()).resolve()
    if root == memory_dir.resolve():
        return None
    remote = run_git(["config", "--get", "remote.origin.url"], root)
    uri = None
    if remote.returncode == 0 and remote.stdout.strip():
        uri = sanitize_git_remote(remote.stdout)
    project_id = (
        project_id_from_remote(uri)
        if uri is not None
        else "local:" + hashlib.sha256(str(root).encode()).hexdigest()
    )
    scope = {"type": "project", "id": project_id, "name": root.name}
    if uri is not None:
        scope["uri"] = uri
    return scope


def parse_scope_argument(value: str) -> dict[str, str]:
    if ":" not in value:
        raise MemoryCliError(
            f"scope must be global, project, auto, or type:id: {value}"
        )
    scope_type, scope_id = value.split(":", 1)
    if not scope_type or not scope_id:
        raise MemoryCliError(f"invalid scope: {value}")
    return {"type": scope_type, "id": scope_id}


def resolve_context_scopes(
    values: Sequence[str] | None,
    cwd: Path,
    memory_dir: Path,
) -> list[dict[str, Any]]:
    requested = list(values or ["auto"])
    scopes: list[dict[str, Any]] = [owner_scope()]
    for value in requested:
        if value in {"global", "user"}:
            continue
        if value in {"auto", "project"}:
            project = detect_project(cwd, memory_dir)
            if value == "project" and project is None:
                raise MemoryCliError("current directory is not a project")
            if project is not None:
                scopes.append(project)
            continue
        scopes.append(parse_scope_argument(value))
    return normalize_scopes(scopes)


def infer_legacy_scopes(claim: str) -> list[dict[str, Any]]:
    scopes: list[dict[str, Any]] = [owner_scope()]
    project_match = re.match(r"^In ([A-Za-z0-9][A-Za-z0-9._-]*),", claim)
    if project_match is None:
        project_match = re.match(
            r"^The ([A-Za-z0-9][A-Za-z0-9._-]*) repository\b", claim
        )
    if project_match is not None:
        scopes.append({"type": "legacy_project", "id": project_match.group(1)})
    return normalize_scopes(scopes)


def import_legacy_memory(connection: sqlite3.Connection, paths: StorePaths) -> int:
    if not paths.legacy_memory.is_file():
        return 0
    imported = 0
    line_pattern = re.compile(r"^- (\S+) (.+)$")
    with paths.legacy_memory.open(encoding="utf-8") as source:
        for line_number, raw_line in enumerate(source, 1):
            match = line_pattern.match(raw_line.rstrip("\n"))
            if match is None:
                continue
            occurred_at, claim = match.groups()
            validate_timestamp(occurred_at, "legacy timestamp")
            content = {
                "claim": validate_claim(claim),
                "memory_type": "semantic",
                "status": ACTIVE_STATUS,
                "pinned": claim.startswith(("User prefers ", "Do not ")),
                "valid_from": None,
                "valid_to": None,
                "confidence": None,
            }
            event = make_event(
                "memory.imported",
                memory_id=uuid7(),
                scopes=infer_legacy_scopes(claim),
                content=content,
                occurred_at=occurred_at,
                actor_type="system",
                derived_from=(f"legacy:memory.md#line={line_number}",),
            )
            if insert_event(connection, event):
                imported += 1

    if paths.legacy_maintenance.is_file():
        try:
            epoch = int(paths.legacy_maintenance.read_text(encoding="utf-8").strip())
        except ValueError:
            pass
        else:
            insert_event(
                connection,
                make_event(
                    "maintenance.completed",
                    memory_id=None,
                    scopes=[owner_scope()],
                    content={"reason": "legacy import", "active_count": imported},
                    occurred_at=utc_from_epoch(epoch),
                    actor_type="system",
                    derived_from=("legacy:.last-maintained",),
                ),
            )
    return imported


def iter_event_file(path: Path) -> Iterator[dict[str, Any]]:
    try:
        source = path.open(encoding="utf-8")
    except OSError as error:
        raise MemoryCliError(f"cannot open event file {path}: {error}", 66) from error
    with source:
        for line_number, raw_line in enumerate(source, 1):
            if not raw_line.strip():
                continue
            try:
                value = strict_json_loads(raw_line)
            except (json.JSONDecodeError, ValueError) as error:
                raise MemoryCliError(
                    f"invalid JSON in {path} at line {line_number}", 65
                ) from error
            yield validate_event(value)


def initialize_database(
    connection: sqlite3.Connection, paths: StorePaths
) -> str | None:
    initialize_schema(connection)
    if get_metadata(connection, "initialized") == "1":
        return None
    migration: str | None = None
    connection.execute("BEGIN IMMEDIATE")
    try:
        if paths.events.is_file() and paths.events.stat().st_size > 0:
            for event in iter_event_file(paths.events):
                insert_event(connection, event)
            migration = "portable event log"
        elif paths.legacy_memory.is_file():
            import_legacy_memory(connection, paths)
            migration = "legacy Markdown"
        set_metadata(connection, "dataset_id", uuid7())
        set_metadata(connection, "initialized", "1")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return migration


def export_events_atomic(connection: sqlite3.Connection, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            rows = connection.execute("SELECT * FROM events ORDER BY sequence")
            for row in rows:
                output.write(canonical_json(row_to_event(row)))
                output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, destination)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def auto_git_enabled() -> bool:
    return os.environ.get("AGENT_MEMORY_GIT", "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def git_repository_root(memory_dir: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    result = run_git(["rev-parse", "--show-toplevel"], memory_dir)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def auto_commit_repository_root(memory_dir: Path) -> Path | None:
    if not auto_git_enabled():
        return None
    root = git_repository_root(memory_dir)
    if root is None or root != memory_dir.resolve():
        return None
    remote = run_git(["remote"], root)
    allow_remote = os.environ.get("AGENT_MEMORY_GIT_ALLOW_REMOTE", "0").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if remote.returncode == 0 and remote.stdout.strip() and not allow_remote:
        return None
    return root


def relative_to_repository(path: Path, root: Path) -> Path | None:
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return None


def exclude_database_from_git(paths: StorePaths) -> None:
    root = git_repository_root(paths.memory_dir)
    if root is None:
        return
    relative_database = relative_to_repository(paths.database, root)
    if relative_database is None:
        return
    git_path = run_git(["rev-parse", "--git-path", "info/exclude"], root)
    if git_path.returncode != 0:
        return
    exclude_path = Path(git_path.stdout.strip())
    if not exclude_path.is_absolute():
        exclude_path = root / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    patterns = [
        f"/{relative_database.as_posix()}",
        f"/{relative_database.as_posix()}-shm",
        f"/{relative_database.as_posix()}-wal",
    ]
    missing = [pattern for pattern in patterns if pattern not in existing.splitlines()]
    if not missing:
        return
    with exclude_path.open("a", encoding="utf-8") as output:
        if existing and not existing.endswith("\n"):
            output.write("\n")
        output.write("# Agent memory operational database; events.jsonl is portable.\n")
        output.write("\n".join(missing))
        output.write("\n")


def commit_portable_log(paths: StorePaths, message: str) -> None:
    root = auto_commit_repository_root(paths.memory_dir)
    if root is None:
        return
    relative_events = relative_to_repository(paths.events, root)
    if relative_events is None:
        print(
            "WARN: memory updated, but its portable event log is outside the memory git repository",
            file=sys.stderr,
        )
        return
    relative = relative_events.as_posix()
    add = run_git(["--literal-pathspecs", "add", "--", relative], root)
    if add.returncode != 0:
        print("WARN: memory updated, but git add failed", file=sys.stderr)
        return
    diff = run_git(
        ["--literal-pathspecs", "diff", "--cached", "--quiet", "--", relative], root
    )
    if diff.returncode == 0:
        return
    commit = run_git(
        [
            "--literal-pathspecs",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            message,
            "--",
            relative,
        ],
        root,
    )
    if commit.returncode != 0:
        print("WARN: memory updated, but git commit failed", file=sys.stderr)


def sync_portable_log(
    connection: sqlite3.Connection, paths: StorePaths, git_message: str
) -> None:
    try:
        export_events_atomic(connection, paths.events)
    except OSError as error:
        raise MemoryCliError(
            f"memory was committed, but portable export failed: {error}", 74
        ) from error
    exclude_database_from_git(paths)
    commit_portable_log(paths, git_message)


def row_to_memory(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "memory_id": row["memory_id"],
        "claim": row["claim"],
        "memory_type": row["memory_type"],
        "status": row["status"],
        "pinned": bool(row["pinned"]),
        "scopes": json.loads(row["scopes_json"]),
        "occurred_at": row["occurred_at"],
        "recorded_at": row["recorded_at"],
        "valid_from": row["valid_from"],
        "valid_to": row["valid_to"],
        "confidence": row["confidence"],
        "created_event_id": row["created_event_id"],
        "updated_event_id": row["updated_event_id"],
        "updated_sequence": row["updated_sequence"],
        "derived_from": json.loads(row["derived_from_json"]),
        "retention": json.loads(row["retention_json"]),
    }


def active_memories(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM memories WHERE status = ? ORDER BY recorded_at DESC, memory_id",
        (ACTIVE_STATUS,),
    )
    return [row_to_memory(row) for row in rows]


def legacy_project_names(connection: sqlite3.Connection) -> list[str]:
    names = {
        scope["id"]
        for memory in active_memories(connection)
        for scope in memory["scopes"]
        if scope["type"] == "legacy_project"
    }
    return sorted(names)


def scopes_match(
    memory_scopes: list[dict[str, Any]], context_scopes: list[dict[str, Any]]
) -> bool:
    context = {(scope["type"], scope["id"]) for scope in context_scopes}
    return all((scope["type"], scope["id"]) in context for scope in memory_scopes)


def scope_identities(scopes: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(scope["type"], scope["id"]) for scope in scopes}


def query_terms(query: str) -> list[str]:
    terms = re.findall(r"[\w./:@+-]+", query.lower(), flags=re.UNICODE)
    return list(dict.fromkeys(term for term in terms if term))[:12]


def fts_ranks(connection: sqlite3.Connection, query: str) -> dict[str, float]:
    if not fts_enabled(connection):
        return {}
    terms = query_terms(query)
    if not terms:
        return {}
    expression = " OR ".join(
        f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms
    )
    try:
        rows = connection.execute(
            "SELECT memory_id, bm25(memory_fts) AS rank "
            "FROM memory_fts WHERE memory_fts MATCH ?",
            (expression,),
        )
    except sqlite3.OperationalError:
        return {}
    return {str(row["memory_id"]): float(row["rank"]) for row in rows}


def lexical_score(memory: dict[str, Any], query: str) -> int:
    haystack = (memory["claim"] + " " + scope_text(memory["scopes"])).casefold()
    folded_query = query.casefold().strip()
    score = 4 if folded_query and folded_query in haystack else 0
    score += sum(1 for term in query_terms(query) if term.casefold() in haystack)
    return score


def estimate_tokens(text: str) -> int:
    ascii_count = sum(1 for character in text if ord(character) < 128)
    non_ascii_count = len(text) - ascii_count
    return max(1, math.ceil(ascii_count / 4) + non_ascii_count)


def memory_has_project_scope(memory: dict[str, Any]) -> bool:
    return any(scope["type"] == "project" for scope in memory["scopes"])


def select_memories(
    connection: sqlite3.Connection,
    memories: list[dict[str, Any]],
    query: str | None,
    budget_tokens: int,
) -> list[dict[str, Any]]:
    ranks = fts_ranks(connection, query) if query else {}
    candidates: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for memory in memories:
        lexical = lexical_score(memory, query) if query else 0
        fts_rank = ranks.get(memory["memory_id"])
        matched = lexical > 0 or fts_rank is not None
        if query and not matched and not memory["pinned"]:
            continue
        key = (
            0 if memory["pinned"] else 1,
            0 if matched else 1,
            fts_rank if fts_rank is not None else 1_000_000.0,
            -lexical,
            0 if memory_has_project_scope(memory) else 1,
            -memory["updated_sequence"],
        )
        candidates.append((key, memory))
    candidates.sort(key=lambda item: item[0])

    selected: list[dict[str, Any]] = []
    used_tokens = 0
    for _, memory in candidates:
        memory_tokens = estimate_tokens(memory["claim"]) + 2
        if used_tokens + memory_tokens > budget_tokens:
            continue
        selected.append(memory)
        used_tokens += memory_tokens
    return selected


def parse_non_negative_integer(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as error:
        raise MemoryCliError(f"{name} must be a non-negative integer") from error
    if value < 0:
        raise MemoryCliError(f"{name} must be a non-negative integer")
    return value


def context_key(scopes: list[dict[str, Any]] | None) -> str:
    if scopes is None:
        return "all"
    identities = sorted(scope_identities(scopes))
    return hashlib.sha256(canonical_json(identities).encode()).hexdigest()[:24]


def maintenance_due(
    connection: sqlite3.Connection, fact_count: int, scope_key: str
) -> bool:
    minimum = parse_non_negative_integer(
        "AGENT_MEMORY_MAINTENANCE_MIN_FACTS", DEFAULT_MAINTENANCE_MIN_FACTS
    )
    days = parse_non_negative_integer(
        "AGENT_MEMORY_MAINTENANCE_DAYS", DEFAULT_MAINTENANCE_DAYS
    )
    if fact_count < minimum:
        return False
    maintained_at = get_metadata(connection, f"last_maintained_at:{scope_key}")
    if maintained_at is None:
        return True
    normalized = (
        maintained_at[:-1] + "+00:00" if maintained_at.endswith("Z") else maintained_at
    )
    maintained = datetime.fromisoformat(normalized)
    return (datetime.now(timezone.utc) - maintained).total_seconds() >= days * 86400


def memory_generation(memories: Sequence[dict[str, Any]]) -> str:
    payload = sorted(memories, key=lambda memory: memory["memory_id"])
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def command_read(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    all_memories = active_memories(connection)
    if args.all:
        current_scopes = None
        applicable = all_memories
    else:
        current_scopes = resolve_context_scopes(
            args.scope, Path.cwd(), paths.memory_dir
        )
        applicable = [
            memory
            for memory in all_memories
            if scopes_match(memory["scopes"], current_scopes)
        ]
    if args.maintenance:
        selected = applicable
    else:
        selected = select_memories(
            connection, applicable, args.query, args.budget_tokens
        )
    for memory in selected:
        if args.json or args.maintenance:
            print(canonical_json(memory))
        else:
            print(f"- {memory['claim']}")

    if args.maintenance:
        print(f"GENERATION: {memory_generation(applicable)}", file=sys.stderr)
    elif maintenance_due(connection, len(applicable), context_key(current_scopes)):
        print(
            "NOTICE: memory maintenance is due; run memory-read --maintenance.",
            file=sys.stderr,
        )
    if not (args.all or args.maintenance) and len(selected) < len(applicable):
        print(
            f"NOTICE: selected {len(selected)} of {len(applicable)} applicable memories.",
            file=sys.stderr,
        )


def build_memory_content(
    claim: str,
    memory_type: str,
    *,
    pinned: bool = False,
    valid_from: str | None = None,
    valid_to: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    return {
        "claim": validate_claim(claim),
        "memory_type": memory_type,
        "status": ACTIVE_STATUS,
        "pinned": pinned,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "confidence": confidence,
    }


def command_append(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    if args.fact:
        fact = " ".join(args.fact)
    elif sys.stdin.isatty():
        raise MemoryCliError("usage: memory-append [options] <fact>")
    else:
        fact = sys.stdin.read()
    claim = validate_claim(fact)
    scopes = resolve_context_scopes(args.scope, Path.cwd(), paths.memory_dir)
    duplicate = next(
        (
            memory
            for memory in active_memories(connection)
            if memory["claim"] == claim
            and scope_identities(memory["scopes"]) == scope_identities(scopes)
        ),
        None,
    )
    if duplicate is not None:
        sync_portable_log(connection, paths, "memory: sync event log")
        print(f"Memory already exists: {duplicate['memory_id']}")
        return
    for memory_id in args.supersedes:
        row = connection.execute(
            "SELECT status FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if row is None or row["status"] != ACTIVE_STATUS:
            raise MemoryCliError(
                f"cannot supersede inactive or unknown memory: {memory_id}"
            )
    event = make_event(
        "memory.created",
        memory_id=uuid7(),
        scopes=scopes,
        content=build_memory_content(
            claim,
            args.memory_type,
            pinned=args.pin,
            valid_from=args.valid_from,
            valid_to=args.valid_to,
            confidence=args.confidence,
        ),
        actor_type=args.actor,
        derived_from=args.source,
        supersedes=args.supersedes,
    )
    with connection:
        insert_event(connection, event)
    sync_portable_log(connection, paths, "memory: append event")
    print(f"Appended memory: {event['memory_id']}")


def command_rescope_legacy(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    project = detect_project(Path.cwd(), paths.memory_dir)
    if project is None:
        raise MemoryCliError("current directory is not a project")
    legacy_name = args.legacy_name or project.get("name")
    targets = [
        memory
        for memory in active_memories(connection)
        if any(
            scope["type"] == "legacy_project" and scope["id"] == legacy_name
            for scope in memory["scopes"]
        )
    ]
    events: list[dict[str, Any]] = []
    for memory in targets:
        scopes = [
            project if scope["type"] == "legacy_project" else scope
            for scope in memory["scopes"]
        ]
        events.append(
            make_event(
                "memory.updated",
                memory_id=memory["memory_id"],
                scopes=normalize_scopes(scopes),
                content=build_memory_content(
                    memory["claim"],
                    memory["memory_type"],
                    pinned=memory["pinned"],
                    valid_from=memory["valid_from"],
                    valid_to=memory["valid_to"],
                    confidence=memory["confidence"],
                ),
                derived_from=(f"legacy-project:{legacy_name}",),
                retention=memory["retention"],
            )
        )
    with connection:
        for event in events:
            insert_event(connection, event)
    sync_portable_log(connection, paths, "memory: rescope legacy project")
    print(f"Rescoped {len(events)} legacy memories to {project['id']}.")


def parse_maintenance_input() -> list[dict[str, Any]]:
    if sys.stdin.isatty():
        raise MemoryCliError(
            "memory-maintain requires replacement facts on standard input"
        )
    replacements: list[dict[str, Any]] = []
    seen_memory_ids: set[str] = set()
    for line_number, raw_line in enumerate(sys.stdin, 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            value = strict_json_loads(line)
        except (json.JSONDecodeError, ValueError) as error:
            raise MemoryCliError(
                f"maintenance input at line {line_number} must be valid JSONL"
            ) from error
        if not isinstance(value, dict):
            raise MemoryCliError(
                f"maintenance JSON at line {line_number} must be an object"
            )
        value["claim"] = validate_claim(value.get("claim"))
        memory_id = value.get("memory_id")
        if memory_id is None:
            if "scopes" not in value:
                raise MemoryCliError(
                    f"new maintenance memory at line {line_number} requires scopes"
                )
        else:
            memory_id = str(memory_id)
            if memory_id in seen_memory_ids:
                raise MemoryCliError(f"duplicate replacement memory_id: {memory_id}")
            seen_memory_ids.add(memory_id)
            value["memory_id"] = memory_id
        replacements.append(value)
    if not replacements:
        raise MemoryCliError("at least one replacement fact is required")
    return replacements


def replacement_event(
    existing: dict[str, Any], replacement: dict[str, Any], generation: str
) -> dict[str, Any]:
    scopes = normalize_scopes(replacement.get("scopes", existing["scopes"]))
    memory_type = replacement.get("memory_type", existing["memory_type"])
    if memory_type not in MEMORY_TYPES:
        raise MemoryCliError(f"unsupported memory type: {memory_type}")
    return make_event(
        "memory.updated",
        memory_id=existing["memory_id"],
        scopes=scopes,
        content=build_memory_content(
            replacement["claim"],
            memory_type,
            pinned=bool(replacement.get("pinned", existing["pinned"])),
            valid_from=replacement.get("valid_from", existing["valid_from"]),
            valid_to=replacement.get("valid_to", existing["valid_to"]),
            confidence=replacement.get("confidence", existing["confidence"]),
        ),
        actor_type="agent",
        derived_from=(f"maintenance:{generation}",),
        retention=replacement.get("retention", existing["retention"]),
    )


def command_maintain(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    all_active = active_memories(connection)
    if args.all:
        current_scopes = None
        existing = all_active
    else:
        current_scopes = resolve_context_scopes(
            args.scope, Path.cwd(), paths.memory_dir
        )
        existing = [
            memory
            for memory in all_active
            if scopes_match(memory["scopes"], current_scopes)
        ]
    expected_generation = args.generation
    current_generation = memory_generation(existing)
    if expected_generation != current_generation:
        raise MemoryCliError(
            "memory changed after it was read; run memory-read --maintenance again", 75
        )
    replacements = parse_maintenance_input()
    by_id = {memory["memory_id"]: memory for memory in existing}
    retained_ids: set[str] = set()
    events: list[dict[str, Any]] = []
    for replacement in replacements:
        memory_id = replacement.get("memory_id")
        if memory_id is not None:
            current = by_id.get(str(memory_id))
            if current is None:
                raise MemoryCliError(f"unknown replacement memory_id: {memory_id}")
            replacement_scopes = normalize_scopes(
                replacement.get("scopes", current["scopes"])
            )
            if current_scopes is not None and scope_identities(
                replacement_scopes
            ) != scope_identities(current["scopes"]):
                raise MemoryCliError(
                    "scoped maintenance cannot move an existing memory; use --all"
                )
            retained_ids.add(current["memory_id"])
            if any(
                replacement.get(key, current.get(key)) != current.get(key)
                for key in (
                    "claim",
                    "memory_type",
                    "pinned",
                    "scopes",
                    "valid_from",
                    "valid_to",
                    "confidence",
                    "retention",
                )
            ):
                events.append(
                    replacement_event(current, replacement, expected_generation)
                )
            continue
        scopes = normalize_scopes(replacement["scopes"])
        if current_scopes is not None and not scopes_match(scopes, current_scopes):
            raise MemoryCliError("new maintenance memory is outside the selected scope")
        memory_type = replacement.get("memory_type", "semantic")
        events.append(
            make_event(
                "memory.created",
                memory_id=uuid7(),
                scopes=scopes,
                content=build_memory_content(
                    replacement["claim"],
                    memory_type,
                    pinned=bool(replacement.get("pinned", False)),
                    valid_from=replacement.get("valid_from"),
                    valid_to=replacement.get("valid_to"),
                    confidence=replacement.get("confidence"),
                ),
                derived_from=(f"maintenance:{expected_generation}",),
                retention=replacement.get("retention"),
            )
        )

    for memory in existing:
        if memory["memory_id"] in retained_ids:
            continue
        events.append(
            make_event(
                "memory.retracted",
                memory_id=memory["memory_id"],
                scopes=memory["scopes"],
                content={"status": "retracted", "reason": "maintenance"},
                derived_from=(f"maintenance:{expected_generation}",),
            )
        )

    events.append(
        make_event(
            "maintenance.completed",
            memory_id=None,
            scopes=current_scopes or [owner_scope()],
            content={
                "active_count": len(replacements),
                "scope_key": context_key(current_scopes),
            },
            derived_from=(f"generation:{expected_generation}",),
        )
    )
    with connection:
        for event in events:
            insert_event(connection, event)
    sync_portable_log(connection, paths, "memory: maintain events")
    print(f"Maintained memory with {len(replacements)} facts.")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_bundle(
    connection: sqlite3.Connection, paths: StorePaths, destination: Path
) -> None:
    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise MemoryCliError(
            f"export destination already exists: {destination}", 73
        ) from error
    schema_dir = destination / "schemas"
    schema_dir.mkdir()
    events_path = destination / "events.jsonl"
    schema_path = schema_dir / paths.event_schema.name
    export_events_atomic(connection, events_path)
    shutil.copyfile(paths.event_schema, schema_path)
    schema_path.chmod(0o600)

    event_count, last_sequence = connection.execute(
        "SELECT COUNT(*), COALESCE(MAX(sequence), 0) FROM events"
    ).fetchone()
    manifest = {
        "format": "agent-memory-export",
        "format_version": 1,
        "dataset_id": get_metadata(connection, "dataset_id"),
        "created_at": utc_now(),
        "producer": "agent-memory",
        "event_count": event_count,
        "last_sequence": last_sequence,
        "event_schema": EVENT_SCHEMA_URI,
        "last_maintained_at": get_metadata(connection, "last_maintained_at:all"),
    }
    manifest_path = destination / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            manifest,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path.chmod(0o600)

    checksum_paths = [events_path, manifest_path, schema_path]
    checksums = destination / "checksums.sha256"
    checksums.write_text(
        "".join(
            f"{sha256_file(path)}  {path.relative_to(destination).as_posix()}\n"
            for path in checksum_paths
        ),
        encoding="utf-8",
    )
    checksums.chmod(0o600)
    destination.chmod(0o700)
    schema_dir.chmod(0o700)


def command_export(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    if args.output is None:
        for row in connection.execute("SELECT * FROM events ORDER BY sequence"):
            print(canonical_json(row_to_event(row)))
        return
    export_bundle(connection, paths, args.output.expanduser())
    print(f"Exported memory bundle to {args.output.expanduser()}")


def verify_bundle(bundle: Path) -> tuple[Path, dict[str, Any]]:
    events_path = bundle / "events.jsonl"
    checksums_path = bundle / "checksums.sha256"
    manifest_path = bundle / "manifest.json"
    schema_path = bundle / "schemas" / "memory_event_v1.schema.json"
    required_files = [events_path, checksums_path, manifest_path, schema_path]
    missing = [
        path.relative_to(bundle).as_posix()
        for path in required_files
        if not path.is_file()
    ]
    if missing:
        raise MemoryCliError(
            f"bundle is missing required files: {', '.join(missing)}", 66
        )
    try:
        manifest = strict_json_loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as error:
        raise MemoryCliError("bundle manifest is not valid JSON", 65) from error
    if not isinstance(manifest, dict):
        raise MemoryCliError("bundle manifest must be an object", 65)
    expected_manifest = {
        "format": "agent-memory-export",
        "format_version": 1,
        "event_schema": EVENT_SCHEMA_URI,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) != expected:
            raise MemoryCliError(f"bundle manifest has unsupported {key}", 65)
    dataset_id = manifest.get("dataset_id")
    try:
        uuid.UUID(str(dataset_id))
    except (ValueError, AttributeError) as error:
        raise MemoryCliError("bundle manifest has an invalid dataset_id", 65) from error

    checked_paths: set[str] = set()
    for line_number, raw_line in enumerate(
        checksums_path.read_text(encoding="utf-8").splitlines(), 1
    ):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", raw_line)
        if match is None:
            raise MemoryCliError(
                f"invalid checksum entry at {checksums_path}:{line_number}", 65
            )
        expected, relative_name = match.groups()
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise MemoryCliError(f"unsafe checksum path: {relative_name}", 65)
        if relative_name in checked_paths:
            raise MemoryCliError(f"duplicate checksum path: {relative_name}", 65)
        checked_paths.add(relative_name)
        target = bundle / relative
        if not target.is_file() or sha256_file(target) != expected:
            raise MemoryCliError(f"bundle checksum failed: {relative_name}", 65)
    required_checksums = {
        "events.jsonl",
        "manifest.json",
        "schemas/memory_event_v1.schema.json",
    }
    if not required_checksums.issubset(checked_paths):
        raise MemoryCliError("bundle checksums do not cover every required file", 65)
    local_schema = Path(__file__).with_name("memory_event_v1.schema.json")
    if schema_path.read_bytes() != local_schema.read_bytes():
        raise MemoryCliError("bundle contains an unsupported event schema", 65)
    events = list(iter_event_file(events_path))
    sequences: list[int] = []
    for event in events:
        sequence = event.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise MemoryCliError("bundle events require local sequence values", 65)
        sequences.append(sequence)
    if sequences != list(range(1, len(events) + 1)):
        raise MemoryCliError(
            "bundle event sequences must be continuous, unique, and ordered", 65
        )
    event_ids = [event["event_id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise MemoryCliError("bundle event IDs must be unique", 65)
    event_count = manifest.get("event_count")
    last_sequence = manifest.get("last_sequence")
    if (
        isinstance(event_count, bool)
        or not isinstance(event_count, int)
        or event_count != len(events)
    ):
        raise MemoryCliError("bundle manifest event_count does not match events", 65)
    expected_last = 0 if not sequences else sequences[-1]
    if (
        isinstance(last_sequence, bool)
        or not isinstance(last_sequence, int)
        or last_sequence != expected_last
    ):
        raise MemoryCliError("bundle manifest last_sequence does not match events", 65)
    return events_path, manifest


def import_preview(event: dict[str, Any]) -> dict[str, Any]:
    content = event["content"]
    return {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "memory_id": event.get("memory_id"),
        "claim": content.get("claim"),
        "pinned": bool(content.get("pinned", False)),
        "scopes": event["scopes"],
    }


def validate_import_trust(event: dict[str, Any], args: argparse.Namespace) -> None:
    user_ids = {scope["id"] for scope in event["scopes"] if scope["type"] == "user"}
    if (
        user_ids
        and owner_scope()["id"] not in user_ids
        and not args.allow_foreign_owner
    ):
        raise MemoryCliError(
            "import contains a foreign owner; inspect with --dry-run and use "
            "--allow-foreign-owner to accept it"
        )
    content = event["content"]
    has_project = any(scope["type"] == "project" for scope in event["scopes"])
    if content.get("pinned") and not has_project and not args.allow_pinned_global:
        raise MemoryCliError(
            "import contains pinned global memory; inspect with --dry-run and use "
            "--allow-pinned-global to accept it"
        )


def command_import(
    connection: sqlite3.Connection, paths: StorePaths, args: argparse.Namespace
) -> None:
    manifest: dict[str, Any] | None = None
    if args.source == "-":
        descriptor, temporary_name = tempfile.mkstemp(
            prefix="agent-memory-import-", suffix=".jsonl"
        )
        source_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(sys.stdin.read())
            imported, previews = import_event_path(connection, source_path, args)
        finally:
            source_path.unlink(missing_ok=True)
    else:
        source_path = Path(args.source).expanduser()
        if source_path.is_dir():
            source_path, manifest = verify_bundle(source_path)
        imported, previews = import_event_path(
            connection,
            source_path,
            args,
            dataset_id=None if manifest is None else str(manifest["dataset_id"]),
        )
    if args.dry_run:
        for preview in previews:
            print(canonical_json(preview))
    if not args.dry_run:
        sync_portable_log(connection, paths, "memory: import events")
    action = "Validated" if args.dry_run else "Imported"
    print(f"{action} {imported} new events.")


def import_event_path(
    connection: sqlite3.Connection,
    source_path: Path,
    args: argparse.Namespace,
    dataset_id: str | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    imported = 0
    previews: list[dict[str, Any]] = []
    was_empty = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
    connection.execute("BEGIN IMMEDIATE")
    try:
        for event in iter_event_file(source_path):
            validate_import_trust(event, args)
            if insert_event(connection, event):
                imported += 1
                previews.append(import_preview(event))
        if dataset_id is not None and was_empty:
            set_metadata(connection, "dataset_id", dataset_id)
        if args.dry_run:
            connection.rollback()
        else:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    return imported, previews


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-memory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser(
        "read", help="retrieve relevant active memories"
    )
    read_parser.add_argument("--query", help="short description of the current task")
    read_parser.add_argument(
        "--scope",
        action="append",
        help="global, project, auto, or type:id; repeat for multiple scopes",
    )
    read_parser.add_argument(
        "--budget-tokens",
        type=int,
        default=int(
            os.environ.get("AGENT_MEMORY_BUDGET_TOKENS", DEFAULT_BUDGET_TOKENS)
        ),
    )
    read_parser.add_argument(
        "--all", action="store_true", help="read all active memories"
    )
    read_parser.add_argument(
        "--maintenance",
        action="store_true",
        help="read active memories in scope and print a generation token",
    )
    read_parser.add_argument("--json", action="store_true", help="emit memory JSONL")

    append_parser = subparsers.add_parser("append", help="append a durable memory")
    append_parser.add_argument("fact", nargs="*")
    append_parser.add_argument(
        "--type",
        dest="memory_type",
        choices=sorted(MEMORY_TYPES),
        default="semantic",
    )
    append_parser.add_argument("--scope", action="append")
    append_parser.add_argument("--pin", action="store_true")
    append_parser.add_argument("--actor", default="agent")
    append_parser.add_argument("--source", action="append", default=[])
    append_parser.add_argument("--supersedes", action="append", default=[])
    append_parser.add_argument("--valid-from")
    append_parser.add_argument("--valid-to")
    append_parser.add_argument("--confidence", type=float)

    rescope_parser = subparsers.add_parser(
        "rescope-legacy", help="assign legacy project facts to the current project"
    )
    rescope_parser.add_argument("legacy_name", nargs="?")

    maintain_parser = subparsers.add_parser(
        "maintain", help="replace the active memory projection safely"
    )
    maintain_parser.add_argument("generation")
    maintain_parser.add_argument("--scope", action="append")
    maintain_parser.add_argument("--all", action="store_true")

    export_parser = subparsers.add_parser("export", help="export portable JSONL")
    export_parser.add_argument(
        "--output", type=Path, help="create a self-contained export bundle"
    )

    import_parser = subparsers.add_parser("import", help="import JSONL or a bundle")
    import_parser.add_argument("source", help="JSONL file, bundle directory, or -")
    import_parser.add_argument("--dry-run", action="store_true")
    import_parser.add_argument("--allow-foreign-owner", action="store_true")
    import_parser.add_argument("--allow-pinned-global", action="store_true")
    return parser


def dispatch(
    connection: sqlite3.Connection,
    paths: StorePaths,
    args: argparse.Namespace,
) -> None:
    if args.command == "read":
        if args.budget_tokens < 1:
            raise MemoryCliError("--budget-tokens must be positive")
        command_read(connection, paths, args)
    elif args.command == "append":
        command_append(connection, paths, args)
    elif args.command == "maintain":
        command_maintain(connection, paths, args)
    elif args.command == "rescope-legacy":
        command_rescope_legacy(connection, paths, args)
    elif args.command == "export":
        command_export(connection, paths, args)
    elif args.command == "import":
        command_import(connection, paths, args)
    else:
        raise MemoryCliError(f"unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = resolve_paths()
    try:
        prepare_memory_dir(paths)
        with memory_lock(paths):
            connection = connect_database(paths)
            try:
                migration = initialize_database(connection, paths)
                git_message = (
                    "memory: migrate portable event log"
                    if migration == "legacy Markdown"
                    else "memory: sync event log"
                )
                sync_portable_log(connection, paths, git_message)
                if migration == "legacy Markdown":
                    print(
                        "NOTICE: migrated legacy memory.md into the event store.",
                        file=sys.stderr,
                    )
                    for name in legacy_project_names(connection):
                        print(
                            "NOTICE: from the intended project, run "
                            f"memory-rescope-legacy {name} to adopt its legacy memories.",
                            file=sys.stderr,
                        )
                dispatch(connection, paths, args)
            finally:
                connection.close()
    except MemoryCliError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return error.exit_code
    except (OSError, sqlite3.Error) as error:
        print(f"ERROR: agent memory failed: {error}", file=sys.stderr)
        return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
