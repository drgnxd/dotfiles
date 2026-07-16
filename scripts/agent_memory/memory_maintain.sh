#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: memory-maintain <generation> < facts.txt\n' >&2
  printf 'Input must contain one replacement fact per line, without Markdown bullets.\n' >&2
}

if [ "$#" -ne 1 ] || [ -t 0 ]; then
  usage
  exit 64
fi

expected_generation="$1"
memory_dir="${AGENT_MEMORY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/agent-memory}"
memory_file="${AGENT_MEMORY_FILE:-$memory_dir/memory.md}"
memory_file_dir="$(dirname "$memory_file")"
archive_dir="$memory_dir/archive"
maintenance_file="$memory_dir/.last-maintained"
timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
maintenance_epoch="$(date +%s)"
archive_stamp="$(date -u '+%Y-%m-%dT%H-%M-%SZ')"
temp_file=""
maintenance_temp_file=""

cleanup() {
  if [ -n "$temp_file" ] && [ -f "$temp_file" ]; then
    rm -f "$temp_file"
  fi
  if [ -n "$maintenance_temp_file" ] && [ -f "$maintenance_temp_file" ]; then
    rm -f "$maintenance_temp_file"
  fi
}

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

git_relative_path() {
  local path absolute_path

  path="$1"
  absolute_path="$(cd "$(dirname "$path")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$path")")"
  case "$absolute_path" in
  "$git_root"/*) printf '%s\n' "${absolute_path#"$git_root"/}" ;;
  *) return 1 ;;
  esac
}

commit_changes() {
  local memory_rel maintenance_rel archive_rel
  local -a git_paths

  if ! command -v git >/dev/null 2>&1 ||
    ! git -C "$memory_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 0
  fi

  git_root="$(git -C "$memory_dir" rev-parse --show-toplevel)"
  git_root="$(cd "$git_root" && pwd -P)"
  if ! memory_rel="$(git_relative_path "$memory_file")" ||
    ! maintenance_rel="$(git_relative_path "$maintenance_file")"; then
    printf 'WARN: memory maintained, but its files are outside the memory git repository\n' >&2
    return 0
  fi
  git_paths=("$memory_rel" "$maintenance_rel")

  if [ -n "${archive_file:-}" ]; then
    if ! archive_rel="$(git_relative_path "$archive_file")"; then
      printf 'WARN: memory maintained, but its archive is outside the memory git repository\n' >&2
      return 0
    fi
    git_paths+=("$archive_rel")
  fi

  if git -C "$git_root" --literal-pathspecs add -- "${git_paths[@]}" >/dev/null 2>&1; then
    if ! git -C "$git_root" --literal-pathspecs diff --cached --quiet -- "${git_paths[@]}"; then
      git -C "$git_root" --literal-pathspecs -c commit.gpgsign=false commit -m 'memory: compact facts' -- "${git_paths[@]}" >/dev/null 2>&1 ||
        printf 'WARN: memory maintained, but git commit failed\n' >&2
    fi
  else
    printf 'WARN: memory maintained, but git add failed\n' >&2
  fi
}

umask 077
mkdir -p "$memory_dir" "$memory_file_dir"
memory_file_dir="$(cd "$memory_file_dir" && pwd -P)"
memory_file="$memory_file_dir/${memory_file##*/}"
acquire_lock "$@"
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 129' HUP
trap 'exit 143' TERM
if [ ! -f "$memory_file" ]; then
  printf 'ERROR: memory changed after it was read; run memory-read again\n' >&2
  exit 75
fi
current_generation="$(memory_generation)"
if [ "$current_generation" != "$expected_generation" ]; then
  printf 'ERROR: memory changed after it was read; run memory-read again\n' >&2
  exit 75
fi

temp_file="$(mktemp "$memory_file_dir/.${memory_file##*/}.tmp.XXXXXX")"
fact_count=0

while IFS= read -r fact || [ -n "$fact" ]; do
  if [[ -z ${fact//[[:space:]]/} ]]; then
    continue
  fi
  if [[ $fact == *$'\r'* ]]; then
    printf 'ERROR: replacement facts must not contain carriage returns\n' >&2
    exit 64
  fi
  if [[ $fact =~ ^[[:space:]]*[-+*][[:space:]] || $fact =~ ^[[:space:]]*[0-9]+\.[[:space:]] || $fact =~ ^[[:space:]]*[0-9]+\)[[:space:]] ]]; then
    printf 'ERROR: replacement facts must not include Markdown bullets\n' >&2
    exit 64
  fi

  printf -- '- %s %s\n' "$timestamp" "$fact" >>"$temp_file"
  fact_count=$((fact_count + 1))
done

if ((fact_count == 0)); then
  printf 'ERROR: at least one replacement fact is required\n' >&2
  exit 64
fi

archive_file=""
if [ -s "$memory_file" ]; then
  mkdir -p "$archive_dir"
  archive_file="$(mktemp "$archive_dir/${archive_stamp}.md.XXXXXX")"
  cp "$memory_file" "$archive_file"
  chmod 600 "$archive_file"
fi

chmod 600 "$temp_file"
mv "$temp_file" "$memory_file"
temp_file=""
maintenance_temp_file="$(mktemp "$memory_dir/.last-maintained.tmp.XXXXXX")"
printf '%s\n' "$maintenance_epoch" >"$maintenance_temp_file"
chmod 600 "$maintenance_temp_file"
mv "$maintenance_temp_file" "$maintenance_file"
maintenance_temp_file=""
commit_changes

printf 'Maintained memory with %d facts.\n' "$fact_count"
