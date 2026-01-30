#!/bin/bash
set -euo pipefail

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/.internal_scripts/lib/bootstrap.sh"

log_info "🔍  Auditing macOS security posture..."

# Console user for user-scoped defaults
target_user=${SUDO_USER:-$(get_console_user)}

printf "[Firewall] State: %s\n" "$({ /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate || true; } | awk 'NF{print $NF}' | tail -n1)"
printf "[Firewall] Stealth mode: %s\n" "$({ /usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode || true; } | awk 'NF{print $NF}' | tail -n1)"
printf "[Firewall] Allow signed apps: %s\n" "$({ /usr/libexec/ApplicationFirewall/socketfilterfw --getallowsigned || true; } | awk 'NF{print $NF}' | tail -n1)"
printf "[SIP] State: %s\n" "$({ csrutil status 2>/dev/null || true; } | awk 'NF{print $NF}' | sed 's/\.$//' | head -n1)"

ssh_state=$({ systemsetup -getremotelogin 2>/dev/null || true; })
[ -n "$ssh_state" ] && printf "[RemoteLogin] %s\n" "$ssh_state" || printf "[RemoteLogin] unavailable (may require sudo)\n"

ard_state=$({ /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -status -verbose 2>/dev/null || true; })
if [ -n "$ard_state" ]; then
	printf "[ARD] %s\n" "$ard_state" | head -n 1
else
	printf "[ARD] status unavailable (may require sudo)\n"
fi

guest_enabled=$(read_defaults /Library/Preferences/com.apple.loginwindow GuestEnabled)
printf "[GuestAccount] %s\n" "$guest_enabled"

login_msg=$(read_defaults /Library/Preferences/com.apple.loginwindow LoginwindowText)
printf "[LoginMessage] %s\n" "$login_msg"

if [ "$EUID" -eq 0 ]; then
	ext_value=$({ sudo -u "$target_user" defaults read NSGlobalDomain AppleShowAllExtensions 2>/dev/null || true; })
else
	ext_value=$({ defaults read NSGlobalDomain AppleShowAllExtensions 2>/dev/null || true; })
fi
[ -n "$ext_value" ] && printf "[Finder] AppleShowAllExtensions: %s\n" "$ext_value" || printf "[Finder] AppleShowAllExtensions: unavailable\n"

log_success "Audit complete."
