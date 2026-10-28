# Claude Code Global Instructions

Use the configured `agent-inbox` MCP `ask_user` tool for agent-generated questions that need a user response, and never store conversation transcripts.

@~/.config/opencode/AGENTS.md

Load applicable project `AGENTS.md` files from repository root through the target directory; more specific rules take precedence. For projects without a `.claude/skills` mirror, load only matching `.opencode/skills/<skill>/SKILL.md` files.
