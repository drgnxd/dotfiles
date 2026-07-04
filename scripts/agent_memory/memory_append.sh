#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: memory-append <fact>\n' >&2
}

if [ "$#" -eq 0 ]; then
  if [ -t 0 ]; then
    usage
    exit 64
  fi
  fact="$(</dev/stdin)"
else
  fact="$*"
fi

if [[ -z "${fact//[[:space:]]/}" ]]; then
  printf 'ERROR: memory fact must not be empty\n' >&2
  exit 64
fi

if [[ "$fact" == *$'\n'* || "$fact" == *$'\r'* ]]; then
  printf 'ERROR: memory fact must be a single line\n' >&2
  exit 64
fi

memory_dir="${AGENT_MEMORY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-memory}"
memory_file="${AGENT_MEMORY_FILE:-$memory_dir/memory.md}"
timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

umask 077
mkdir -p "$memory_dir"
touch "$memory_file"
chmod 600 "$memory_file"
printf -- '- %s %s\n' "$timestamp" "$fact" >>"$memory_file"

if command -v git >/dev/null 2>&1 && git -C "$memory_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_root="$(git -C "$memory_dir" rev-parse --show-toplevel)"
  git_prefix="$(git -C "$memory_dir" rev-parse --show-prefix)"
  memory_rel="${git_prefix}${memory_file##*/}"

  if git -C "$git_root" add -- "$memory_rel" >/dev/null 2>&1; then
    if ! git -C "$git_root" diff --cached --quiet -- "$memory_rel"; then
      git -C "$git_root" -c commit.gpgsign=false commit -m 'memory: append fact' -- "$memory_rel" >/dev/null 2>&1 || \
        printf 'WARN: memory appended, but git commit failed\n' >&2
    fi
  else
    printf 'WARN: memory appended, but git add failed\n' >&2
  fi
fi

printf 'Appended memory fact.\n'
