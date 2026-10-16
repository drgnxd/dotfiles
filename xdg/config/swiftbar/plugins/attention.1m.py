#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Menu bar view of everything that needs attention, and proof that the watcher itself is alive.

A thin reader of the report written by the attention collector; it holds no policy. It always
shows something: a green check with the last check time when all is well, so a stale or missing
report is visible as a different icon. When the report is missing or old it falls back to its own
quick look at the launchd jobs and failure markers instead of showing nothing.

Every string is sanitized again because `|` and newlines are SwiftBar control characters. Apply
hints are plain text; only fixed acknowledge and re-check actions are clickable.
"""

import getpass
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

STATE = Path(os.environ.get("ATTENTION_STATE_DIR", Path.home() / ".local/state/attention")) / "state.json"
MARKER_DIR = Path.home() / ".local/state/automation-failures"
PREFIX = "com.drgnxd."
SCHEMA = 1
STALE_AFTER = timedelta(minutes=20)
RED, ORANGE, GREEN, GRAY = "#d62728", "#e08a00", "#2e7d32", "#888888"
UNSAFE = re.compile("[\x00-\x1f\x7f-\x9f|­؜​-‏ -‮⁠-⁤⁦-⁩﻿]")
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+@/:-]{0,99}$")
SAFE_PATH = re.compile(r"^/[A-Za-z0-9._+@/~-]+$")
PLAIN = " emojize=false symbolize=false"
CATEGORY = {"job": "ジョブ", "runtime": "ランタイム", "update": "更新", "nix": "Nix", "monitor": "監視"}


def clean(text, limit=100):
    return UNSAFE.sub(" ", str(text)).strip().lstrip("-").strip()[:limit]


def line(text, *params):
    return f"{text} | {' '.join(params)}{PLAIN}" if params else f"{text} |{PLAIN}"


def parse(stamp):
    try:
        moment = datetime.fromisoformat(str(stamp))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.astimezone()


def hhmm(moment):
    return moment.astimezone().strftime("%H:%M") if moment else "?"


def ago(moment, now):
    if not moment:
        return "?"
    minutes = int((now - moment).total_seconds() // 60)
    return f"{minutes} 分前" if minutes < 120 else f"{minutes // 60} 時間前"


def wake_time():
    """When the machine last woke; the collector cannot have run while it slept."""
    try:
        out = subprocess.run(["/usr/sbin/sysctl", "-n", "kern.waketime"], capture_output=True, text=True, timeout=5).stdout
        match = re.search(r"sec = (\d+)", out)
        return datetime.fromtimestamp(int(match.group(1))).astimezone() if match else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def uv_path():
    for candidate in (f"/etc/profiles/per-user/{getpass.getuser()}/bin/uv", str(Path.home() / ".nix-profile/bin/uv"),
                      "/run/current-system/sw/bin/uv"):
        if os.access(candidate, os.X_OK):
            return candidate
    return None


def command(report, *arguments):
    script, uv = report.get("script"), uv_path()
    if not (isinstance(script, str) and SAFE_PATH.fullmatch(script) and uv):
        return []
    values = ["run", "--script", script, *arguments]
    return [f"bash={uv}", *[f"param{i}={v}" for i, v in enumerate(values, 1)], "terminal=false", "refresh=true"]


def load():
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "状態ファイルがありません"
    report = state.get("report") if isinstance(state, dict) else None
    if not isinstance(report, dict) or state.get("schema") != SCHEMA or report.get("schema") != SCHEMA:
        return None, "状態の形式が合いません (プラグインとハブの版がずれています)"
    return report, ""


def fallback(reason, report, now):
    """The collector is not reporting: show launchd failures and markers directly, flagged as degraded."""
    problems = {}
    try:
        rows = subprocess.run(["/bin/launchctl", "list"], capture_output=True, text=True, timeout=10).stdout.splitlines()[1:]
        for row in rows:
            parts = row.split("\t")
            if len(parts) == 3 and parts[2].startswith(PREFIX) and parts[1] not in ("0", "-"):
                problems[clean(parts[2][len(PREFIX):], 40)] = f"終了コード {clean(parts[1], 6)}"
    except (OSError, subprocess.SubprocessError):
        pass
    markers = sorted(clean(p.stem, 40) for p in MARKER_DIR.glob("*.json")) if MARKER_DIR.is_dir() else []
    for name in markers:
        problems[name] = (problems[name] + "・" if name in problems else "") + "失敗マーカー"
    total = len(problems)
    out = [line(f"⚠? {total}" if total else "?", f"color={ORANGE if total else GRAY}"), "---",
           line(f"⚠ 監視ハブの報告がありません: {clean(reason, 70)}", f"color={ORANGE}")]
    last = parse(report.get("generated_at")) if report else None
    if last:
        out.append(line(f"最後の確認 {hhmm(last)} ({ago(last, now)})", f"color={GRAY}"))
    hub = report.get("hub") if isinstance(report, dict) else None
    if isinstance(hub, dict) and KEY_RE.fullmatch(str(hub.get("label", ""))):
        out.append(line(f"再起動: launchctl kickstart -k gui/{os.getuid()}/{clean(hub['label'], 60)}", f"color={GRAY}"))
    else:
        out.append(line("ハブの LaunchAgent が登録されているか確認してください", f"color={GRAY}"))
    out.append("---")
    out.append(line("簡易確認 (ハブを介さない)", f"color={GRAY}", "size=11"))
    out += [line(f"⚠ {name} ({why})") for name, why in sorted(problems.items())[:15]]
    if not total:
        out.append(line("✓ launchd とマーカーに異常は見えません", f"color={GRAY}"))
    return out


def render(report, reason, now):
    if report is None:
        return fallback(reason, None, now)
    last = parse(report.get("generated_at"))
    base = max([m for m in (last, wake_time()) if m], default=None)
    if base is None or now - base > STALE_AFTER:
        return fallback("最終確認から時間が経っています", report, now)
    items = [i for i in report.get("items", []) if isinstance(i, dict) and KEY_RE.fullmatch(str(i.get("key", "")))]
    counts = report.get("counts", {})
    urgent, action = int(counts.get("urgent", 0)), int(counts.get("action", 0))
    total = urgent + action
    out = []
    if total:
        out.append(line(f"⚠ {total}", f"color={RED if urgent else ORANGE}"))
    else:
        out.append(line("✓", f"color={GREEN}"))
    out.append("---")
    out.append(line(f"最終確認 {hhmm(last)} ({ago(last, now)})", f"color={GRAY}", "size=11"))
    bad_sources = {k: v for k, v in report.get("sources", {}).items() if isinstance(v, dict) and v.get("status") != "ok"}
    if not total:
        out.append(line("✓ 要対応はありません", f"color={GREEN}"))
    for severity, label in (("urgent", "緊急"), ("action", "要対応"), ("info", "参考")):
        group = [i for i in items if i.get("severity") == severity and not i.get("acked")]
        if not group:
            continue
        out.append(line(label, "size=11", f"color={GRAY}"))
        for item in group:
            mark = " (古い情報)" if item.get("stale") else ""
            out.append(line(f"{CATEGORY.get(item.get('category'), '')} {clean(item.get('title'), 90)}{mark}".strip(),
                            f"color={RED if severity == 'urgent' else ORANGE if severity == 'action' else GRAY}"))
            for detail in item.get("details", [])[:6]:
                out.append(line(f"--{clean(detail, 110)}"))
            if item.get("hint"):
                out.append(line(f"--対処: {clean(item['hint'], 140)}"))
            if severity == "action":
                for days in (1, 3, 7):
                    params = command(report, "ack", item["key"], str(days), "menu-bar")
                    if params:
                        out.append(line(f"--{days} 日間 確認済みにする", *params))
    acked = [i for i in items if i.get("acked")]
    if acked:
        out.append(line("確認済み", "size=11", f"color={GRAY}"))
        out += [line(f"{clean(i.get('title'), 90)}", f"color={GRAY}") for i in acked]
    for name, status in bad_sources.items():
        out.append(line(f"⚠ 確認元 {clean(name, 24)}: {clean(status.get('error', ''), 90)}", f"color={ORANGE}"))
    jobs = [j for j in report.get("jobs", []) if isinstance(j, dict)]
    ok = [j for j in jobs if j.get("state") == "ok"]
    out.append("---")
    out.append(line(f"ジョブ {len(ok)}/{len([j for j in jobs if j.get('state') != 'disabled'])} 件 正常", f"color={GREEN if len(ok) == len([j for j in jobs if j.get('state') != 'disabled']) else GRAY}"))
    for job in jobs:
        glyph = {"ok": "✓", "disabled": "−"}.get(job.get("state"), "⚠")
        out.append(line(f"--{glyph} {clean(job.get('short'), 40)}", f"color={GRAY if job.get('state') in ('ok', 'disabled') else ORANGE}"))
    updates = report.get("updates", {})
    last_update = parse(updates.get("last_run"))
    waiting = [w for w in updates.get("waiting", []) if isinstance(w, dict)]
    out.append(line(f"更新の確認 {hhmm(last_update)} ・待機/保留 {len(waiting)} 件", f"color={GRAY}"))
    for w in waiting[:8]:
        out.append(line(f"--{clean(w.get('title'), 50)} ({clean(w.get('state'), 8)} {clean(w.get('ready_at'), 10)})", f"color={GRAY}"))
    for name, status in report.get("sources", {}).items():
        if isinstance(status, dict) and status.get("status") == "ok":
            out.append(line(f"--✓ 確認元 {clean(name, 24)}", f"color={GRAY}"))
    recheck = command(report, "check")
    if recheck:
        out += ["---", line("今すぐ再確認", *recheck)]
    return out


def main():
    now = datetime.now().astimezone()
    try:
        report, reason = load()
        lines = render(report, reason, now)
    except Exception as exc:  # the watcher must never fail silently
        lines = [line("✗ 監視エラー", f"color={RED}"), "---", line(f"{clean(type(exc).__name__, 40)}: {clean(exc, 80)}")]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
