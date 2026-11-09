#!/usr/bin/env bash
# shellcheck disable=SC1091
set -euo pipefail

source "$(dirname "$0")/../modules/activation/sync_opencode_managed.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp:?}"' EXIT
export DRY_RUN_CMD=

# Sources come from the store read-only, so replace rather than rewrite them.
set_src() {
  rm -f "$src/managed.ts"
  printf '%s\n' "$1" >"$src/managed.ts"
  chmod 0444 "$src/managed.ts"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

src="$tmp/src"
dest="$tmp/dest"
state="$tmp/state"
mkdir -p "$src" "$dest"
printf '#!/bin/sh\necho tool\n' >"$src/run-tool"
chmod 0555 "$src/run-tool"
printf 'v1\n' >"$src/managed.ts"
chmod 0444 "$src/managed.ts"
: >"$src/.gitkeep"

# First deployment: files copied, exec bit follows the source, dotfiles skipped.
sync_opencode_managed_dir "$src" "$dest" "$state"
[[ "$(<"$dest/managed.ts")" == v1 ]] || fail 'managed file not deployed'
[[ -x "$dest/run-tool" ]] || fail 'executable bit not applied'
[[ ! -x "$dest/managed.ts" ]] || fail 'plain file became executable'
[[ -w "$dest/managed.ts" ]] || fail 'deployed file is not writable'
[[ ! -e "$dest/.gitkeep" ]] || fail 'placeholder was synced'
[[ -z "$(find "$dest" \( -name '*before-nix*' -o -name '.*.tmp.*' \))" ]] || fail 'unexpected backup or temp file'

# Unmanaged files survive and a template update replaces the managed file silently.
printf 'mine\n' >"$dest/custom.ts"
set_src v2
sync_opencode_managed_dir "$src" "$dest" "$state"
[[ "$(<"$dest/managed.ts")" == v2 ]] || fail 'template update not applied'
[[ "$(<"$dest/custom.ts")" == mine ]] || fail 'unmanaged file changed'
[[ -z "$(find "$dest" -name '*before-nix*')" ]] || fail 'update of an unedited file made a backup'

# Every hand edit is backed up, not only the first one.
for round in 1 2; do
  printf 'edit %s\n' "$round" >"$dest/managed.ts"
  set_src "v3-$round"
  sleep 1
  sync_opencode_managed_dir "$src" "$dest" "$state" 2>/dev/null
  [[ "$(<"$dest/managed.ts")" == "v3-$round" ]] || fail "round $round not replaced"
done
[[ "$(find "$dest" -name 'managed.ts.before-nix.*' | wc -l | tr -d ' ')" == 2 ]] || fail 'hand edits were not all backed up'
grep -qx 'edit 2' "$dest"/managed.ts.before-nix.* || fail 'second hand edit lost'

# Backups and temp files never end in .ts/.js, so OpenCode does not load them.
if find "$dest" -name '*before-nix*' -name '*.[tj]s' | grep -q .; then fail 'backup name is loadable'; fi

# A destination with the right content but a lost exec bit is repaired.
chmod 0600 "$dest/run-tool"
sync_opencode_managed_dir "$src" "$dest" "$state"
[[ -x "$dest/run-tool" ]] || fail 'lost exec bit was not repaired'

# Unchanged input does nothing.
before="$(_oc_sha "$dest/managed.ts")"
sync_opencode_managed_dir "$src" "$dest" "$state"
[[ "$(_oc_sha "$dest/managed.ts")" == "$before" ]] || fail 'idempotent run changed a file'

# Dry run changes nothing.
set_src v4
DRY_RUN_CMD="echo" sync_opencode_managed_dir "$src" "$dest" "$state" 2>/dev/null
[[ "$(<"$dest/managed.ts")" == "v3-2" ]] || fail 'dry run modified a file'
[[ -z "$(find "$dest" -name '.*.tmp.*' | head -1)" ]] || fail 'dry run left a temp file'

# A symlinked destination file is skipped and its target is untouched.
printf 'external\n' >"$tmp/external"
rm "$dest/managed.ts"
ln -s "$tmp/external" "$dest/managed.ts"
sync_opencode_managed_dir "$src" "$dest" "$state" 2>/dev/null
[[ -L "$dest/managed.ts" ]] || fail 'symlink was replaced'
[[ "$(<"$tmp/external")" == external ]] || fail 'symlink target was written'
rm "$dest/managed.ts"

# A directory symlink is followed for plugins but refused when a real directory is required.
mkdir -p "$tmp/linked-target"
ln -s "$tmp/linked-target" "$tmp/linked"
sync_opencode_managed_dir "$src" "$tmp/linked" "$state/linked"
[[ -f "$tmp/linked-target/managed.ts" ]] || fail 'directory symlink was not followed'
ln -s "$tmp/linked-target" "$tmp/linked-real"
rm -f "$tmp/linked-target/managed.ts" "$tmp/linked-target/run-tool"
sync_opencode_managed_dir "$src" "$tmp/linked-real" "$state/linked-real" real 2>/dev/null
[[ ! -e "$tmp/linked-target/managed.ts" ]] || fail 'real-directory requirement was ignored'

# A non-directory symlink as the destination is refused.
printf 'not a directory\n' >"$tmp/not-a-directory"
ln -s "$tmp/not-a-directory" "$tmp/file-link"
sync_opencode_managed_dir "$src" "$tmp/file-link" "$state/file-link" 2>/dev/null
[[ -L "$tmp/file-link" && "$(<"$tmp/not-a-directory")" == 'not a directory' ]] || fail 'non-directory symlink was modified'

# Retirement moves a file aside only while it has the deployed content.
printf 'old tool\n' >"$dest/old.ts"
sha="$(_oc_sha "$dest/old.ts")"
retire_opencode_managed_file "$dest" old.ts "$sha"
[[ ! -e "$dest/old.ts" ]] || fail 'matching retired file was not moved'
[[ -n "$(find "$dest" -name 'old.ts.retired.*')" ]] || fail 'retired file was deleted instead of moved'
printf 'user rewrote it\n' >"$dest/old.ts"
retire_opencode_managed_file "$dest" old.ts "$sha" 2>/dev/null
[[ "$(<"$dest/old.ts")" == 'user rewrote it' ]] || fail 'modified retired file was moved'

printf 'ok\n'
