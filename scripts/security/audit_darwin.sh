#!/usr/bin/env bash

set -euo pipefail

JSON_OUTPUT=0
STRICT_MODE=0
WARN_COUNT=0

RESULT_SECTIONS=()
RESULT_NAMES=()
RESULT_STATUSES=()
RESULT_OBSERVED=()
RESULT_GUIDANCE=()

for argument in "$@"; do
  case "$argument" in
  --json)
    JSON_OUTPUT=1
    ;;
  --strict)
    STRICT_MODE=1
    ;;
  *)
    printf 'Unknown option: %s\n' "$argument" >&2
    printf 'Usage: %s [--json] [--strict]\n' "${0##*/}" >&2
    exit 0
    ;;
  esac
done

case "${OSTYPE:-}" in
darwin*) ;;
*)
  printf '%s\n' 'This audit is macOS-only; no checks were run.'
  exit 0
  ;;
esac

add_result() {
  local section=$1
  local name=$2
  local status=$3
  local observed=$4
  local guidance=${5:-}
  local index=${#RESULT_NAMES[@]}

  case "$status" in
  OK | WARN | MANUAL | UNKNOWN) ;;
  *)
    printf 'Internal error: invalid audit status\n' >&2
    exit 0
    ;;
  esac

  RESULT_SECTIONS[index]=$section
  RESULT_NAMES[index]=$name
  RESULT_STATUSES[index]=$status
  RESULT_OBSERVED[index]=$observed
  RESULT_GUIDANCE[index]=$guidance

  if [[ $status == "WARN" ]]; then
    ((WARN_COUNT += 1))
  fi
}

trim_whitespace() {
  local value=$1

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  TRIMMED_VALUE=$value
}

display_value() {
  local value=$1

  value=${value//$'\r'/\\r}
  value=${value//$'\n'/\\n}
  value=${value//$'\t'/\\t}
  DISPLAY_VALUE=$value
}

json_escape() {
  local value=$1

  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//$'\b'/\\b}
  value=${value//$'\f'/\\f}
  value=${value//$'\n'/\\n}
  value=${value//$'\r'/\\r}
  value=${value//$'\t'/\\t}
  JSON_ESCAPED=$value
}

check_filevault() {
  local section='Boot and disk'
  local tool
  local output

  if ! tool=$(command -v fdesetup 2>/dev/null); then
    add_result "$section" 'FileVault' 'UNKNOWN' 'fdesetup is unavailable' 'Restore access to fdesetup and rerun the audit.'
    return
  fi

  if ! output=$("$tool" status 2>/dev/null); then
    add_result "$section" 'FileVault' 'UNKNOWN' 'fdesetup status failed' 'Run fdesetup status manually and investigate the error.'
    return
  fi

  case "$output" in
  *'FileVault is On.'*)
    add_result "$section" 'FileVault' 'OK' "$output"
    ;;
  *'FileVault is Off.'*)
    add_result "$section" 'FileVault' 'WARN' "$output" 'Enable FileVault in System Settings > Privacy & Security > FileVault.'
    ;;
  *)
    add_result "$section" 'FileVault' 'UNKNOWN' "$output" 'The fdesetup status output was not recognized.'
    ;;
  esac
}

check_sip() {
  local section='Boot and disk'
  local tool
  local output

  if ! tool=$(command -v csrutil 2>/dev/null); then
    add_result "$section" 'System Integrity Protection' 'UNKNOWN' 'csrutil is unavailable' 'Restore access to csrutil and rerun the audit.'
    return
  fi

  if ! output=$("$tool" status 2>/dev/null); then
    add_result "$section" 'System Integrity Protection' 'UNKNOWN' 'csrutil status failed' 'Run csrutil status manually and investigate the error.'
    return
  fi

  case "$output" in
  *'System Integrity Protection status: enabled.'*)
    add_result "$section" 'System Integrity Protection' 'OK' "$output"
    ;;
  *'System Integrity Protection status: disabled.'*)
    add_result "$section" 'System Integrity Protection' 'WARN' "$output" 'Boot into macOS Recovery and enable System Integrity Protection.'
    ;;
  *)
    add_result "$section" 'System Integrity Protection' 'UNKNOWN' "$output" 'The csrutil status output was not recognized.'
    ;;
  esac
}

check_gatekeeper() {
  local section='Boot and disk'
  local tool
  local output

  if ! tool=$(command -v spctl 2>/dev/null); then
    add_result "$section" 'Gatekeeper assessment' 'UNKNOWN' 'spctl is unavailable' 'Restore access to spctl and rerun the audit.'
    return
  fi

  if ! output=$("$tool" --status 2>/dev/null); then
    add_result "$section" 'Gatekeeper assessment' 'UNKNOWN' 'spctl --status failed' 'Run spctl --status manually and investigate the error.'
    return
  fi

  case "$output" in
  *'assessments enabled'*)
    add_result "$section" 'Gatekeeper assessment' 'OK' "$output"
    ;;
  *'assessments disabled'*)
    add_result "$section" 'Gatekeeper assessment' 'WARN' "$output" 'Enable Gatekeeper using an operator-approved administrative procedure.'
    ;;
  *)
    add_result "$section" 'Gatekeeper assessment' 'UNKNOWN' "$output" 'The spctl status output was not recognized.'
    ;;
  esac
}

