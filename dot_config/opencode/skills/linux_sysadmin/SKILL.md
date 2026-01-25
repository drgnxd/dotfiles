---
name: linux_sysadmin
description: Linux administration guidance for safe system operations
---

# Linux Sysadmin

## Purpose

Provide operational guidance for managing Linux systems, services, and resources safely.

## Core Principles

1. Prefer least-privilege changes and reversible steps.
2. Validate system state before and after changes.
3. Document commands and rationale for traceability.

## Rules/Standards

### System Changes

- Check current state (processes, disk, memory) before modifications.
- Use targeted commands instead of broad changes.
- Capture config backups before edits.

### Services

- Verify service status after reloads or restarts.
- Use logs to confirm behavior and detect regressions.

### Resource Management

- Monitor disk usage, memory pressure, and CPU load.
- Set limits for long-running processes when appropriate.

## Examples

Good:
- "Check service status and logs after a restart."

Bad:
- "Restart all services without validating impact."

## Edge Cases

- For production systems, schedule changes during maintenance windows.
- For emergency fixes, record all actions for post-incident review.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://man7.org/linux/man-pages/man1/systemctl.1.html (Last accessed: 2026-01-26)
- https://man7.org/linux/man-pages/man5/systemd.service.5.html (Last accessed: 2026-01-26)
- https://man7.org/linux/man-pages/man1/systemd.1.html (Last accessed: 2026-01-26)
