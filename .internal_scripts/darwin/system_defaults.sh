#!/bin/bash
set -euo pipefail

SOURCE_ROOT="${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${SOURCE_ROOT}/.internal_scripts/lib/bootstrap.sh"

# Check guard flag
require_flag "ALLOW_DEFAULTS" "macOS defaults modification"

log_info "Setting macOS defaults..."

# Quit System Preferences to prevent conflicts
quit_app "System Preferences"

apply_defaults() {
	local label=$1
	shift
	safe_defaults_write "$@" || record_failure "$label"
}

configure_general_ui_ux() {
	###############################################################################
	# General UI/UX                                                               #
	###############################################################################

	# Always show expanded save dialog
	apply_defaults "Expand save dialog (NSNavPanelExpandedStateForSaveMode)" NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
	apply_defaults "Expand save dialog (NSNavPanelExpandedStateForSaveMode2)" NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

	# Always show expanded print dialog
	apply_defaults "Expand print dialog (PMPrintingExpandedStateForPrint)" NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
	apply_defaults "Expand print dialog (PMPrintingExpandedStateForPrint2)" NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

	# Language and region (English UI, Japan region)
	apply_defaults "Set AppleLanguages" NSGlobalDomain AppleLanguages -array "en-JP" "ja-JP"
	apply_defaults "Set AppleLocale" NSGlobalDomain AppleLocale -string "en_JP"
	apply_defaults "Set AppleMeasurementUnits" NSGlobalDomain AppleMeasurementUnits -string "Centimeters"
	apply_defaults "Set AppleMetricUnits" NSGlobalDomain AppleMetricUnits -bool true
	apply_defaults "Set AppleTemperatureUnit" NSGlobalDomain AppleTemperatureUnit -string "Celsius"

	# Date format (short): yyyy/MM/dd
	apply_defaults "Set AppleICUDateFormatStrings" NSGlobalDomain AppleICUDateFormatStrings -dict-add 1 "yyyy/MM/dd"

	# Disable the "Are you sure you want to open this application?" dialog (opt-in)
	if [ "${ALLOW_LSQUARANTINE_OFF:-0}" = "1" ]; then
		apply_defaults "Disable LSQuarantine" com.apple.LaunchServices LSQuarantine -bool false
	else
		log_info "Skipping LSQuarantine disable (set ALLOW_LSQUARANTINE_OFF=1 to apply)."
	fi

	# Disable Spotlight keyboard shortcuts (opt-in; affects global UX)
	if [ "${ALLOW_SPOTLIGHT_DISABLE:-0}" = "1" ]; then
		apply_defaults "Disable Spotlight hotkey 64" com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 '<dict><key>enabled</key><false/></dict>'
		apply_defaults "Disable Spotlight hotkey 65" com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 65 '<dict><key>enabled</key><false/></dict>'
	else
		log_info "Skipping Spotlight hotkey disable (set ALLOW_SPOTLIGHT_DISABLE=1 to apply)."
	fi

	# Disable smart text substitutions (developer-friendly)
	apply_defaults "Disable automatic spelling correction" NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
	apply_defaults "Disable automatic capitalization" NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
	apply_defaults "Disable automatic quote substitution" NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
	apply_defaults "Disable automatic dash substitution" NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
	apply_defaults "Disable automatic period substitution" NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
}

configure_input_devices() {
	###############################################################################
	# Trackpad, mouse, keyboard, Bluetooth accessories, and input                 #
	###############################################################################

	# Note: Keyboard settings are managed by keyboard.sh script

	# Enable tap to click
	apply_defaults "Set mouse scaling" -g com.apple.mouse.scaling -int 7
	apply_defaults "Set trackpad scaling" -g com.apple.trackpad.scaling -int 7
}

configure_finder() {
	###############################################################################
	# Finder                                                                      #
	###############################################################################

	# Always show all extensions
	apply_defaults "Show all filename extensions" NSGlobalDomain AppleShowAllExtensions -bool true

	# Show hidden files in Finder
	apply_defaults "Show hidden files in Finder" com.apple.finder AppleShowAllFiles -bool true

	# Show POSIX path in Finder title bar
	apply_defaults "Show POSIX path in Finder title" com.apple.finder _FXShowPosixPathInTitle -bool true

	# Show status bar
	apply_defaults "Show Finder status bar" com.apple.finder ShowStatusBar -bool true

	# Show path bar
	apply_defaults "Show Finder path bar" com.apple.finder ShowPathbar -bool true

	# Keep folders on top when sorting by name
	apply_defaults "Sort folders first in Finder" com.apple.finder _FXSortFoldersFirst -bool true

	# Search current folder by default
	apply_defaults "Set Finder search scope to current folder" com.apple.finder FXDefaultSearchScope -string "SCcf"

	# Avoid creating .DS_Store files on USB and network storage
	apply_defaults "Avoid .DS_Store on network volumes" com.apple.desktopservices DSDontWriteNetworkStores -bool true
	apply_defaults "Avoid .DS_Store on USB volumes" com.apple.desktopservices DSDontWriteUSBStores -bool true
}

configure_dock() {
	###############################################################################
	# Dock, Dashboard, and hot corners                                            #
	###############################################################################

	# Automatically hide and show the Dock
	apply_defaults "Auto-hide Dock" com.apple.dock autohide -bool true

	# Remove Dock autohide delay and animation
	apply_defaults "Remove Dock autohide delay" com.apple.dock autohide-delay -float 0
	apply_defaults "Remove Dock autohide animation" com.apple.dock autohide-time-modifier -float 0

	# Disable Spaces animation
	apply_defaults "Disable Spaces animation" com.apple.dock workspaces-swoosh-animation-off -bool true

	# Don't show recent applications in Dock
	apply_defaults "Disable recent apps in Dock" com.apple.dock show-recents -bool false

	# Show only running applications in Dock
	apply_defaults "Show running apps only in Dock" com.apple.dock static-only -bool true

	# Set Dock icon size (pixels)
	apply_defaults "Set Dock icon size" com.apple.dock tilesize -int 48
}

configure_screenshots() {
	###############################################################################
	# Screenshots                                                                 #
	###############################################################################

	# Disable shadow in screenshots
	apply_defaults "Disable screenshot shadow" com.apple.screencapture disable-shadow -bool true

	# Save screenshots as PNG
	apply_defaults "Set screenshot type to PNG" com.apple.screencapture type -string "png"

	# Save screenshots to a dedicated folder (do NOT create it automatically)
	SCREENSHOT_DIR="$HOME/Desktop/Screenshots"
	if [ -d "$SCREENSHOT_DIR" ]; then
		apply_defaults "Set screenshot location" com.apple.screencapture location -string "$SCREENSHOT_DIR"
	else
		log_warning "Screenshot directory does not exist: $SCREENSHOT_DIR — skipping 'com.apple.screencapture location' (will not create it)"
		log_info "Create the directory manually and run: defaults write com.apple.screencapture location -string \"$SCREENSHOT_DIR\"; killall SystemUIServer"
	fi
}

# Main execution - call configuration functions in order
configure_general_ui_ux
configure_input_devices
configure_finder
configure_dock
configure_screenshots

###############################################################################
# Kill affected applications                                                  #
###############################################################################

for app in "Dock" "Finder" "SystemUIServer"; do
	kill_process "${app}" || record_failure "Restart ${app}"
done

report_failures
