#!/bin/bash
set -euo pipefail

# Source common library
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)"
source "${LIB_DIR}/common.sh"

usage() {
  cat <<'EOF'
Usage: ./run_onchange_darwin_keyboard.sh.tmpl [--apply] [--user <name>] [--help]

Preset (recommended):
  KeyRepeat = 1 (fastest)
  InitialKeyRepeat = 10 (minimal delay)
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

while [ $# -gt 0 ]; do
  case "$1" in
    --apply)
      apply=1
      ;;
    --user)
      shift
      target_user=${1:?"--user requires an argument"}
      ;;
    -h|--help)
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
  log_error "Target user '$target_user' does not exist"
  exit 1
fi

cmd_prefix=()
if [ "$(whoami)" != "$target_user" ]; then
  cmd_prefix=(sudo -u "$target_user")
fi

PR_KeyRepeat=1
PR_InitialKeyRepeat=10
PR_ApplePressAndHoldEnabled=false
PR_fnState=1

print_preview() {
  echo "=== Keyboard preset for user: $target_user ==="
  printf "KeyRepeat: %s\n" "$PR_KeyRepeat"
  printf "InitialKeyRepeat: %s\n" "$PR_InitialKeyRepeat"
  printf "ApplePressAndHoldEnabled: %s\n" "$PR_ApplePressAndHoldEnabled"
  printf "com.apple.keyboard.fnState: %s\n" "$PR_fnState"
  echo
  echo "Commands to apply:"
  echo "  ${cmd_prefix[*]:-} defaults write -g KeyRepeat -int $PR_KeyRepeat"
  echo "  ${cmd_prefix[*]:-} defaults write -g InitialKeyRepeat -int $PR_InitialKeyRepeat"
  echo "  ${cmd_prefix[*]:-} defaults write -g ApplePressAndHoldEnabled -bool ${PR_ApplePressAndHoldEnabled}" 
  echo "  ${cmd_prefix[*]:-} defaults write -g com.apple.keyboard.fnState -int $PR_fnState"
}

if [ "$apply" -eq 0 ]; then
  print_preview
  echo
  echo "Run with --apply to write these values."
  exit 0
fi

if ! check_command defaults; then
  exit 1
fi

require_flag "ALLOW_KEYBOARD_APPLY" "キーボード設定変更"

print_preview

echo
"${cmd_prefix[@]}" defaults write -g KeyRepeat -int "$PR_KeyRepeat"
log_success "Set KeyRepeat = $PR_KeyRepeat"

"${cmd_prefix[@]}" defaults write -g InitialKeyRepeat -int "$PR_InitialKeyRepeat"
log_success "Set InitialKeyRepeat = $PR_InitialKeyRepeat"

if [ "$PR_ApplePressAndHoldEnabled" = "false" ]; then
  "${cmd_prefix[@]}" defaults write -g ApplePressAndHoldEnabled -bool false
  log_success "Set ApplePressAndHoldEnabled = false"
else
  "${cmd_prefix[@]}" defaults write -g ApplePressAndHoldEnabled -bool true
  log_success "Set ApplePressAndHoldEnabled = true"
fi

"${cmd_prefix[@]}" defaults write -g com.apple.keyboard.fnState -int "$PR_fnState"
log_success "Set com.apple.keyboard.fnState = $PR_fnState"

log_info "Done. Logout or restart affected apps if changes do not apply immediately."
