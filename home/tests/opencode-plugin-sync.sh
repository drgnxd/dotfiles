#!/usr/bin/env bash
# shellcheck source=home/modules/activation/sync_opencode_plugins.sh
set -euo pipefail

source "$(dirname "$0")/../modules/activation/sync_opencode_plugins.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/template" "$tmp/plugins" "$tmp/symlink-target"
printf 'managed update\n' >"$tmp/template/managed.ts"
printf 'old managed\n' >"$tmp/plugins/managed.ts"
printf 'user plugin\n' >"$tmp/plugins/custom.ts"
DRY_RUN_CMD=
sync_opencode_plugins "$tmp/template" "$tmp/plugins"
[[ "$(<"$tmp/plugins/managed.ts")" == 'managed update' ]]
[[ "$(<"$tmp/plugins/custom.ts")" == 'user plugin' ]]

printf 'another managed plugin\n' >"$tmp/template/another.ts"
printf 'user plugin in linked directory\n' >"$tmp/symlink-target/custom.ts"
ln -s "$tmp/symlink-target" "$tmp/plugins-link"
sync_opencode_plugins "$tmp/template" "$tmp/plugins-link"
[[ -L "$tmp/plugins-link" ]]
[[ "$(<"$tmp/symlink-target/custom.ts")" == 'user plugin in linked directory' ]]
[[ "$(<"$tmp/symlink-target/another.ts")" == 'another managed plugin' ]]

printf 'external target bytes\n' >"$tmp/external-target"
rm "$tmp/symlink-target/managed.ts"
ln -s "$tmp/external-target" "$tmp/symlink-target/managed.ts"
before="$(shasum -a 256 "$tmp/external-target")"
if sync_opencode_plugins "$tmp/template" "$tmp/plugins-link"; then
  exit 1
fi
[[ -L "$tmp/symlink-target/managed.ts" ]]
[[ "$(shasum -a 256 "$tmp/external-target")" == "$before" ]]
[[ "$(<"$tmp/external-target")" == 'external target bytes' ]]

printf 'not a directory\n' >"$tmp/not-a-directory"
ln -s "$tmp/not-a-directory" "$tmp/plugins-file-link"
if sync_opencode_plugins "$tmp/template" "$tmp/plugins-file-link"; then
  exit 1
fi
[[ -L "$tmp/plugins-file-link" ]]