check_firewall_value() {
  local name=$1
  local argument=$2
  local enabled_pattern=$3
  local disabled_pattern=$4
  local remediation=$5
  local tool='/usr/libexec/ApplicationFirewall/socketfilterfw'
  local output

  if [[ ! -x $tool ]]; then
    add_result 'Network' "$name" 'UNKNOWN' 'socketfilterfw is unavailable' 'Restore access to socketfilterfw and rerun the audit.'
    return
  fi

  if ! output=$("$tool" "$argument" 2>/dev/null); then
    add_result 'Network' "$name" 'UNKNOWN' "socketfilterfw $argument failed" "Run socketfilterfw $argument manually and investigate the error."
    return
  fi

  if [[ $output == *"$enabled_pattern"* ]]; then
    add_result 'Network' "$name" 'OK' "$output"
  elif [[ $output == *"$disabled_pattern"* ]]; then
    add_result 'Network' "$name" 'WARN' "$output" "$remediation"
  else
    add_result 'Network' "$name" 'UNKNOWN' "$output" 'The socketfilterfw output was not recognized.'
  fi
}

check_system_extensions() {
  local section='Declared-vs-actual drift'
  local tool
  local output
  local line
  local extension_count=0
  local zero_reported=0

  if ! tool=$(command -v systemextensionsctl 2>/dev/null); then
    add_result "$section" 'Loaded system extensions' 'UNKNOWN' 'systemextensionsctl is unavailable' 'Restore access to systemextensionsctl and rerun the audit.'
    return
  fi

  if ! output=$("$tool" list 2>/dev/null); then
    add_result "$section" 'Loaded system extensions' 'UNKNOWN' 'systemextensionsctl list failed' 'Run systemextensionsctl list manually and investigate the error.'
    return
  fi

  while IFS= read -r line; do
    if [[ $line =~ ^[[:space:]]*0[[:space:]]+extension\(s\) ]]; then
      zero_reported=1
    elif [[ $line =~ \[[^]]+\][[:space:]]*$ ]] && [[ $line != *'extension(s)'* ]] && [[ $line != *$'teamID\tbundleID'* ]]; then
      trim_whitespace "$line"
      add_result "$section" 'System extension' 'WARN' "$TRIMMED_VALUE" 'Remove the extension or explicitly declare and justify it in the Nix configuration.'
      ((extension_count += 1))
    fi
  done <<<"$output"

  if ((extension_count > 0)); then
    return
  fi

  if ((zero_reported == 1)); then
    add_result "$section" 'Loaded system extensions' 'OK' 'None'
  else
    add_result "$section" 'Loaded system extensions' 'UNKNOWN' "$output" 'The systemextensionsctl output was not recognized.'
  fi
}

array_contains() {
  local needle=$1
  shift
  local value

  for value in "$@"; do
    if [[ $value == "$needle" ]]; then
      return 0
    fi
  done

  return 1
}

