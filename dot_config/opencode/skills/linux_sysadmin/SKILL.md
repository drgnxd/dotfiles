---
name: linux_sysadmin
description: Linux admin for safe system ops
---

# Linux Sysadmin

Aim:
Operational guidance for managing Linux systems, services, resources safely.

Core:
1. Least-privilege changes, reversible steps
2. Validate state before & after changes
3. Doc commands & rationale for traceability

Do:

### System Changes
- Check current state (processes, disk, mem) before mods
- Use targeted commands vs broad changes
- Capture config backups before edits

### Services
- Verify service status after reloads/restarts
- Use logs to confirm behavior, detect regressions

### Resource Management
- Monitor disk usage, mem pressure, CPU load
- Set limits for long-running processes when appropriate

## Examples

✅ "Check service status & logs after restart"
❌ "Restart all services w/o validating impact"

## Edge Cases
- Production systems: schedule changes during maintenance windows
- Emergency fixes: record all actions for post-incident review

Refs: See doc/refs.md
