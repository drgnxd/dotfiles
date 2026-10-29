#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$repo_root/home/modules/activation/sync_opencode_tools.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

src="$tmp/src"
dest="$tmp/dest"
mkdir -p "$src" "$dest"
printf 'managed v1\n' >"$src/managed.sh"
printf 'user data\n' >"$dest/unmanaged.sh"
sync_opencode_tools "$src" "$dest"
[ "$(cat "$dest/unmanaged.sh")" = 'user data' ] || fail 'unmanaged destination file was changed or removed'
[ "$(cat "$dest/managed.sh")" = 'managed v1' ] || fail 'managed file was not copied'

printf 'managed v2\n' >"$src/managed.sh"
sync_opencode_tools "$src" "$dest"
[ "$(cat "$dest/managed.sh")" = 'managed v2' ] || fail 'managed file was not updated'

mkdir -p "$tmp/dir-target"
printf 'user target\n' >"$tmp/dir-target/user.sh"
ln -s "$tmp/dir-target" "$tmp/tools-link"
if sync_opencode_tools "$src" "$tmp/tools-link" 2>"$tmp/dir-error"; then
  fail 'directory symlink was accepted'
fi
[ -L "$tmp/tools-link" ] || fail 'directory symlink was replaced'
[ "$(cat "$tmp/dir-target/user.sh")" = 'user target' ] || fail 'directory symlink target changed'
grep -q 'directory symlink' "$tmp/dir-error" || fail 'directory symlink refusal lacked diagnostic'

printf 'symlink target\n' >"$tmp/file-target"
rm "$dest/managed.sh"
ln -s "$tmp/file-target" "$dest/managed.sh"
if sync_opencode_tools "$src" "$dest" 2>"$tmp/file-error"; then
  fail 'file symlink was accepted'
fi
[ -L "$dest/managed.sh" ] || fail 'file symlink was replaced'
[ "$(cat "$tmp/file-target")" = 'symlink target' ] || fail 'file symlink target changed'
grep -q 'file symlink' "$tmp/file-error" || fail 'file symlink refusal lacked diagnostic'

printf 'OpenCode tool sync tests passed\n'