check_launch_agents() {
  local section='Declared-vs-actual drift'
  local script_path=${BASH_SOURCE[0]}
  local script_dir=${script_path%/*}
  local repo_root
  local nix_command
  local host_json
  local host_name
  local installable
  local declared_json
  local declared_output
  local declared_name
  local expected_name
  local launch_agents_dir
  local disk_path
  local disk_name
  local mismatch_count=0
  local -a declared_names=()
  local -a expected_names=()
  local -a disk_paths=()
  local -a disk_names=()

  if [[ $script_dir == "$script_path" ]]; then
    script_dir='.'
  fi

  if ! repo_root=$(cd "$script_dir/../.." && pwd -P); then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Repository root could not be resolved' 'Run the audit from an intact repository checkout.'
    return
  fi

  if ! nix_command=$(command -v nix 2>/dev/null); then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'nix is unavailable' 'Restore access to nix and rerun the audit.'
    return
  fi

  if ! host_json=$(cd "$repo_root" && "$nix_command" eval --no-write-lock-file --json 'path:.#darwinConfigurations' --apply builtins.attrNames 2>/dev/null); then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Darwin configuration discovery failed' 'Evaluate darwinConfigurations with path:. and investigate the error.'
    return
  fi

  if [[ $host_json =~ ^\[\"([A-Za-z0-9._-]+)\"\]$ ]]; then
    host_name=${BASH_REMATCH[1]}
  else
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Darwin configuration names were unparsable or ambiguous' 'Ensure the flake exposes exactly one Darwin configuration with a simple attribute name.'
    return
  fi

  installable="path:.#darwinConfigurations.\"${host_name}\".config.launchd.user.agents"
  if ! declared_json=$(cd "$repo_root" && "$nix_command" eval --no-write-lock-file --json "$installable" --apply builtins.attrNames 2>/dev/null); then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Declared LaunchAgent evaluation failed' 'Evaluate config.launchd.user.agents with path:. and investigate the error.'
    return
  fi

  if [[ $declared_json != \[*\] ]]; then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Declared LaunchAgent output was not JSON' 'Inspect the nix eval output and rerun the audit.'
    return
  fi

  if ! declared_output=$(cd "$repo_root" && "$nix_command" eval --no-write-lock-file --raw "$installable" --apply 'agents: builtins.concatStringsSep "\n" (builtins.attrNames agents)' 2>/dev/null); then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'Declared LaunchAgent names could not be decoded' 'Inspect the nix eval output and rerun the audit.'
    return
  fi

  while IFS= read -r declared_name; do
    [[ -n $declared_name ]] || continue
    if [[ ! $declared_name =~ ^[A-Za-z0-9._+-]+$ ]]; then
      add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'A declared LaunchAgent name was unparsable' 'Use simple LaunchAgent attribute names and rerun the audit.'
      return
    fi
    declared_names[${#declared_names[@]}]=$declared_name
    expected_names[${#expected_names[@]}]="org.nixos.${declared_name}.plist"
  done <<<"$declared_output"

  if [[ -z ${HOME:-} ]]; then
    add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'HOME is unset' 'Run the audit from a normal user session.'
    return
  fi

  launch_agents_dir="$HOME/Library/LaunchAgents"
  if [[ -d $launch_agents_dir ]]; then
    if [[ ! -r $launch_agents_dir || ! -x $launch_agents_dir ]]; then
      add_result "$section" 'User LaunchAgents' 'UNKNOWN' 'The user LaunchAgents directory is not readable' 'Review the directory permissions and rerun the audit.'
      return
    fi

    shopt -s nullglob
    disk_paths=("$launch_agents_dir"/*.plist "$launch_agents_dir"/*.plist.disabled)
    shopt -u nullglob
  fi

  for disk_path in "${disk_paths[@]}"; do
    disk_name=${disk_path##*/}
    disk_names[${#disk_names[@]}]=$disk_name
    if ! array_contains "$disk_name" "${expected_names[@]}"; then
      add_result "$section" 'Undeclared user LaunchAgent' 'WARN' "$disk_name" 'Remove the persistence or declare it in launchd.user.agents.'
      ((mismatch_count += 1))
    fi
  done

  for expected_name in "${expected_names[@]}"; do
    if ! array_contains "$expected_name" "${disk_names[@]}"; then
      add_result "$section" 'Missing declared LaunchAgent' 'WARN' "$expected_name" 'Review nix-darwin activation for the declared agent.'
      ((mismatch_count += 1))
    fi
  done

  if ((mismatch_count == 0)); then
    add_result "$section" 'User LaunchAgents' 'OK' 'On-disk agents match launchd.user.agents'
  fi
}

parse_nix_setting() {
  local config_output=$1
  local key=$2
  local line
  local found=0
  local value=''

  while IFS= read -r line; do
    if [[ $line == "$key = "* ]]; then
      value=${line#"$key = "}
      ((found += 1))
    fi
  done <<<"$config_output"

  if ((found != 1)); then
    return 1
  fi

  trim_whitespace "$value"
  NIX_SETTING_VALUE=$TRIMMED_VALUE
}

check_nix_trust_boundary() {
  local section='Nix trust boundary'
  local nix_command
  local config_output
  local observed
  local key

  if ! nix_command=$(command -v nix 2>/dev/null); then
    for key in trusted-users sandbox substituters trusted-public-keys; do
      add_result "$section" "$key" 'UNKNOWN' 'nix is unavailable' 'Restore access to nix and rerun the audit.'
    done
    return
  fi

  if ! config_output=$("$nix_command" config show 2>/dev/null); then
    if ! config_output=$("$nix_command" show-config 2>/dev/null); then
      for key in trusted-users sandbox substituters trusted-public-keys; do
        add_result "$section" "$key" 'UNKNOWN' 'Effective Nix configuration could not be read' 'Run nix config show or nix show-config manually and investigate the error.'
      done
      return
    fi
  fi

  if parse_nix_setting "$config_output" 'trusted-users'; then
    observed=${NIX_SETTING_VALUE:-'(empty)'}
    if [[ $NIX_SETTING_VALUE == 'root' ]]; then
      add_result "$section" 'trusted-users' 'OK' "$observed"
    else
      add_result "$section" 'trusted-users' 'WARN' "$observed" 'Restrict trusted-users to root; every additional entry is root-equivalent.'
    fi
  else
    add_result "$section" 'trusted-users' 'UNKNOWN' 'Setting was absent or duplicated' 'Inspect the effective Nix daemon configuration.'
  fi

  if parse_nix_setting "$config_output" 'sandbox'; then
    observed=${NIX_SETTING_VALUE:-'(empty)'}
    if [[ $NIX_SETTING_VALUE == 'true' ]]; then
      add_result "$section" 'sandbox' 'OK' "$observed"
    else
      add_result "$section" 'sandbox' 'WARN' "$observed" 'Set sandbox to true in the effective daemon configuration.'
    fi
  else
    add_result "$section" 'sandbox' 'UNKNOWN' 'Setting was absent or duplicated' 'Inspect the effective Nix daemon configuration.'
  fi

  for key in substituters trusted-public-keys; do
    if parse_nix_setting "$config_output" "$key"; then
      observed=${NIX_SETTING_VALUE:-'(empty)'}
      add_result "$section" "$key" 'OK' "$observed"
    else
      add_result "$section" "$key" 'UNKNOWN' 'Setting was absent or duplicated' 'Inspect the effective Nix daemon configuration.'
    fi
  done
}

get_file_mode() {
  local path=$1
  local stat_command
  local raw_mode

  if ! stat_command=$(command -v stat 2>/dev/null); then
    return 127
  fi

  if ! raw_mode=$("$stat_command" -f '%Lp' "$path" 2>/dev/null); then
    return 1
  fi

  if [[ ! $raw_mode =~ ^([0-7]?)([0-7])([0-7])([0-7])$ ]]; then
    return 2
  fi

  FILE_MODE="0${raw_mode#0}"
  FILE_SPECIAL_MODE=${BASH_REMATCH[1]:-0}
  FILE_OWNER_MODE=${BASH_REMATCH[2]}
  FILE_GROUP_MODE=${BASH_REMATCH[3]}
  FILE_OTHER_MODE=${BASH_REMATCH[4]}
}

check_ssh_directory_mode() {
  local ssh_dir=$1
  local mode_status

  if [[ ! -d $ssh_dir ]]; then
    add_result 'Credentials' 'SSH directory permissions' 'OK' 'Directory absent'
    return
  fi

  if get_file_mode "$ssh_dir"; then
    if [[ $FILE_SPECIAL_MODE == '0' && $FILE_GROUP_MODE == '0' && $FILE_OTHER_MODE == '0' ]]; then
      add_result 'Credentials' 'SSH directory permissions' 'OK' "$FILE_MODE"
    else
      add_result 'Credentials' 'SSH directory permissions' 'WARN' "$FILE_MODE" 'Restrict the directory mode to 0700 or less permissive.'
    fi
  else
    mode_status=$?
    if ((mode_status == 127)); then
      add_result 'Credentials' 'SSH directory permissions' 'UNKNOWN' 'stat is unavailable' 'Restore access to stat and rerun the audit.'
    else
      add_result 'Credentials' 'SSH directory permissions' 'UNKNOWN' 'File mode could not be determined' 'Inspect the directory permissions manually.'
    fi
  fi
}

check_private_key_mode() {
  local key_path=$1
  local key_name="SSH key ${key_path##*/}"
  local mode_status

  if get_file_mode "$key_path"; then
    if [[ $FILE_SPECIAL_MODE == '0' && $FILE_OWNER_MODE =~ ^[0246]$ && $FILE_GROUP_MODE == '0' && $FILE_OTHER_MODE == '0' ]]; then
      add_result 'Credentials' 'SSH private key permissions' 'OK' "$key_name mode $FILE_MODE"
    else
      add_result 'Credentials' 'SSH private key permissions' 'WARN' "$key_name mode $FILE_MODE" 'Restrict the private key mode to 0600 or less permissive.'
    fi
  else
    mode_status=$?
    if ((mode_status == 127)); then
      add_result 'Credentials' 'SSH private key permissions' 'UNKNOWN' "$key_name; stat is unavailable" 'Restore access to stat and rerun the audit.'
    else
      add_result 'Credentials' 'SSH private key permissions' 'UNKNOWN' "$key_name; mode unavailable" 'Inspect the private key permissions manually.'
    fi
  fi
}

check_ssh_keys() {
  local ssh_dir
  local ssh_keygen=''
  local candidate
  local key_name
  local -a candidates=()
  local -a private_keys=()

  if [[ -z ${HOME:-} ]]; then
    add_result 'Credentials' 'SSH directory permissions' 'UNKNOWN' 'HOME is unset' 'Run the audit from a normal user session.'
    add_result 'Credentials' 'SSH private keys' 'UNKNOWN' 'HOME is unset' 'Run the audit from a normal user session.'
    return
  fi

  ssh_dir="$HOME/.ssh"
  check_ssh_directory_mode "$ssh_dir"

  if [[ ! -d $ssh_dir ]]; then
    add_result 'Credentials' 'SSH private keys' 'OK' 'No private keys with matching .pub files'
    return
  fi

  if [[ ! -r $ssh_dir || ! -x $ssh_dir ]]; then
    add_result 'Credentials' 'SSH private keys' 'UNKNOWN' 'The SSH directory is not readable' 'Review the directory permissions and rerun the audit.'
    return
  fi

  shopt -s dotglob nullglob
  candidates=("$ssh_dir"/*)
  shopt -u dotglob nullglob

  for candidate in "${candidates[@]}"; do
    if [[ -f $candidate && -f "${candidate}.pub" ]]; then
      private_keys[${#private_keys[@]}]=$candidate
    fi
  done

  if ((${#private_keys[@]} == 0)); then
    add_result 'Credentials' 'SSH private keys' 'OK' 'No private keys with matching .pub files'
    return
  fi

  if ssh_keygen=$(command -v ssh-keygen 2>/dev/null); then
    :
  fi

  for candidate in "${private_keys[@]}"; do
    key_name="SSH key ${candidate##*/}"
    if [[ -z $ssh_keygen ]]; then
      add_result 'Credentials' 'SSH private key encryption' 'UNKNOWN' "$key_name; ssh-keygen is unavailable" 'Restore access to ssh-keygen and rerun the audit.'
    elif "$ssh_keygen" -y -P '' -f "$candidate" >/dev/null 2>&1; then
      add_result 'Credentials' 'SSH private key encryption' 'WARN' "$key_name accepts an empty passphrase" 'Protect the private key with a passphrase.'
    else
      add_result 'Credentials' 'SSH private key encryption' 'OK' "$key_name rejects an empty passphrase"
    fi

    check_private_key_mode "$candidate"
  done
}

read_git_config() {
  local git_command=$1
  local key=$2
  local output
  local status

  if output=$("$git_command" config --global --get "$key" 2>/dev/null); then
    GIT_CONFIG_STATE='set'
    GIT_CONFIG_VALUE=$output
    return
  else
    status=$?
  fi

  if ((status == 1)); then
    GIT_CONFIG_STATE='unset'
    GIT_CONFIG_VALUE=''
  else
    GIT_CONFIG_STATE='unknown'
    GIT_CONFIG_VALUE=''
  fi
}

check_git_signing() {
  local git_command
  local normalized_value

  if ! git_command=$(command -v git 2>/dev/null); then
    add_result 'Credentials' 'commit.gpgsign' 'UNKNOWN' 'git is unavailable' 'Restore access to git and rerun the audit.'
    add_result 'Credentials' 'gpg.format' 'UNKNOWN' 'git is unavailable' 'Restore access to git and rerun the audit.'
    add_result 'Credentials' 'user.signingkey' 'UNKNOWN' 'git is unavailable' 'Restore access to git and rerun the audit.'
    return
  fi

  read_git_config "$git_command" 'commit.gpgsign'
  if [[ $GIT_CONFIG_STATE == 'set' ]]; then
    case "$GIT_CONFIG_VALUE" in
    true | yes | on | 1)
      add_result 'Credentials' 'commit.gpgsign' 'OK' "$GIT_CONFIG_VALUE"
      ;;
    false | no | off | 0)
      add_result 'Credentials' 'commit.gpgsign' 'WARN' "$GIT_CONFIG_VALUE" 'Enable Git commit signing.'
      ;;
    *)
      add_result 'Credentials' 'commit.gpgsign' 'UNKNOWN' "$GIT_CONFIG_VALUE" 'The Git boolean value was not recognized.'
      ;;
    esac
  elif [[ $GIT_CONFIG_STATE == 'unset' ]]; then
    add_result 'Credentials' 'commit.gpgsign' 'WARN' '(unset; defaults to false)' 'Enable Git commit signing.'
  else
    add_result 'Credentials' 'commit.gpgsign' 'UNKNOWN' 'Git configuration could not be read' 'Inspect the global Git configuration.'
  fi

  read_git_config "$git_command" 'gpg.format'
  if [[ $GIT_CONFIG_STATE == 'set' ]]; then
    trim_whitespace "$GIT_CONFIG_VALUE"
    normalized_value=$TRIMMED_VALUE
    case "$normalized_value" in
    openpgp | x509 | ssh)
      add_result 'Credentials' 'gpg.format' 'OK' "$normalized_value"
      ;;
    *)
      add_result 'Credentials' 'gpg.format' 'UNKNOWN' "$GIT_CONFIG_VALUE" 'The Git signing format was not recognized.'
      ;;
    esac
  elif [[ $GIT_CONFIG_STATE == 'unset' ]]; then
    add_result 'Credentials' 'gpg.format' 'OK' 'openpgp (default)'
  else
    add_result 'Credentials' 'gpg.format' 'UNKNOWN' 'Git configuration could not be read' 'Inspect the global Git configuration.'
  fi

  read_git_config "$git_command" 'user.signingkey'
  if [[ $GIT_CONFIG_STATE == 'set' && -n $GIT_CONFIG_VALUE ]]; then
    add_result 'Credentials' 'user.signingkey' 'OK' "$GIT_CONFIG_VALUE"
  elif [[ $GIT_CONFIG_STATE == 'unset' ]] || [[ $GIT_CONFIG_STATE == 'set' && -z $GIT_CONFIG_VALUE ]]; then
    add_result 'Credentials' 'user.signingkey' 'WARN' '(unset)' 'Configure the public key used for Git commit signing.'
  else
    add_result 'Credentials' 'user.signingkey' 'UNKNOWN' 'Git configuration could not be read' 'Inspect the global Git configuration.'
  fi
}

