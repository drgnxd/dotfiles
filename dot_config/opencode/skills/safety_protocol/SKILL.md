---
name: safety_protocol
description: Safety rules for destructive commands & changes
---

# Safety Protocol

## Purpose
Consistent safety checklist before destructive commands/actions.

## Core Principles
1. Prevent accidental data loss via explicit warnings
2. Make impact transparent, reversible when possible
3. Require explicit confirmation before destructive steps

## Rules

### Destructive Commands
Treat as destructive: `rm`, `dd`, `mkfs`, `chmod -R`, `> overwrite`, forced git ops.

- Explain what changes, where, why needed
- Ask explicit confirmation before proceeding

### Safer Alternatives
- Prefer non-destructive when feasible (dry-run, backups, move to safe location)
- Offer rollback plan if irreversible

### Scope Control
- Target smallest scope (specific files, explicit paths)
- Avoid wildcard deletes unless user explicitly requires

## Examples

✅ "This permanently deletes `/path/to/data`. Cannot be undone. Move to backup first? Proceed?"
❌ "Running rm -rf now."

## Edge Cases
- Destructive step required for recovery: still ask confirmation, doc recovery plan
- User explicitly requests destructive: confirm scope & intent before executing

See `COMMON.md`.

Refs: [rm](https://man7.org/linux/man-pages/man1/rm.1.html), [dd](https://man7.org/linux/man-pages/man1/dd.1.html), [mkfs](https://man7.org/linux/man-pages/man8/mkfs.8.html), [git-reset](https://git-scm.com/docs/git-reset) (2026-01-26)
