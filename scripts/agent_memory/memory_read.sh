#!/usr/bin/env bash
set -euo pipefail

memory_dir="${AGENT_MEMORY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-memory}"
memory_file="${AGENT_MEMORY_FILE:-$memory_dir/memory.md}"
maintenance_file="$memory_dir/.last-maintained"
maintenance_days="${AGENT_MEMORY_MAINTENANCE_DAYS:-30}"
maintenance_min_facts="${AGENT_MEMORY_MAINTENANCE_MIN_FACTS:-25}"

if [ ! -f "$memory_file" ]; then
  exit 0
fi

maintenance_due() {
  local fact_count maintenance_epoch now_epoch

  if [[ ! $maintenance_days =~ ^[0-9]+$ || ! $maintenance_min_facts =~ ^[0-9]+$ ]]; then
    printf 'WARN: memory maintenance settings must be non-negative integers\n' >&2
    return 1
  fi

  fact_count="$(grep -c '^- ' "$memory_file" || true)"
  if ((fact_count < maintenance_min_facts)); then
    return 1
  fi

  if [ ! -f "$maintenance_file" ]; then
    return 0
  fi

  maintenance_epoch=""
  IFS= read -r maintenance_epoch <"$maintenance_file" || true
  if [[ ! $maintenance_epoch =~ ^[0-9]+$ ]]; then
    printf 'WARN: invalid last memory maintenance time\n' >&2
    return 0
  fi

  now_epoch="$(date +%s)"
  ((now_epoch - maintenance_epoch >= maintenance_days * 86400))
}

memory_generation() {
  local digest _

  if command -v sha256sum >/dev/null 2>&1; then
    read -r digest _ < <(sha256sum "$memory_file")
  elif command -v shasum >/dev/null 2>&1; then
    read -r digest _ < <(shasum -a 256 "$memory_file")
  else
    printf 'ERROR: SHA-256 command is unavailable\n' >&2
    return 69
  fi

  printf '%s\n' "$digest"
}

generation_before="$(memory_generation)"
while IFS= read -r line || [ -n "$line" ]; do
  printf '%s\n' "$line"
done <"$memory_file"
generation_after="$(memory_generation)"

if [ "$generation_before" != "$generation_after" ]; then
  printf 'NOTICE: memory changed while it was being read; run memory-read again.\n' >&2
elif maintenance_due; then
  printf 'NOTICE: memory maintenance is due; compact these facts with memory-maintain.\n' >&2
  printf 'GENERATION: %s\n' "$generation_after" >&2
fi
