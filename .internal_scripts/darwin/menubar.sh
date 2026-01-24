#!/bin/bash
set -euo pipefail

# Source common library
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)"
source "${LIB_DIR}/common.sh"

log_info "Setting up Menu Bar and Control Center preferences..."

###############################################################################
# Control Center & Menu Bar Items                                             #
###############################################################################

# Battery
safe_defaults_write com.apple.controlcenter "NSStatusItem Visible Battery" -bool false

# Control Center (BentoBox)
safe_defaults_write com.apple.controlcenter "NSStatusItem Visible BentoBox" -bool true

# Set physical spacing between menu bar icons to 10px
if ! safe_defaults_write_current_host -globalDomain NSStatusItemSpacing -int 10; then
  log_warning "Skipping currentHost NSStatusItemSpacing update"
fi
safe_defaults_write -globalDomain NSStatusItemSpacing -int 10

# Set padding around icons to 6px (makes the button itself smaller)
if ! safe_defaults_write_current_host -globalDomain NSStatusItemSelectionPadding -int 6; then
  log_warning "Skipping currentHost NSStatusItemSelectionPadding update"
fi
safe_defaults_write -globalDomain NSStatusItemSelectionPadding -int 6

# Now Playing
safe_defaults_write com.apple.controlcenter "NSStatusItem Visible NowPlaying" -bool false

# Screen Mirroring
safe_defaults_write com.apple.controlcenter "NSStatusItem Visible ScreenMirroring" -bool false

# WiFi
safe_defaults_write com.apple.controlcenter "NSStatusItem Visible WiFi" -bool false

# Sound / Volume (Not explicitly in previous output, but good to set standard defaults if known, otherwise skip)
# Bluetooth (Same as above)

###############################################################################
# Clock                                                                       #
###############################################################################

safe_defaults_write com.apple.menuextra.clock IsAnalog -bool false
safe_defaults_write com.apple.menuextra.clock ShowAMPM -bool true
safe_defaults_write com.apple.menuextra.clock ShowDate -bool true
safe_defaults_write com.apple.menuextra.clock ShowDayOfWeek -bool true
safe_defaults_write com.apple.menuextra.clock ShowSeconds -bool true

# Apply changes (SystemUIServer handles the menu bar clock, Control Center handles the rest)
kill_process "SystemUIServer"
kill_process "ControlCenter"

log_success "Menu Bar settings applied"
