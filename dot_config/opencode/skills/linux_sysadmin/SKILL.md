---
name: linux_sysadmin
description: Linux admin for safe system ops
---

# Linux Sysadmin

## Purpose
Operational guidance for managing Linux systems, services, resources safely.

## Core Principles
1. Least-privilege changes, reversible steps
2. Validate state before & after changes
3. Doc commands & rationale for traceability

## Rules

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

See `COMMON.md`.

Refs: [systemctl](https://man7.org/linux/man-pages/man1/systemctl.1.html), [systemd.service](https://man7.org/linux/man-pages/man5/systemd.service.5.html), [systemd](https://man7.org/linux/man-pages/man1/systemd.1.html) (2026-01-26)
