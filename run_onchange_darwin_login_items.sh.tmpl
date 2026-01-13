#!/bin/bash

set -euo pipefail

if [ "${ALLOW_GUI:-0}" != "1" ]; then
    echo "Refusing to modify login items without ALLOW_GUI=1. Set ALLOW_GUI=1 to proceed." >&2
    exit 1
fi

echo "Setting up login items..."

apps=(
    "Alacritty"
    "Floorp"
    "Hammerspoon"
    "Maccy"
    "Proton Mail"
    "Proton Pass"
    "ProtonVPN"
    "Sol"
    "Stats"
)

for app in "${apps[@]}"; do
    echo "Processing $app..."

    if [ ! -d "/Applications/${app}.app" ]; then
        echo "  Warning: /Applications/${app}.app not found. Skipping."
        continue
    fi

    if ! osascript -e "tell application \"System Events\" to if not (exists login item \"${app}\") then make login item at end with properties {path:\"/Applications/${app}.app\", hidden:false}"; then
        echo "  Error: failed to ensure $app login item." >&2
        continue
    fi

    echo "  Ensure $app is in login items."
 done

echo "Login items setup complete."

