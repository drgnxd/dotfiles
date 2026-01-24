#!/bin/bash
set -euo pipefail

# ぼかし設定ファイルのパス
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/alacritty"
CONFIG="${CONFIG_DIR}/blur.toml"

write_config() {
    local enabled="$1"
    mkdir -p "$CONFIG_DIR"
    printf "[window]\nblur = %s\n" "$enabled" > "$CONFIG"
}

# ファイルが存在しない場合は初期作成
if [ ! -f "$CONFIG" ]; then
    write_config "true"
    exit 0
fi

# 現在の設定を確認して反転
if grep -q "blur = true" "$CONFIG"; then
    write_config "false"
else
    write_config "true"
fi
