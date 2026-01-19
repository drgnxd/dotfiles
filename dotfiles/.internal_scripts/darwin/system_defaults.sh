#!/bin/bash

set -euo pipefail

if [ "${ALLOW_DEFAULTS:-0}" != "1" ]; then
  echo "Refusing to change macOS defaults without ALLOW_DEFAULTS=1. Set ALLOW_DEFAULTS=1 to proceed." >&2
  exit 1
fi

echo "Setting macOS defaults..."

if command -v osascript >/dev/null 2>&1; then
  osascript -e 'tell application "System Preferences" to quit' || true
fi

###############################################################################
# General UI/UX                                                               #
###############################################################################

# Always show expanded save dialog
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true

# Always show expanded print dialog
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true

# Disable the “Are you sure you want to open this application?” dialog (opt-in)
if [ "${ALLOW_LSQUARANTINE_OFF:-0}" = "1" ]; then
  defaults write com.apple.LaunchServices LSQuarantine -bool false
else
  echo "Skipping LSQuarantine disable (set ALLOW_LSQUARANTINE_OFF=1 to apply)."
fi

# Disable Spotlight keyboard shortcuts (opt-in; affects global UX)
if [ "${ALLOW_SPOTLIGHT_DISABLE:-0}" = "1" ]; then
  defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 64 '<dict><key>enabled</key><false/></dict>'
  defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 65 '<dict><key>enabled</key><false/></dict>'
else
  echo "Skipping Spotlight hotkey disable (set ALLOW_SPOTLIGHT_DISABLE=1 to apply)."
fi

###############################################################################
# Trackpad, mouse, keyboard, Bluetooth accessories, and input                 #
###############################################################################

# Enable tap to click
defaults write com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking -bool true
defaults -currentHost write NSGlobalDomain com.apple.mouse.tapBehavior -int 1
defaults write NSGlobalDomain com.apple.mouse.tapBehavior -int 1

# Fastest key repeat
defaults write NSGlobalDomain KeyRepeat -int 1
defaults write NSGlobalDomain InitialKeyRepeat -int 10

# Remap Caps Lock to Control (hidutil required)
if command -v hidutil >/dev/null 2>&1; then
  /usr/bin/hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000039,"HIDKeyboardModifierMappingDst":0x7000000E0}]}' || true
else
  echo "hidutil not found; skipping Caps Lock remap." >&2
fi

# Set trackpad/mouse/trackpad tracking speed to fastest (0-7, 7 is fastest)
defaults write -g com.apple.mouse.scaling -int 7
defaults write -g com.apple.trackpad.scaling -int 7

###############################################################################
# Finder                                                                      #
###############################################################################

# Always show all extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Show status bar
defaults write com.apple.finder ShowStatusBar -bool true

# Show path bar
defaults write com.apple.finder ShowPathbar -bool true

# Keep folders on top when sorting by name
defaults write com.apple.finder _FXSortFoldersFirst -bool true

# Search current folder by default
defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"

# Avoid creating .DS_Store files on USB and network storage
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

###############################################################################
# Dock, Dashboard, and hot corners                                            #
###############################################################################

# Automatically hide and show the Dock
defaults write com.apple.dock autohide -bool true

# Don't show recent applications in Dock
defaults write com.apple.dock show-recents -bool false

# Set Dock icon size (pixels)
defaults write com.apple.dock tilesize -int 48

###############################################################################
# Screenshots                                                                 #
###############################################################################

# Disable shadow in screenshots
defaults write com.apple.screencapture disable-shadow -bool true

###############################################################################
# Kill affected applications                                                  #
###############################################################################

for app in "Dock" "Finder" "SystemUIServer"; do
  killall "${app}" > /dev/null 2>&1 || true
 done

echo "macOS defaults set successfully."
