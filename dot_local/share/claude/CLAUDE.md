# Claude Code Global Instructions

Before working, read and follow the OpenCode global rules:

@~/.config/opencode/AGENTS.md

Then read and follow every applicable project `AGENTS.md`, starting at the repository root and continuing through the target directory. More specific project rules take precedence where they do not conflict with the global rules.

For projects without a `.claude/skills/` mirror, load skills manually when a task matches:

- Project skills: `.opencode/skills/<skill>/SKILL.md`

Do not load unrelated skills.
