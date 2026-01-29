---
name: safety_protocol
description: Safety rules for destructive commands & changes
---

# Safety Protocol

Aim:
Consistent safety checklist before destructive commands/actions.

Core:
1. Prevent accidental data loss via explicit warnings
2. Make impact transparent, reversible when possible
3. Require explicit confirmation before destructive steps

Do:

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

Refs: See doc/refs.md
