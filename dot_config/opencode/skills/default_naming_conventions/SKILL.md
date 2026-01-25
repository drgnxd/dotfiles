---
name: default_naming_conventions
description: Default filename and directory rules using the UNIX-Modern Snake Protocol
license: Apache-2.0
metadata:
  author: opencode
  version: "1.1.0"
  category: coding
---

## Purpose

Manage and suggest filenames and directory structures using the UNIX-Modern Snake Protocol when a project does not define its own naming rules.

## Core Principles

1. Apply only when no explicit naming rules exist.
2. Use lowercase snake_case for all filenames and directories.
3. Prioritize clarity and searchability over brevity.
4. Restrict names to approved abbreviations and allowed characters only.

## Rules/Standards

### Naming Rules (The Constitution)

- Case: use lowercase for all filenames and directories. Exception: `README.md` and `SKILL.md`.
- Separator: use underscores only; never use spaces or hyphens.
- Language: names must be English.
- Allowed characters: `a-z`, `0-9`, `_`, `.` only.

### Abbreviation Policy

- Use abbreviations only for industry standards:
  - `src`, `lib`, `doc`, `cfg`, `bin`, `tmp`, `env`, `pkg`
- For all other words, use full spelling for clarity and searchability.

### Directory Structure Suggestions

- Prefer full words for domain-specific directories (`research`, `templates`).
- Use approved abbreviations for conventional directories (`src`, `doc`, `bin`).

## Style Examples

✅ Good

- `example_pattern.md`
- `user_cfg.json`
- `biomimetic_robot_research.pdf`
- `src/main_logic.c`

❌ Bad

- `ex_pat.md` (unapproved abbreviation)
- `user-configuration.json` (hyphen)
- `UserConfiguration.json` (uppercase)
- `user config.json` (space)

## Instruction

Strictly adhere to these rules when interacting with drgnxd. Prioritize clarity and ease of searching over extreme brevity.

## Edge Cases

- If the existing codebase clearly follows another convention, prefer that.
- If a specification mandates a fixed name, keep the mandated name.

Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://google.github.io/styleguide/
- https://developer.mozilla.org/en-US/docs/Glossary/Snake_case
- https://peps.python.org/pep-0008/
