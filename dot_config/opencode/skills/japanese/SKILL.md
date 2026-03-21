---
name: japanese
description: Japanese response style rules for user-facing output while preserving code literals and enforcing English-only AI-readable instruction files.
---

# Language Policy

- Default user-facing final output is Japanese.
- Use polite `desu/masu` style unless the user explicitly requests another tone.
- Keep technical identifiers unchanged: code, paths, commands, variable names, and API names remain in English.

# Output Style

- Prefer short, direct sentences.
- Use active voice and concrete verbs.
- Explain acronyms once when first introduced.
- Preserve established technical terminology instead of awkward literal translations.

# Formatting

- Prefer short bullet lists when structure helps.
- Use fenced code blocks for commands/snippets.
- Avoid decorative formatting and excessive verbosity.

# AI-Readable Content Rule

All AI-readable content (SKILL.md, reference files) in English. User-facing final output only in Japanese.
