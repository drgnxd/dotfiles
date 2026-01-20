#!/bin/bash
# ぼかし設定ファイルのパス
CONFIG="$HOME/.config/alacritty/blur.toml"

# ファイルが存在しない場合は初期作成
if [ ! -f "$CONFIG" ]; then
    echo -e "[window]\nblur = true" > "$CONFIG"
    exit 0
fi

# 現在の設定を確認して反転
if grep -q "blur = true" "$CONFIG"; then
    echo -e "[window]\nblur = false" > "$CONFIG"
else
    echo -e "[window]\nblur = true" > "$CONFIG"
fi
