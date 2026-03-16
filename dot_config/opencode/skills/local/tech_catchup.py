#!/usr/bin/env python3
"""Hacker News Tech Catchup - All top 30 stories"""

import json, time, hashlib
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


class HNCatchup:
    def __init__(self):
        self.base = "https://hacker-news.firebaseio.com/v0"
        # Script location relative paths
        script_dir = Path(__file__).parent
        self.state = script_dir / "data/hackernews/last_run.json"
        self.out = Path.home() / "dev/info"
        self.out.mkdir(parents=True, exist_ok=True)

    def fetch(self, url):
        time.sleep(0.1)
        try:
            return json.loads(urlopen(url, timeout=10).read())
        except Exception as e:
            print(f"Error: {e}")
            return None

    def run(self):
        print("Fetching HN top stories...")
        ids = self.fetch(f"{self.base}/topstories.json")[:30]

        stories = []
        for i, sid in enumerate(ids, 1):
            s = self.fetch(f"{self.base}/item/{sid}.json")
            if s and s.get("score", 0) >= 50:
                s["rank"] = i
                s["domain"] = (
                    s.get("url", "").split("/")[2]
                    if s.get("url")
                    else "news.ycombinator.com"
                )
                stories.append(s)

        prev = json.loads(self.state.read_text()) if self.state.exists() else None

        # Detect changes
        new, updated = [], []
        if prev:
            prev_map = {x["id"]: x for x in prev.get("stories", [])}
            for s in stories:
                if s["id"] not in prev_map:
                    new.append(s)
                else:
                    p = prev_map[s["id"]]
                    ch = {}
                    if abs(s["score"] - p["score"]) >= 20:
                        ch["score"] = s["score"] - p["score"]
                    if abs(s.get("descendants", 0) - p.get("descendants", 0)) >= 10:
                        ch["comments"] = s.get("descendants", 0) - p.get(
                            "descendants", 0
                        )
                    if abs(p["rank"] - s["rank"]) >= 5:
                        ch["rank"] = p["rank"] - s["rank"]
                    if ch:
                        s["changes"] = ch
                        updated.append(s)
        else:
            new = stories

        # Generate report
        d = datetime.now()
        lines = [
            f"## HN テックキャッチアップ - {d.strftime('%Y-%m-%d')}",
            "",
            f"新着: {len(new)}件 / 更新: {len(updated)}件 / 合計: {len(stories)}件",
            "",
        ]

        # All top 30 stories
        lines.append("### 上位30件")
        for s in stories:
            marker = ""
            if s in new:
                marker = " 🆕"
            elif s in updated:
                marker = " ⬆️"
            lines.append(f"{s['rank']}. **{s['title']}**{marker}")
            lines.append(
                f"   - {s.get('url', 'https://news.ycombinator.com')} ({s['domain']})"
            )
            lines.append(
                f"   - {s['score']} pts | {s.get('descendants', 0)} comments | by {s.get('by', 'unknown')}"
            )
            lines.append("")

        # New stories summary
        if new:
            lines.extend(["### 新着ストーリー詳細", ""])
            for s in new:
                lines.append(f"- **{s['title']}** ({s['domain']})")

        lines.extend(["", f"*Generated: {d.isoformat()}*"])

        report = self.out / f"{d.strftime('%Y%m%d')}.md"
        report.write_text("\n".join(lines))

        # Save state
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text(
            json.dumps(
                {
                    "timestamp": d.isoformat(),
                    "stories": [
                        {
                            "id": s["id"],
                            "title": s["title"],
                            "score": s["score"],
                            "descendants": s.get("descendants", 0),
                            "rank": s["rank"],
                        }
                        for s in stories
                    ],
                },
                indent=2,
            )
        )

        print(f"\n✓ Report saved: {report}")
        print(
            f"✓ Total stories: {len(stories)} (New: {len(new)}, Updated: {len(updated)})"
        )


if __name__ == "__main__":
    HNCatchup().run()
