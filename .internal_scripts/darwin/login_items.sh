#!/bin/bash
set -euo pipefail

SOURCE_ROOT="${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${SOURCE_ROOT}/.internal_scripts/lib/bootstrap.sh"

# Check guard flag
require_flag "ALLOW_GUI" "login items modification"

# Verify osascript is available
if ! check_command osascript; then
	log_error "osascript command not found (required for managing login items)"
	log_info "This command is part of macOS and should be available by default"
	exit 1
fi

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
