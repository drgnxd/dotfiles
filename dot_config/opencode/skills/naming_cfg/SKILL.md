---
name: naming_cfg
description: Default filename/directory rules (UNIX-Modern Snake Protocol)
---

# Default Naming Conventions

Aim:
- default UNIX-modern snake_case rules when no project rules

Core:
- apply only if no explicit rules; lowercase snake_case; clarity>brevity; approved abbrevs only

Do:
- case: lowercase (exceptions: README.md, SKILL.md); separator: underscores; chars: a-z0-9_.; approved abbrevs: src,lib,doc,cfg,bin,tmp,env,pkg

Edge:
- existing codebase: prefer existing; spec-mandated: keep

Refs: See doc/refs.md
