---
name: default_naming_conventions
description: Default filename/directory rules (UNIX-Modern Snake Protocol)
---

# Default Naming Conventions

Aim:
Manage filenames/directories using UNIX-Modern Snake Protocol when no project rules exist.

Core:
1. Apply only when no explicit naming rules exist
2. Lowercase snake_case for all files/dirs
3. Clarity & searchability > brevity
4. Approved abbreviations & allowed chars only

Do:

### Naming (The Constitution)
- **Case:** lowercase (Exception: `README.md`, `SKILL.md`)
- **Separator:** underscores only; no spaces/hyphens
- **Language:** English
- **Chars:** `a-z`, `0-9`, `_`, `.` only

### Abbreviations
Use only for industry standards:
- Approved: `src`, `lib`, `doc`, `cfg`, `bin`, `tmp`, `env`, `pkg`
- All others: full spelling

### Directory Structure
- Full words for domain-specific dirs (`research`, `templates`)
- Approved abbrevs for conventional dirs (`src`, `doc`, `bin`)

## Examples

✅ `example_pattern.md`, `user_cfg.json`, `biomimetic_robot_research.pdf`, `src/main_logic.c`
❌ `ex_pat.md` (unapproved abbrev), `user-cfg.json` (hyphen), `UserCfg.json` (uppercase), `user cfg.json` (space)

## Edge Cases
- Existing codebase w/ different convention: prefer that
- Spec mandates fixed name: keep mandated name

See `doc/naming_protocol.md` for details.

Refs: See doc/refs.md