check_github_cli_credentials() {
  local config_home
  local hosts_file
  local mode_status

  if [[ -n ${XDG_CONFIG_HOME:-} ]]; then
    config_home=$XDG_CONFIG_HOME
  elif [[ -n ${HOME:-} ]]; then
    config_home="$HOME/.config"
  else
    add_result 'Credentials' 'GitHub CLI credential storage' 'UNKNOWN' 'Configuration home could not be resolved' 'Run the audit from a normal user session.'
    return
  fi

  hosts_file="$config_home/gh/hosts.yml"
  if [[ ! -e $hosts_file && ! -L $hosts_file ]]; then
    add_result 'Credentials' 'GitHub CLI credential storage' 'OK' 'Absent'
    return
  fi

  if get_file_mode "$hosts_file"; then
    if [[ $FILE_SPECIAL_MODE == '0' && $FILE_OWNER_MODE =~ ^[0246]$ && $FILE_GROUP_MODE == '0' && $FILE_OTHER_MODE == '0' ]]; then
      add_result 'Credentials' 'GitHub CLI credential storage' 'OK' "Present; mode $FILE_MODE"
    else
      add_result 'Credentials' 'GitHub CLI credential storage' 'WARN' "Present; mode $FILE_MODE" 'Restrict hosts.yml to mode 0600 or less permissive.'
    fi
  else
    mode_status=$?
    if ((mode_status == 127)); then
      add_result 'Credentials' 'GitHub CLI credential storage' 'UNKNOWN' 'Present; stat is unavailable' 'Restore access to stat and rerun the audit.'
    else
      add_result 'Credentials' 'GitHub CLI credential storage' 'UNKNOWN' 'Present; mode unavailable' 'Inspect the file permissions manually.'
    fi
  fi
}

