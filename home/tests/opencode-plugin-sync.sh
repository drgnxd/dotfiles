#!/usr/bin/env bash
set -euo pipefail

source_file="$(dirname "$0")/../modules/activation/opencode.nix"
sync_block="$(awk '/home\.activation\.syncOpencodePlugins =/{copy=1} copy{print} copy && /^  '\'';/{exit}' "$source_file")"

case "$sync_block" in
*"cp -fL \"\$src_file\" \"\$dest_file\""*) ;;
*) exit 1 ;;
esac
case "$sync_block" in
*"rm -f \"\$dest_file\""*) exit 1 ;;
esac

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/template" "$tmp/plugins"
printf 'managed update\n' >"$tmp/template/managed.ts"
printf 'old managed\n' >"$tmp/plugins/managed.ts"
printf 'user plugin\n' >"$tmp/plugins/custom.ts"

for src_file in "$tmp/template"/*; do
  base="$(basename "$src_file")"
  dest_file="$tmp/plugins/$base"
  if [[ -f $dest_file ]] && diff -q "$src_file" "$dest_file" >/dev/null; then
    continue
  fi
  cp -f "$src_file" "$dest_file"
done

[[ "$(<"$tmp/plugins/managed.ts")" == 'managed update' ]]
[[ "$(<"$tmp/plugins/custom.ts")" == 'user plugin' ]]
