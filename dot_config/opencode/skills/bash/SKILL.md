---
name: bash
description: Bash scripting standards for safe automation
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Bash

## Purpose

Establish consistent and safe shell scripting practices for automation tasks.

## Core Principles

1. Make scripts predictable and fail fast.
2. Quote variables to prevent word splitting.
3. Prefer explicit checks over assumptions.

## Rules/Standards

### Safety

- Use `set -euo pipefail` unless the script requires different behavior.
- Quote all variable expansions.
- Validate inputs and required commands.

### Structure

- Group logic into functions with clear names.
- Use `readonly` for constants.
- Log key steps and errors.

### Portability

- Avoid non-portable flags unless the environment is fixed.
- Document required shell version and dependencies.

## Examples

Good:
- "Quote paths and check exit codes for critical steps."

Bad:
- "Use unquoted variables and ignore failures."

## Edge Cases

- For destructive operations, add dry-run flags or confirmation prompts.
- For long-running tasks, add timeouts and progress logs.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://tiswww.case.edu/php/chet/bash/bashref.html#The-Set-Builtin
- https://man7.org/linux/man-pages/man1/bash.1.html
