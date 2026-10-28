# Claude Code Global Instructions

Use the configured `agent-inbox` MCP `ask_user` tool for agent-generated questions that need a user response, and never store conversation transcripts.

## Local MCP Setup

The user-scope inbox MCP entry is registered manually to avoid racing a live Claude Code writer.
After the Rust binary has been built into the configured cache and all Claude Code clients are stopped, the user may register it with:

```sh
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
python3 -I "$data_home/claude/agent_inbox_config.py" \
  "$data_home/claude/.claude.json" \
  "$HOME/.claude.json" \
  "$(command -v agent-inbox)"
```

@~/.config/opencode/AGENTS.md

Load applicable project `AGENTS.md` files from repository root through the target directory; more specific rules take precedence. For projects without a `.claude/skills` mirror, load only matching `.opencode/skills/<skill>/SKILL.md` files.
