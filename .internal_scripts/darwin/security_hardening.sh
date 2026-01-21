#!/bin/bash

# Source common library
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)"
source "${LIB_DIR}/common.sh"

# Check guard flag
require_flag "ALLOW_HARDEN" "セキュリティハードニング"

if ! sudo -v; then
  log_error "sudo unavailable. Aborting hardening."
  exit 1
fi

log_info "🛡️  Starting macOS Security Hardening..."

###############################################################################
# 0. Login Window Message Removal                                              #
###############################################################################
/bin/sh -c '/usr/bin/defaults read /Library/Preferences/com.apple.loginwindow LoginwindowText >/dev/null 2>&1 && sudo /usr/bin/defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText' || record_failure "LoginwindowText delete"

###############################################################################
# 1. Network Security (Firewall & Stealth Mode)                               #
###############################################################################
log_info "Configuring Application Firewall..."
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on || record_failure "Enable firewall"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on || record_failure "Enable stealth mode"
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on || record_failure "Allow signed apps"
sudo pkill -HUP socketfilterfw || record_failure "Restart socketfilterfw"

###############################################################################
# 2. Service Hardening (Disable Remote Access)                                #
###############################################################################
log_info "Disabling Remote Services..."
sudo systemsetup -setremotelogin off || record_failure "Disable Remote Login"
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off || record_failure "Disable ARD"

###############################################################################
# 3. Account Security                                                         #
###############################################################################
log_info "Disabling Guest Account..."
sudo sysadminctl -guestAccount off || record_failure "Disable guest account"

###############################################################################
# 4. File System Visibility                                                   #
###############################################################################
log_info "Setting Finder preferences..."
safe_defaults_write NSGlobalDomain AppleShowAllExtensions -bool true || record_failure "Show all extensions"
kill_process "Finder"

log_success "✅  Security hardening complete"

# Report any failures
report_failures
