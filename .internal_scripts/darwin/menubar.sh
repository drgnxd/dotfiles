#!/bin/bash
set -euo pipefail

SOURCE_ROOT="${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${SOURCE_ROOT}/.internal_scripts/lib/bootstrap.sh"

log_info "Setting up Menu Bar and Control Center preferences..."

apply_defaults() {
	local label=$1
	shift
	safe_defaults_write "$@" || record_failure "$label"
}

apply_defaults_current_host() {
	local label=$1
	shift
	safe_defaults_write_current_host "$@" || record_failure "$label"
}

configure_control_center() {
	###############################################################################
	# Control Center & Menu Bar Items                                             #
	###############################################################################

	# Battery
	apply_defaults "Hide Battery menu bar item" com.apple.controlcenter "NSStatusItem Visible Battery" -bool false

	# Control Center (BentoBox)
	apply_defaults "Show Control Center" com.apple.controlcenter "NSStatusItem Visible BentoBox" -bool true

	# Set physical spacing between menu bar icons to 10px
	apply_defaults_current_host "Set currentHost NSStatusItemSpacing" -globalDomain NSStatusItemSpacing -int 10
	apply_defaults "Set NSStatusItemSpacing" -globalDomain NSStatusItemSpacing -int 10

	# Set padding around icons to 6px (makes the button itself smaller)
	apply_defaults_current_host "Set currentHost NSStatusItemSelectionPadding" -globalDomain NSStatusItemSelectionPadding -int 6
	apply_defaults "Set NSStatusItemSelectionPadding" -globalDomain NSStatusItemSelectionPadding -int 6

	# Now Playing
	apply_defaults "Hide Now Playing" com.apple.controlcenter "NSStatusItem Visible NowPlaying" -bool false

	# Screen Mirroring
	apply_defaults "Hide Screen Mirroring" com.apple.controlcenter "NSStatusItem Visible ScreenMirroring" -bool false

	# WiFi
	apply_defaults "Hide WiFi menu bar item" com.apple.controlcenter "NSStatusItem Visible WiFi" -bool false
}

configure_clock() {
	###############################################################################
	# Clock                                                                       #
	###############################################################################

	apply_defaults "Use digital clock" com.apple.menuextra.clock IsAnalog -bool false
	apply_defaults "Show AM/PM in clock" com.apple.menuextra.clock ShowAMPM -bool true
	apply_defaults "Show date in clock" com.apple.menuextra.clock ShowDate -bool true
	apply_defaults "Show day of week in clock" com.apple.menuextra.clock ShowDayOfWeek -bool true
	apply_defaults "Show seconds in clock" com.apple.menuextra.clock ShowSeconds -bool true
}

# Main execution
configure_control_center
configure_clock

# Apply changes (SystemUIServer handles the menu bar clock, Control Center handles the rest)
if ! kill_process "SystemUIServer"; then
	record_failure "Restart SystemUIServer"
fi
if ! kill_process "ControlCenter"; then
	record_failure "Restart ControlCenter"
fi

report_failures
