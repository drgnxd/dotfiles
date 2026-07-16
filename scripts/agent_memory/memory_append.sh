#!/usr/bin/env bash
set -euo pipefail

memory_dir="${AGENT_MEMORY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-memory}"
memory_file="${AGENT_MEMORY_FILE:-$memory_dir/memory.md}"
memory_file_dir="$(dirname "$memory_file")"

memory_lock_key() {
  local checksum size _

  read -r checksum size _ < <(printf '%s' "$memory_file" | cksum)
  printf '%s-%s\n' "$checksum" "$size"
}

acquire_lock() {
  local lock_file

  if [ "${AGENT_MEMORY_LOCKED:-0}" = 1 ]; then
    return 0
  fi

  lock_file="/tmp/agent-memory-$(id -u)-$(memory_lock_key).lock"
  if [ "$(uname -s)" = Darwin ]; then
    exec /usr/bin/lockf -t 10 "$lock_file" env AGENT_MEMORY_LOCKED=1 "$BASH" "$0" "$@"
  elif command -v flock >/dev/null 2>&1; then
    exec flock -w 10 "$lock_file" env AGENT_MEMORY_LOCKED=1 "$BASH" "$0" "$@"
  fi

  printf 'ERROR: flock is unavailable on this platform\n' >&2
  exit 69
}

usage() {
  printf 'Usage: memory-append <fact>\n' >&2
}

umask 077
mkdir -p "$memory_dir" "$memory_file_dir"
memory_file_dir="$(cd "$memory_file_dir" && pwd -P)"
memory_file="$memory_file_dir/${memory_file##*/}"
acquire_lock "$@"

if [ "$#" -eq 0 ]; then
  if [ -t 0 ]; then
    usage
    exit 64
  fi
  fact="$(</dev/stdin)"
else
  fact="$*"
fi

if [[ -z ${fact//[[:space:]]/} ]]; then
  printf 'ERROR: memory fact must not be empty\n' >&2
  exit 64
fi

if [[ $fact == *$'\n'* || $fact == *$'\r'* ]]; then
  printf 'ERROR: memory fact must be a single line\n' >&2
  exit 64
fi

timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

git_relative_path() {
  local path absolute_path

  path="$1"
  absolute_path="$(cd "$(dirname "$path")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$path")")"
  case "$absolute_path" in
  "$git_root"/*) printf '%s\n' "${absolute_path#"$git_root"/}" ;;
  *) return 1 ;;
  esac
}

touch "$memory_file"
chmod 600 "$memory_file"
printf -- '- %s %s\n' "$timestamp" "$fact" >>"$memory_file"

if command -v git >/dev/null 2>&1 && git -C "$memory_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_root="$(git -C "$memory_dir" rev-parse --show-toplevel)"
  git_root="$(cd "$git_root" && pwd -P)"

  if ! memory_rel="$(git_relative_path "$memory_file")"; then
    printf 'WARN: memory appended, but its file is outside the memory git repository\n' >&2
  elif git -C "$git_root" --literal-pathspecs add -- "$memory_rel" >/dev/null 2>&1; then
    if ! git -C "$git_root" --literal-pathspecs diff --cached --quiet -- "$memory_rel"; then
      git -C "$git_root" --literal-pathspecs -c commit.gpgsign=false commit -m 'memory: append fact' -- "$memory_rel" >/dev/null 2>&1 ||
        printf 'WARN: memory appended, but git commit failed\n' >&2
    fi
  else
    printf 'WARN: memory appended, but git add failed\n' >&2
  fi
fi

printf 'Appended memory fact.\n'
