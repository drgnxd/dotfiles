---
name: nix
description: Use when editing Nix flakes or deployment workflows.
---

# Nix Preferences

- Prefer flake-native commands and follow the active repository's documented
  evaluation and deployment workflow.
- Use `path:.` only when local evaluation must include untracked or ignored
  files; otherwise preserve the repository's source semantics.
- Resolve configuration attributes dynamically when the repository supports
  multiple users or hosts. Do not invent target names.
