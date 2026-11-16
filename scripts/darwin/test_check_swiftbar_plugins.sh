#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

export XDG_DATA_HOME="$tmp_dir/data" XDG_CONFIG_HOME="$tmp_dir/config"
bin_dir="$XDG_DATA_HOME/swiftbar-plugins/bin"
plugin_dir="$XDG_CONFIG_HOME/swiftbar/plugins"
mkdir -p "$bin_dir" "$plugin_dir"

run_check() { bash "$SCRIPT_DIR/check_swiftbar_plugins.sh" >/dev/null 2>&1; }

if run_check; then
  printf 'expected missing binaries to fail\n' >&2
  exit 1
fi

for plugin in caffeine.5s.bin attention.1m.bin; do
  : >"$bin_dir/$plugin"
  ln -s "$bin_dir/$plugin" "$plugin_dir/$plugin"
done
if run_check; then
  printf 'expected non-executable binaries to fail\n' >&2
  exit 1
fi

chmod +x "$bin_dir"/*.bin
run_check

rm "$bin_dir/attention.1m.bin"
if run_check; then
  printf 'expected dangling link to fail\n' >&2
  exit 1
fi
printf 'OK\n'
