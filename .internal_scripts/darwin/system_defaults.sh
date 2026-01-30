#!/bin/bash
set -euo pipefail

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/.internal_scripts/lib/bootstrap.sh"

# Check guard flag
require_flag "ALLOW_DEFAULTS" "macOS defaults modification"

log_info "Setting macOS defaults..."

# Quit System Preferences to prevent conflicts
quit_app "System Preferences"

configure_general_ui_ux() {
	###############################################################################
	# General UI/UX                                                               #
	###############################################################################

	# Always show expanded save dialog
	safe_defaults_write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
	safe_defaults_write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

	# Always show expanded print dialog
	safe_defaults_write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
	safe_defaults_write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

	# Language and region (English UI, Japan region)
	safe_defaults_write NSGlobalDomain AppleLanguages -array "en-JP" "ja-JP"
	safe_defaults_write NSGlobalDomain AppleLocale -string "en_JP"
	safe_defaults_write NSGlobalDomain AppleMeasurementUnits -string "Centimeters"
	safe_defaults_write NSGlobalDomain AppleMetricUnits -bool true
	safe_defaults_write NSGlobalDomain AppleTemperatureUnit -string "Celsius"

	# Date format (short): yyyy/MM/dd
	safe_defaults_write NSGlobalDomain AppleICUDateFormatStrings -dict-add 1 "yyyy/MM/dd"

	# Disable the "Are you sure you want to open this application?" dialog (opt-in)
	if [ "${ALLOW_LSQUARANTINE_OFF:-0}" = "1" ]; then
		safe_defaults_write com.apple.LaunchServices LSQuarantine -bool false
	else
		log_info "Skipping LSQuarantine disable (set ALLOW_LSQUARANTINE_OFF=1 to apply)."
	fi

	# Disable Spotlight keyboard shortcuts (opt-in; affects global UX)
	if [ "${ALLOW_SPOTLIGHT_DISABLE:-0}" = "1" ]; then
		safe_defaults_write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 '<dict><key>enabled</key><false/></dict>'
		safe_defaults_write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 65 '<dict><key>enabled</key><false/></dict>'
	else
		log_info "Skipping Spotlight hotkey disable (set ALLOW_SPOTLIGHT_DISABLE=1 to apply)."
	fi

	# Disable smart text substitutions (developer-friendly)
	safe_defaults_write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
	safe_defaults_write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
	safe_defaults_write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
	safe_defaults_write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
	safe_defaults_write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false
}

configure_input_devices() {
	###############################################################################
	# Trackpad, mouse, keyboard, Bluetooth accessories, and input                 #
	###############################################################################

	# Note: Keyboard settings are managed by keyboard.sh script

	# Enable tap to click
	safe_defaults_write -g com.apple.mouse.scaling -int 7
	safe_defaults_write -g com.apple.trackpad.scaling -int 7
}

configure_finder() {
	###############################################################################
	# Finder                                                                      #
	###############################################################################

	# Always show all extensions
	safe_defaults_write NSGlobalDomain AppleShowAllExtensions -bool true

	# Show hidden files in Finder
	safe_defaults_write com.apple.finder AppleShowAllFiles -bool true

	# Show POSIX path in Finder title bar
	safe_defaults_write com.apple.finder _FXShowPosixPathInTitle -bool true

	# Show status bar
	safe_defaults_write com.apple.finder ShowStatusBar -bool true

	# Show path bar
	safe_defaults_write com.apple.finder ShowPathbar -bool true

	# Keep folders on top when sorting by name
	safe_defaults_write com.apple.finder _FXSortFoldersFirst -bool true

	# Search current folder by default
	safe_defaults_write com.apple.finder FXDefaultSearchScope -string "SCcf"

	# Avoid creating .DS_Store files on USB and network storage
	safe_defaults_write com.apple.desktopservices DSDontWriteNetworkStores -bool true
	safe_defaults_write com.apple.desktopservices DSDontWriteUSBStores -bool true
}

configure_dock() {
	###############################################################################
	# Dock, Dashboard, and hot corners                                            #
	###############################################################################

	# Automatically hide and show the Dock
	safe_defaults_write com.apple.dock autohide -bool true

	# Remove Dock autohide delay and animation
	safe_defaults_write com.apple.dock autohide-delay -float 0
	safe_defaults_write com.apple.dock autohide-time-modifier -float 0

	# Disable Spaces animation
	safe_defaults_write com.apple.dock workspaces-swoosh-animation-off -bool true

	# Don't show recent applications in Dock
	safe_defaults_write com.apple.dock show-recents -bool false

	# Show only running applications in Dock
	safe_defaults_write com.apple.dock static-only -bool true

	# Set Dock icon size (pixels)
	safe_defaults_write com.apple.dock tilesize -int 48
}

configure_screenshots() {
	###############################################################################
	# Screenshots                                                                 #
	###############################################################################

	# Disable shadow in screenshots
	safe_defaults_write com.apple.screencapture disable-shadow -bool true

	# Save screenshots as PNG
	safe_defaults_write com.apple.screencapture type -string "png"

	# Save screenshots to a dedicated folder (do NOT create it automatically)
	SCREENSHOT_DIR="$HOME/Desktop/Screenshots"
	if [ -d "$SCREENSHOT_DIR" ]; then
		safe_defaults_write com.apple.screencapture location -string "$SCREENSHOT_DIR"
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
	kill_process "${app}"
done

log_success "macOS defaults set successfully"
