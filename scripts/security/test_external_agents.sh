#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
# shellcheck source=external_agents.sh
source "${SCRIPT_DIR}/external_agents.sh"
tmp_dir="$(/usr/bin/mktemp -d)"
manifest="${tmp_dir}/manifest.local"
trap '/bin/rm -rf "$tmp_dir"' EXIT

write_manifest() {
  /usr/bin/printf '%s\n' "$@" >"$manifest"
}

expect_invalid() {
  write_manifest "$@"
  if external_agents_load_manifest "$manifest" >/dev/null 2>&1; then
    printf 'expected invalid manifest to fail\n' >&2
    exit 1
  fi
  if ((${#EXTERNAL_AGENT_LABELS[@]} != 0 || ${#EXTERNAL_AGENT_RELAUNCH[@]} != 0)); then
    printf 'invalid manifest published partial state\n' >&2
    exit 1
  fi
}

header=(
  '# relaunch-prefix=com.example.'
  '# relaunch-lock-path=/tmp/accretion-test.lock'
  '# relaunch-lock-label=com.example.sync'
)
sync_row='com.example.sync|/tmp/repo|/tmp/repo/launchd/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|enabled|true'
shell_row='com.example.monitor|/tmp/repo|/tmp/repo/launchd/com.example.monitor.plist|/tmp/LaunchAgents/com.example.monitor.plist|/tmp/repo/bin/check.sh|enabled|false'
disabled_row='com.example.paused|/tmp/repo|/tmp/repo/launchd/com.example.paused.plist|/tmp/LaunchAgents/com.example.paused.plist.disabled|/tmp/repo/bin/paused|disabled|false'

write_manifest "${header[@]}" "$sync_row" "$shell_row" "$disabled_row"
external_agents_load_manifest "$manifest"
[[ ${#EXTERNAL_AGENT_LABELS[@]} -eq 3 ]]
[[ ${#EXTERNAL_AGENT_RELAUNCH[@]} -eq 3 ]]
[[ ${EXTERNAL_AGENT_LABELS[0]} == com.example.sync ]]
[[ ${EXTERNAL_AGENT_RELAUNCH[0]} == true ]]
[[ ${EXTERNAL_AGENT_RELAUNCH[1]} == false ]]
[[ ${EXTERNAL_AGENT_STATES[2]} == disabled ]]
[[ ${#EXTERNAL_AGENT_LOCKED_LABELS[@]} -eq 1 ]]

expect_invalid "${header[@]}" 'com.example.sync|/tmp/repo|/tmp/repo/launchd/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|enabled'
expect_invalid "${header[@]}" 'com.example.sync.plist|/tmp/repo|/tmp/repo/launchd/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|enabled|true'
expect_invalid "${header[@]}" 'com.example.sync|/tmp/repo|/tmp/repo/../other/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|enabled|true'
expect_invalid "${header[@]}" 'com.example.sync|/tmp/repo|/tmp/repo/launchd/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|active|true'
expect_invalid "${header[@]}" 'com.example.sync|/tmp/repo|/tmp/repo/launchd/com.example.sync.plist|/tmp/LaunchAgents/com.example.sync.plist|/tmp/repo/bin/sync|enabled|maybe'
expect_invalid "${header[@]}" "$sync_row" "$sync_row"
expect_invalid "${header[@]}" "$sync_row" 'malformed record'
expect_invalid "${header[@]}" "${header[0]}" '# relaunch-prefix=com.example.' "$sync_row"
expect_invalid "${header[@]}" '# relaunch-prefix=com.example.' '# relaunch-lock-path=/tmp/accretion-test.lock' '# relaunch-lock-label=com.example.sync' '# relaunch-lock-label=com.example.sync' "$sync_row"
expect_invalid '# relaunch-prefix=com.example.' '# relaunch-lock-path=/tmp/accretion-test.lock' '# relaunch-lock-label=com.example.shell' "$shell_row"
expect_invalid '# relaunch-prefix=com.example.' 'com.example.disabled|/tmp/repo|/tmp/repo/launchd/com.example.disabled.plist|/tmp/LaunchAgents/com.example.disabled.plist.disabled|/tmp/repo/bin/disabled|disabled|true'

enabled_state=$(/usr/bin/printf '%s\n' 'disabled services = {' '  "com.example.sync" => enabled' '}')
external_agents_get_disabled_state "$enabled_state" com.example.sync
[[ $EXTERNAL_AGENTS_DISABLED_STATE == enabled ]]
disabled_state=$(/usr/bin/printf '%s\n' 'disabled services = {' '  "com.example.sync" => disabled' '}')
external_agents_get_disabled_state "$disabled_state" com.example.sync
[[ $EXTERNAL_AGENTS_DISABLED_STATE == disabled ]]
if external_agents_get_disabled_state 'unknown output' com.example.sync; then
  printf 'malformed disabled-state output was accepted\n' >&2
  exit 1
fi

printf 'external-agent manifest tests passed\n'
