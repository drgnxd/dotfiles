#!/bin/bash
set -euo pipefail

if [ "${ALLOW_HARDEN:-0}" != "1" ]; then
  echo "Refusing to harden without ALLOW_HARDEN=1. Set ALLOW_HARDEN=1 to proceed." >&2
  exit 1
fi

if ! sudo -v; then
  echo "sudo unavailable. Aborting hardening." >&2
  exit 1
fi

echo "🛡️  Starting macOS Security Hardening..."

failures=()
run_or_record() {
  local msg=$1; shift
  if "$@"; then
    :
  else
    failures+=("$msg")
  fi
}

###############################################################################
# 0. Login Window Message Removal                                              #
###############################################################################
run_or_record "LoginwindowText delete" /bin/sh -c '/usr/bin/defaults read /Library/Preferences/com.apple.loginwindow LoginwindowText >/dev/null 2>&1 && sudo /usr/bin/defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText'

###############################################################################
# 1. Network Security (Firewall & Stealth Mode)                               #
###############################################################################
echo "Configuring Application Firewall..."
run_or_record "Enable firewall" sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
run_or_record "Enable stealth mode" sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on
run_or_record "Allow signed apps" sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on
run_or_record "Restart socketfilterfw" sudo pkill -HUP socketfilterfw

###############################################################################
# 2. Service Hardening (Disable Remote Access)                                #
###############################################################################
echo "Disabling Remote Services..."
run_or_record "Disable Remote Login" sudo systemsetup -setremotelogin off
run_or_record "Disable ARD" sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off

###############################################################################
# 3. Account Security                                                         #
###############################################################################
echo "Disabling Guest Account..."
run_or_record "Disable guest account" sudo sysadminctl -guestAccount off

###############################################################################
# 4. File System Visibility                                                   #
###############################################################################
echo "Setting Finder preferences..."
run_or_record "Show all extensions" defaults write NSGlobalDomain AppleShowAllExtensions -bool true
run_or_record "Restart Finder" killall Finder

echo "✅  Security hardening complete."

if [ "${#failures[@]}" -ne 0 ]; then
  echo "The following steps failed:" >&2
  printf ' - %s\n' "${failures[@]}" >&2
  exit 1
fi
