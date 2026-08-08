#!/usr/bin/env sh

set -eu

managed_marker="# managed by nix-config"
git rev-parse --show-toplevel >/dev/null
hook_path="$(git rev-parse --git-path hooks/commit-msg)"
hook_dir="$(dirname "$hook_path")"

if [ -e "$hook_path" ] && ! grep -Fqx "$managed_marker" "$hook_path"; then
  printf '%s\n' "refusing to replace unmanaged commit-msg hook: $hook_path" >&2
  exit 1
fi

mkdir -p "$hook_dir"
temporary_hook="$(mktemp "$hook_dir/.commit-msg.XXXXXX")"
trap 'rm -f "$temporary_hook"' EXIT HUP INT TERM

# shellcheck disable=SC2016
printf '%s\n' \
  '#!/usr/bin/env sh' \
  "$managed_marker" \
  'set -eu' \
  'repo_root="$(git rev-parse --show-toplevel)"' \
  'exec sh "$repo_root/scripts/validate_commit_message.sh" "$@"' >"$temporary_hook"

chmod +x "$temporary_hook"
mv -f "$temporary_hook" "$hook_path"
