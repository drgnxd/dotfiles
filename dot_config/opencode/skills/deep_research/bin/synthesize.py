#!/usr/bin/env python3

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize research notes")
    parser.add_argument("--input", required=True, help="Comma-separated input files")
    parser.add_argument("--output", required=True, help="Output markdown file")
    args = parser.parse_args()

    sections = []
    for path in [Path(item.strip()) for item in args.input.split(",") if item.strip()]:
        title = path.stem.replace("_", " ").title()
        content = path.read_text(encoding="utf-8")
        sections.extend([f"## {title}", "", content, ""])

    output = "\n".join(sections).strip() + "\n"
    Path(args.output).write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
