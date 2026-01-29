#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import List


@dataclass
class SearchResult:
    title: str
    url: str
    source_type: str
    date: str
    summary: str
    confidence: str


def load_results(path: Path) -> List[SearchResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results: List[SearchResult] = []
    for item in payload:
        results.append(
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                source_type=item.get("source_type", ""),
                date=item.get("date", ""),
                summary=item.get("summary", ""),
                confidence=item.get("confidence", ""),
            )
        )
    return results


def build_report(query: str, sources: List[str], results: List[SearchResult], deep_dive: bool) -> str:
    header = [
        f"# Search Results: {query}",
        "",
        "## Metadata",
        f"- Search Date: {datetime.now().strftime('%Y-%m-%d')}",
        f"- Sources: {', '.join(sources)}",
        f"- Total Results: {len(results)}",
        f"- Deep Dive: {'yes' if deep_dive else 'no'}",
        "",
        "## Findings",
        "",
    ]
    body: List[str] = []
    if not results:
        body.append("No results collected. Provide --input with JSON results or add findings manually.")
    for index, result in enumerate(results, 1):
        body.extend(
            [
                f"### {index}. {result.title}",
                f"- URL: {result.url}",
                f"- Type: {result.source_type}",
                f"- Date: {result.date}",
                f"- Confidence: {result.confidence}",
                "",
                result.summary,
                "",
            ]
        )
    return "\n".join(header + body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep research search helper")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--sources", default="all", help="Comma-separated source types")
    parser.add_argument("--input", help="Path to JSON results")
    parser.add_argument("--deep-dive", action="store_true", help="Enable deep dive mode")
    parser.add_argument("--output", default="findings.md", help="Output markdown file")
    args = parser.parse_args()

    sources = args.sources.split(",") if args.sources != "all" else [
        "academic",
        "technical",
        "news",
        "blogs",
    ]

    results: List[SearchResult] = []
    if args.input:
        results = load_results(Path(args.input))

    report = build_report(args.query, sources, results, args.deep_dive)
    Path(args.output).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
