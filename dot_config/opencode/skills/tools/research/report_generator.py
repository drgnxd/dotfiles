#!/usr/bin/env python3

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deep research report")
    parser.add_argument("--synthesis", required=True, help="Synthesis markdown file")
    parser.add_argument("--template", help="Report template markdown file")
    parser.add_argument("--output", required=True, help="Output report file")
    args = parser.parse_args()

    synthesis = Path(args.synthesis).read_text(encoding="utf-8")

    if args.template:
        template = Path(args.template).read_text(encoding="utf-8")
    else:
        template = "# Deep Research Report\n\n## Synthesis Input\n"

    report = template.rstrip() + "\n\n## Synthesis Input\n\n" + synthesis
    Path(args.output).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