render_table() {
  local current_section=''
  local index
  local guidance
  local first_section=1

  for ((index = 0; index < ${#RESULT_NAMES[@]}; index++)); do
    if [[ ${RESULT_SECTIONS[index]} != "$current_section" ]]; then
      current_section=${RESULT_SECTIONS[index]}
      if ((first_section == 0)); then
        printf '\n'
      fi
      printf '[%s]\n' "$current_section"
      printf '%-32s | %-7s | %-36s | %s\n' 'CHECK' 'STATUS' 'OBSERVED' 'GUIDANCE'
      printf '%-32s-+-%-7s-+-%-36s-+-%s\n' '--------------------------------' '-------' '------------------------------------' '--------'
      first_section=0
    fi

    display_value "${RESULT_NAMES[index]}"
    printf '%-32s | ' "$DISPLAY_VALUE"
    printf '%-7s | ' "${RESULT_STATUSES[index]}"
    display_value "${RESULT_OBSERVED[index]}"
    printf '%-36s | ' "$DISPLAY_VALUE"
    guidance=${RESULT_GUIDANCE[index]}
    display_value "$guidance"
    printf '%s\n' "$DISPLAY_VALUE"
  done
}

render_json() {
  local index
  local separator=''
  local section
  local name
  local status
  local observed
  local guidance

  printf '['
  for ((index = 0; index < ${#RESULT_NAMES[@]}; index++)); do
    json_escape "${RESULT_SECTIONS[index]}"
    section=$JSON_ESCAPED
    json_escape "${RESULT_NAMES[index]}"
    name=$JSON_ESCAPED
    json_escape "${RESULT_STATUSES[index]}"
    status=$JSON_ESCAPED
    json_escape "${RESULT_OBSERVED[index]}"
    observed=$JSON_ESCAPED
    json_escape "${RESULT_GUIDANCE[index]}"
    guidance=$JSON_ESCAPED

    printf '%s{"section":"%s","check":"%s","status":"%s","observed":"%s","guidance":"%s"}' \
      "$separator" "$section" "$name" "$status" "$observed" "$guidance"
    separator=','
  done
  printf ']\n'
}

check_filevault
check_sip
add_result 'Boot and disk' 'Secure Boot policy' 'MANUAL' 'Elevation required' 'sudo bputil -d'
check_gatekeeper

check_firewall_value 'Application firewall' '--getglobalstate' 'Firewall is enabled' 'Firewall is disabled' 'Enable the application firewall in System Settings > Network > Firewall.'
check_firewall_value 'Firewall stealth mode' '--getstealthmode' 'stealth mode is on' 'stealth mode is off' 'Enable stealth mode in the application firewall options.'
check_firewall_value 'Firewall block-all' '--getblockall' 'block all state set to enabled' 'block all state set to disabled' 'Enable block-all mode if the resulting service restrictions are acceptable.'
add_result 'Network' 'Remote login / Apple Remote Desktop' 'MANUAL' 'Elevation required' 'sudo systemsetup -getremotelogin'

check_system_extensions
check_launch_agents
add_result 'Declared-vs-actual drift' 'Configuration profiles' 'MANUAL' 'Elevation required' 'sudo profiles list -type configuration'
add_result 'Declared-vs-actual drift' 'TCC grants' 'MANUAL' 'Full Disk Access is required to inspect TCC' 'Review System Settings > Privacy & Security; do not read TCC.db from this audit.'

check_nix_trust_boundary

check_ssh_keys
check_git_signing
check_github_cli_credentials

if ((JSON_OUTPUT == 1)); then
  render_json
else
  render_table
fi

if ((STRICT_MODE == 1 && WARN_COUNT > 0)); then
  exit 1
fi

exit 0
