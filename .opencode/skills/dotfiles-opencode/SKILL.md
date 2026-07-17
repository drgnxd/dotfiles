---
name: dotfiles-opencode
description: Use when changing this repository's OpenCode providers, agents, tools, global deployment, validation, or activation behavior.
---

# Dotfiles OpenCode Maintenance

Edit sources under `dot_config/opencode/`, never deployed files under
`~/.config/opencode/`.

- `global_rules.md` deploys read-only as `~/.config/opencode/AGENTS.md`.
- Native global skills under `dot_config/opencode/skills/*/SKILL.md` deploy
  read-only. Repository-local skills under `.opencode/skills/` do not deploy.
- `opencode.json`, `package.json`, and `tools/` are activation-synced real
  files. Tools must remain real files for Bun module resolution.
- Keep the provider allowlist and agent assignments minimal. Verify availability
  and run a bounded read-only smoke test before changing a model assignment.
- Use `OPENCODE_CONFIG` or `OPENCODE_CONFIG_CONTENT` for experiments. Do not
  edit the deployed configuration directly.
- After configuration, skill, or tool changes, run the repository OpenCode
  validation gate and inspect `opencode debug config`. Apply the Nix
  configuration and restart OpenCode to activate changes.
