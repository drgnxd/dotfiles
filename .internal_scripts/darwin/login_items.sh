#!/bin/bash

# Source common library
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)"
source "${LIB_DIR}/common.sh"

# Check guard flag
require_flag "ALLOW_GUI" "ログイン項目の変更"

log_info "Setting up login items..."

apps=(
    "Alacritty"
    "Floorp"
    "Proton Mail"
    "Proton Pass"
    "ProtonVPN"
    "Sol"
)

for app in "${apps[@]}"; do
    log_info "Processing $app..."

    if [ ! -d "/Applications/${app}.app" ]; then
        log_warning "/Applications/${app}.app not found. Skipping"
        continue
    fi

    if ! osascript -e "tell application \"System Events\" to if not (exists login item \"${app}\") then make login item at end with properties {path:\"/Applications/${app}.app\", hidden:false}"; then
        log_error "Failed to ensure $app login item"
        continue
    fi

    log_success "Ensured $app is in login items"
 done

log_success "Login items setup complete"

