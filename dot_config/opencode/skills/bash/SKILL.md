---
name: bash
description: Safe bash scripting for automation
---

# Bash

## Purpose
Consistent, safe shell scripting practices.

## Core Principles
1. Predictable execution, fail fast
2. Quote to prevent word splitting
3. Explicit checks over assumptions

## Rules

### Safety
- `set -euo pipefail` unless different needed
- Quote all variable expansions: `"${var}"`
- Validate inputs and required commands

### Structure
- Functions w/ clear names
- `readonly` for constants
- Log key steps/errors

### Portability
- Avoid non-portable flags unless env fixed
- Doc shell version & dependencies

## Examples

✅ Quote paths, check exit codes for critical steps
❌ Unquoted vars, ignore failures

## Edge Cases
- Destructive ops: dry-run flags or confirmation prompts
- Long tasks: timeouts, progress logs

See `COMMON.md` for naming/refs.

Refs: [bashref](https://tiswww.case.edu/php/chet/bash/bashref.html), [man](https://man7.org/linux/man-pages/man1/bash.1.html) (2026-01-26)
