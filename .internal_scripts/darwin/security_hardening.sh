#!/bin/bash
set -euo pipefail

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/.internal_scripts/lib/bootstrap.sh"

# Check guard flag
require_flag "ALLOW_HARDEN" "security hardening"

if ! sudo -v; then
	log_error "sudo unavailable. Aborting hardening."
	exit 1
fi

log_info "🛡️  Starting macOS Security Hardening..."

###############################################################################
# 0. Login Window Message Removal                                            #
###############################################################################
# Remove custom login window text banner if present
# This prevents information disclosure at the login screen
if sudo /usr/bin/defaults read /Library/Preferences/com.apple.loginwindow LoginwindowText >/dev/null 2>&1; then
	sudo /usr/bin/defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText || record_failure "LoginwindowText delete"
else
	log_info "LoginwindowText not set; skipping"
fi

###############################################################################
# 1. Network Security (Firewall & Stealth Mode)                             #
###############################################################################
log_info "Configuring Application Firewall..."

# Enable macOS Application Firewall (socketfilterfw)
# This blocks incoming connections at the application layer
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on || record_failure "Enable firewall"

# Enable Stealth Mode
# Prevents the system from responding to ICMP ping requests and connection attempts
# Makes the system invisible to port scanners and casual network probes
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on || record_failure "Enable stealth mode"

# Allow signed applications automatically
# Apps signed by valid Apple Developer IDs can accept incoming connections
# without explicit user approval (reduces friction while maintaining security)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on || record_failure "Allow signed apps"

# Restart firewall daemon to apply changes
sudo pkill -HUP socketfilterfw || record_failure "Restart socketfilterfw"

###############################################################################
# 2. Service Hardening (Disable Remote Access)                              #
###############################################################################
log_info "Disabling Remote Services..."

# Disable SSH Remote Login
# Prevents remote shell access via SSH protocol (Port 22)
sudo systemsetup -setremotelogin off || record_failure "Disable Remote Login"

# Disable Apple Remote Desktop (ARD)
# Prevents remote screen sharing and control via Apple's ARD protocol
# This is a common vector for unauthorized access and should be disabled unless explicitly needed
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off || record_failure "Disable ARD"

###############################################################################
# 3. Account Security                                                       #
###############################################################################
# 3. Guest Account                                                          #
###############################################################################
log_info "Disabling Guest Account..."

# Disable Guest Account login
# Guest accounts bypass FileVault encryption and allow unauthenticated access
# This is a significant security risk and should be disabled on all systems
sudo sysadminctl -guestAccount off || record_failure "Disable guest account"

log_success "✅  Security hardening complete"

# Report any failures
report_failures
