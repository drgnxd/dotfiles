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
if ! command -v osascript >/dev/null 2>&1; then
	record_failure "osascript command not found"
	report_failures
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
		record_failure "Ensure login item: $app"
		continue
	fi

	log_success "Ensured $app is in login items"
done

report_failures
