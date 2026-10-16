#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Menu bar view of pending software updates.

A thin reader of the report written by the update collector; it holds no policy. Every
string is sanitized again here because it ends up on a SwiftBar line, where `|` starts
parameters and a newline starts another menu item. The apply commands are shown as text
only; only the fixed snooze and re-check actions are clickable.
"""

import getpass
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

STATE_DIR = Path(os.environ.get("UPDATE_WATCH_STATE_DIR", Path.home() / ".local/state/update-watch"))
STALE_AFTER = timedelta(hours=36)
ACTIONABLE = ("urgent", "overdue", "due_soon", "ready")
LABEL = {"urgent": "緊急", "overdue": "期限超過", "due_soon": "期限間近", "ready": "適用可",
         "waiting": "待機中", "held": "保留"}
COLOR = {"urgent": "#d62728", "overdue": "#d62728", "due_soon": "#e08a00", "ready": "#2e7d32"}
UNSAFE = re.compile("[\x00-\x1f\x7f-\x9f|\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
HASH_RE = re.compile(r"^[0-9a-f]{40}$")
PLAIN = " | emojize=false symbolize=false"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+@/:-]{0,99}$")
SAFE_PATH = re.compile(r"^/[A-Za-z0-9._+@/~-]+$")


def clean(text, limit=100):
    text = UNSAFE.sub(" ", str(text)).strip()
    return text.lstrip("-")[:limit]


def short(value):
    text = str(value)
    return text[:12] if HASH_RE.fullmatch(text) else text


def uv_path():
    user = getpass.getuser()
    for candidate in (f"/etc/profiles/per-user/{user}/bin/uv", str(Path.home() / ".nix-profile/bin/uv"),
                      "/run/current-system/sw/bin/uv"):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def command_params(state, *arguments):
    """SwiftBar bash= parameters for the collector CLI, or [] when it cannot be located."""
    script, uv = state.get("script"), uv_path()
    if not (isinstance(script, str) and SAFE_PATH.fullmatch(script) and uv):
        return []
    values = ["run", "--script", script, *arguments]
    return [f"bash={uv}", *[f"param{i}={v}" for i, v in enumerate(values, 1)], "terminal=false", "refresh=true"]


def short_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%m/%d")
    except (TypeError, ValueError):
        return "?"


def stale_reason(state, now):
    if not state:
        return "状態ファイルがありません"
    try:
        age = now - datetime.fromisoformat(state["last_run"])
    except (KeyError, TypeError, ValueError):
        return "実行記録がありません"
    if age > STALE_AFTER:
        return f"最終確認から {int(age.total_seconds() // 3600)} 時間経過"
    broken = [name for name, record in state.get("adapters", {}).items()
              if isinstance(record, dict) and record.get("failures", 0) >= 2]
    if broken:
        return "取得に連続失敗: " + ", ".join(clean(n, 20) for n in broken)
    return ""


def render(state, now):
    report = state.get("report", {}) if isinstance(state, dict) else {}
    items = [i for i in report.get("items", []) if isinstance(i, dict) and ID_RE.fullmatch(str(i.get("id", "")))]
    stale = stale_reason(state, now)
    actionable = [i for i in items if i.get("state") in ACTIONABLE]
    if not actionable and not stale:
        return []
    worst = next((s for s in ACTIONABLE if any(i["state"] == s for i in actionable)), None)
    lines = []
    if actionable:
        lines.append(f"⬆ {len(actionable)} | color={COLOR[worst]}")
    else:
        lines.append("⬆? | color=#888888")
    lines.append("---")
    if stale:
        lines.append(f"⚠ 情報が古い可能性: {clean(stale, 60)} | color=#888888")
    for key in ("urgent", "overdue", "due_soon", "ready", "waiting", "held"):
        group = [i for i in items if i.get("state") == key]
        if not group or (key in ("waiting", "held") and not actionable and not stale):
            continue
        lines.append(f"{LABEL[key]} | size=11 color=#888888")
        for item in group:
            badge = " 🔧" if item.get("job_runtime") else ""
            stale_mark = " (古い)" if item.get("stale") else ""
            target = clean(short(item.get("target")) if item.get("target") else "〜" + short_date(item.get("ready_at")), 24)
            lines.append(f"{clean(item.get('title'), 40)} {clean(short(item.get('installed')), 24)} → {target}"
                         f"  {clean(item.get('tier'), 3)} 期限 {short_date(item.get('deadline'))}{badge}{stale_mark}" + PLAIN)
            apply = clean(item.get("apply", ""), 120)
            if apply and key in ACTIONABLE:
                lines.append(f"--適用: {apply}" + PLAIN)
            if badge and key in ACTIONABLE:
                lines.append("--適用後に just relaunch-agents が必要" + PLAIN)
            for detail in item.get("details", [])[:8]:
                lines.append(f"--{clean(detail, 100)}" + PLAIN)
            if key in ACTIONABLE and item.get("tier") != "S0":
                for days in (1, 3, 7):
                    params = command_params(state, "snooze", item["id"], str(days), "menu-bar")
                    if params:
                        lines.append(f"--スヌーズ {days} 日 | " + " ".join(params))
    for note in report.get("info", [])[:6]:
        lines.append(f"ℹ {clean(note, 110)} | color=#888888 emojize=false symbolize=false")
    recheck = command_params(state, "check")
    if recheck:
        lines += ["---", "今すぐ再確認 | " + " ".join(recheck)]
    return lines


def main():
    now = datetime.now().astimezone()
    try:
        state = json.loads((STATE_DIR / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    print("\n".join(render(state, now)))


if __name__ == "__main__":
    main()
