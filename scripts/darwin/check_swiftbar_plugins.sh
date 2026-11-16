#!/usr/bin/env bash
set -euo pipefail

# The plugin binaries are built and installed by their own repository; home-manager only links them.
# An out-of-store symlink to a missing target still builds, so this read-only check reports it.
plugins=(caffeine.5s.bin attention.1m.bin)
bin_dir="${XDG_DATA_HOME:-$HOME/.local/share}/swiftbar-plugins/bin"
plugin_dir="${XDG_CONFIG_HOME:-$HOME/.config}/swiftbar/plugins"

errors=0
for plugin in "${plugins[@]}"; do
  if [ ! -e "$bin_dir/$plugin" ]; then
    printf 'ERROR: not installed: %s\n' "$bin_dir/$plugin" >&2
    errors=$((errors + 1))
  elif [ ! -f "$bin_dir/$plugin" ] || [ ! -x "$bin_dir/$plugin" ]; then
    printf 'ERROR: not an executable file: %s\n' "$bin_dir/$plugin" >&2
    errors=$((errors + 1))
  fi
  if [ ! -L "$plugin_dir/$plugin" ] || [ ! -e "$plugin_dir/$plugin" ]; then
    printf 'ERROR: link missing or dangling: %s\n' "$plugin_dir/$plugin" >&2
    errors=$((errors + 1))
  fi
done

if [ "$errors" -gt 0 ]; then
  exit 1
fi
printf 'OK: SwiftBar plugin binaries are installed and linked.\n'
