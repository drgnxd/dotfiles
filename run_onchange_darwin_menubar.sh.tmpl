#!/bin/bash

set -e

echo "Setting up Menu Bar and Control Center preferences..."

###############################################################################
# Control Center & Menu Bar Items                                             #
###############################################################################

# Battery
defaults write com.apple.controlcenter "NSStatusItem Visible Battery" -bool false

# Control Center (BentoBox)
defaults write com.apple.controlcenter "NSStatusItem Visible BentoBox" -bool true

# Set physical spacing between menu bar icons to 10px
defaults -currentHost write -globalDomain NSStatusItemSpacing -int 10
defaults write -globalDomain NSStatusItemSpacing -int 10

# Set padding around icons to 6px (makes the button itself smaller)
defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 6
defaults write -globalDomain NSStatusItemSelectionPadding -int 6

# Now Playing
defaults write com.apple.controlcenter "NSStatusItem Visible NowPlaying" -bool false

# Screen Mirroring
defaults write com.apple.controlcenter "NSStatusItem Visible ScreenMirroring" -bool false

# WiFi
defaults write com.apple.controlcenter "NSStatusItem Visible WiFi" -bool false

# Sound / Volume (Not explicitly in previous output, but good to set standard defaults if known, otherwise skip)
# Bluetooth (Same as above)

###############################################################################
# Clock                                                                       #
###############################################################################

defaults write com.apple.menuextra.clock IsAnalog -bool false
defaults write com.apple.menuextra.clock ShowAMPM -bool true
defaults write com.apple.menuextra.clock ShowDate -bool true
defaults write com.apple.menuextra.clock ShowDayOfWeek -bool true
defaults write com.apple.menuextra.clock ShowSeconds -bool true

# Apply changes (SystemUIServer handles the menu bar clock, Control Center handles the rest)
killall SystemUIServer || true
killall ControlCenter || true

echo "Menu Bar settings applied."
