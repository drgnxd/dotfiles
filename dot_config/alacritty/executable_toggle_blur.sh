#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/alacritty"
CONFIG="${CONFIG_DIR}/blur.toml"

write_config() {
	local enabled="$1"
	mkdir -p "$CONFIG_DIR"
	printf "[window]\nblur = %s\n" "$enabled" >"$CONFIG"
}

if [[ ! -f "$CONFIG" ]]; then
	write_config "true"
	exit 0
fi

if grep -q "blur = true" "$CONFIG"; then
	write_config "false"
else
	write_config "true"
fi
