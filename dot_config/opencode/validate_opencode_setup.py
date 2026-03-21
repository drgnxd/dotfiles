#!/usr/bin/env python3
"""Validate OpenCode rules, instructions, and skill layout.

This script enforces the minimal OpenCode structure used here:
- AGENTS.md at config root
- dcp.json for Dynamic Context Pruning defaults
- opencode.json with valid schema
- package.json for custom tool dependencies
- tools/*.ts for custom tools
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
LEGACY_SKILL_DIRS = {"essential", "specialized", "tools", "local"}


def _validate_skill_frontmatter(skill_file: Path, errors: list[str]) -> None:
    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Failed to read {skill_file}: {exc}")
        return

    lines = content.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        errors.append(f"{skill_file} must start with YAML frontmatter")
        return

    closing_idx = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_idx = idx
            break

    if closing_idx is None:
        errors.append(f"{skill_file} frontmatter is missing closing ---")
        return

    fields: dict[str, str] = {}
    for raw_line in lines[1:closing_idx]:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        errors.append(f"{skill_file} frontmatter must include non-empty name")
    if not description:
        errors.append(f"{skill_file} frontmatter must include non-empty description")


def _validate_skill_subdirectory(skill_dir: Path, errors: list[str]) -> None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        errors.append(f"{skill_dir} must contain SKILL.md")
        return
    _validate_skill_frontmatter(skill_file, errors)


def validate_config(errors: list[str]) -> None:
    config_path = BASE_DIR / "opencode.json"
    if not config_path.exists():
        errors.append(f"Missing required config file: {config_path}")
        return

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {config_path}: {exc}")
        return

    if config.get("$schema") != "https://opencode.ai/config.json":
        errors.append(
            "opencode.json should set $schema to https://opencode.ai/config.json"
        )


def validate_dcp_config(errors: list[str]) -> None:
    dcp_path = BASE_DIR / "dcp.json"
    if not dcp_path.exists():
        errors.append(f"Missing required config file: {dcp_path}")
        return

    try:
        config = json.loads(dcp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {dcp_path}: {exc}")
        return

    expected_schema = (
        "https://raw.githubusercontent.com/"
        "Opencode-DCP/opencode-dynamic-context-pruning/master/dcp.schema.json"
    )
    if config.get("$schema") != expected_schema:
        errors.append(f"dcp.json should set $schema to {expected_schema}")


def validate_package(errors: list[str]) -> None:
    package_path = BASE_DIR / "package.json"
    if not package_path.exists():
        errors.append(f"Missing required file: {package_path}")
        return

    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {package_path}: {exc}")
        return

    deps = package.get("dependencies", {})
    if not isinstance(deps, dict) or "@opencode-ai/plugin" not in deps:
        errors.append("package.json must include @opencode-ai/plugin in dependencies")


def validate_tools(errors: list[str]) -> None:
    tools_dir = BASE_DIR / "tools"
    if not tools_dir.exists() or not tools_dir.is_dir():
        errors.append(f"Missing required tools directory: {tools_dir}")
        return

    tool_files = sorted(tools_dir.glob("*.ts")) + sorted(tools_dir.glob("*.js"))
    if not tool_files:
        errors.append("tools/ must contain at least one .ts or .js custom tool")
        return

    for tool_file in tool_files:
        content = tool_file.read_text(encoding="utf-8")
        if "@opencode-ai/plugin" not in content:
            errors.append(f"{tool_file} should import @opencode-ai/plugin")
        if "export default tool(" not in content and "export const " not in content:
            errors.append(f"{tool_file} does not appear to export an OpenCode tool")


def validate_skills(errors: list[str]) -> None:
    skills_dir = BASE_DIR / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        errors.append(f"Missing required skills directory: {skills_dir}")
        return

    subdirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not subdirs:
        errors.append("skills/ must contain at least one subdirectory")
        return

    native_subdirs = [path for path in subdirs if path.name not in LEGACY_SKILL_DIRS]
    if not native_subdirs:
        errors.append("skills/ must contain at least one native skill subdirectory")
        return

    for skill_dir in native_subdirs:
        _validate_skill_subdirectory(skill_dir, errors)


def validate_skills_local(errors: list[str]) -> None:
    skills_local_dir = BASE_DIR / "skills" / "local"
    if not skills_local_dir.exists():
        return
    if not skills_local_dir.is_dir():
        errors.append(f"skills/local exists but is not a directory: {skills_local_dir}")
        return

    local_subdirs = sorted(path for path in skills_local_dir.iterdir() if path.is_dir())
    for skill_dir in local_subdirs:
        _validate_skill_subdirectory(skill_dir, errors)


def validate_agents_file(errors: list[str]) -> None:
    agents_path = BASE_DIR / "AGENTS.md"
    if not agents_path.exists():
        errors.append(f"Missing required file: {agents_path}")
        return

    if not agents_path.read_text(encoding="utf-8").strip():
        errors.append("AGENTS.md exists but is empty")


def main() -> int:
    errors: list[str] = []

    validate_agents_file(errors)
    validate_config(errors)
    validate_dcp_config(errors)
    validate_package(errors)
    validate_tools(errors)
    validate_skills(errors)
    validate_skills_local(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OpenCode setup validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
