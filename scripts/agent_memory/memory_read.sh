#!/usr/bin/env bash
set -euo pipefail

memory_dir="${AGENT_MEMORY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-memory}"
memory_file="${AGENT_MEMORY_FILE:-$memory_dir/memory.md}"

if [ ! -f "$memory_file" ]; then
  exit 0
fi

while IFS= read -r line || [ -n "$line" ]; do
  printf '%s\n' "$line"
done <"$memory_file"
