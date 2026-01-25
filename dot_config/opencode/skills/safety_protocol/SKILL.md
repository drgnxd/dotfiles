---
name: safety_protocol
description: Safety rules for potentially destructive commands and changes
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: meta
---

# Safety Protocol

## Purpose

Provide a consistent safety checklist before suggesting or running commands that could delete data, overwrite files, or destabilize systems.

## Core Principles

1. Prevent accidental data loss through explicit warnings.
2. Make the impact of actions transparent and reversible when possible.
3. Require explicit confirmation before executing destructive steps.

## Rules/Standards

### Destructive Commands

- Treat commands like `rm`, `dd`, `mkfs`, `chmod -R`, `> overwrite`, and forced git operations as destructive.
- Explain what will change, where, and why it is needed.
- Ask for explicit confirmation before proceeding.

### Safer Alternatives

- Prefer non-destructive alternatives when feasible (dry-run flags, backups, or moving to a safe location).
- Offer a rollback plan if the change is irreversible.

### Scope Control

- Target the smallest possible scope (specific files, explicit paths).
- Avoid wildcard deletes unless the user explicitly requires them.

## Examples

Good:
- "This command will permanently delete `/path/to/data`. It cannot be undone. If you want, we can move the files to a backup directory first. Do you want me to proceed?"

Bad:
- "Running rm -rf now."

## Edge Cases

- If a destructive step is required for recovery, still ask for confirmation and document the recovery plan.
- If the user explicitly requests a destructive action, confirm the scope and intent before executing.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://man7.org/linux/man-pages/man1/rm.1.html (Last accessed: 2026-01-26)
- https://man7.org/linux/man-pages/man1/dd.1.html (Last accessed: 2026-01-26)
- https://man7.org/linux/man-pages/man8/mkfs.8.html (Last accessed: 2026-01-26)
- https://git-scm.com/docs/git-reset (Last accessed: 2026-01-26)
