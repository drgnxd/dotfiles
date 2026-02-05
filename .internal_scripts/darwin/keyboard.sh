#!/bin/bash
set -euo pipefail

SOURCE_ROOT="${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Source shared bootstrap
# shellcheck source=../lib/bootstrap.sh
# shellcheck disable=SC1091
source "${SOURCE_ROOT}/.internal_scripts/lib/bootstrap.sh"

usage() {
	cat <<'EOF'
Usage: ./run_onchange_darwin_keyboard.sh.tmpl [--apply] [--user <name>] [--help]

Preset (recommended):
  KeyRepeat = 1 (fastest)
  InitialKeyRepeat = 15 (short delay)
  ApplePressAndHoldEnabled = false (prefer repeat over accent popup)
  com.apple.keyboard.fnState = 1 (Fn behaves as standard function keys)

Behavior:
  - Without flags, prints the preset and the commands.
  - With --apply, writes the values for the target user.
  - Use --user to override the console user.
EOF
}

apply=0
target_user=${SUDO_USER:-$(get_console_user)}
preview_prefix=""

while [ $# -gt 0 ]; do
	case "$1" in
	--apply)
		apply=1
		;;
	--user)
		shift
		target_user=${1:?"--user requires an argument"}
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		echo "Unknown option: $1" >&2
		usage
		exit 1
		;;
	esac
	shift
done

if ! id "$target_user" >/dev/null 2>&1; then
	record_failure "Target user not found: $target_user"
	report_failures
	exit 1
fi

if [ "$(whoami)" != "$target_user" ]; then
	preview_prefix="sudo -u ${target_user} "
fi

PR_KeyRepeat=1
PR_InitialKeyRepeat=15
PR_ApplePressAndHoldEnabled=false
PR_fnState=1

# Validate keyboard settings
validate_keyboard_settings() {
	# KeyRepeat: 1-120 (lower = faster)
	if [ "$PR_KeyRepeat" -lt 1 ] || [ "$PR_KeyRepeat" -gt 120 ]; then
		log_error "KeyRepeat must be between 1-120 (got: $PR_KeyRepeat)"
		return 1
	fi

	# InitialKeyRepeat: 10-120 (lower = shorter delay)
	if [ "$PR_InitialKeyRepeat" -lt 10 ] || [ "$PR_InitialKeyRepeat" -gt 120 ]; then
		log_error "InitialKeyRepeat must be between 10-120 (got: $PR_InitialKeyRepeat)"
		return 1
	fi

	# fnState: 0 or 1
	if [ "$PR_fnState" != "0" ] && [ "$PR_fnState" != "1" ]; then
		log_error "com.apple.keyboard.fnState must be 0 or 1 (got: $PR_fnState)"
		return 1
	fi

	return 0
}

print_preview() {
	echo "=== Keyboard preset for user: $target_user ==="
	printf "KeyRepeat: %s\n" "$PR_KeyRepeat"
	printf "InitialKeyRepeat: %s\n" "$PR_InitialKeyRepeat"
	printf "ApplePressAndHoldEnabled: %s\n" "$PR_ApplePressAndHoldEnabled"
	printf "com.apple.keyboard.fnState: %s\n" "$PR_fnState"
	echo
	echo "Commands to apply:"
	printf "  %sdefaults write -g KeyRepeat -int %s\n" "$preview_prefix" "$PR_KeyRepeat"
	printf "  %sdefaults write -g InitialKeyRepeat -int %s\n" "$preview_prefix" "$PR_InitialKeyRepeat"
	printf "  %sdefaults write -g ApplePressAndHoldEnabled -bool %s\n" "$preview_prefix" "$PR_ApplePressAndHoldEnabled"
	printf "  %sdefaults write -g com.apple.keyboard.fnState -int %s\n" "$preview_prefix" "$PR_fnState"
}

apply_defaults() {
	local label=$1
	shift

	if ! safe_defaults_write_as_user "$target_user" "$@"; then
		record_failure "Set ${label}"
		return 0
	fi

	log_success "Set ${label}"
}

if [ "$apply" -eq 0 ]; then
	print_preview
	echo
	echo "Run with --apply to write these values."
	exit 0
fi

if ! command -v defaults >/dev/null 2>&1; then
	record_failure "defaults command not found"
	report_failures
	exit 1
fi

require_flag "ALLOW_KEYBOARD_APPLY" "keyboard settings modification"

# Validate settings before applying
if ! validate_keyboard_settings; then
	log_error "Invalid keyboard settings detected"
	exit 1
fi

print_preview

echo
apply_defaults "KeyRepeat = $PR_KeyRepeat" -g KeyRepeat -int "$PR_KeyRepeat"
apply_defaults "InitialKeyRepeat = $PR_InitialKeyRepeat" -g InitialKeyRepeat -int "$PR_InitialKeyRepeat"

if [ "$PR_ApplePressAndHoldEnabled" = "false" ]; then
	apply_defaults "ApplePressAndHoldEnabled = false" -g ApplePressAndHoldEnabled -bool false
else
	apply_defaults "ApplePressAndHoldEnabled = true" -g ApplePressAndHoldEnabled -bool true
fi

apply_defaults "com.apple.keyboard.fnState = $PR_fnState" -g com.apple.keyboard.fnState -int "$PR_fnState"

log_info "Done. Logout or restart affected apps if changes do not apply immediately."
report_failures
