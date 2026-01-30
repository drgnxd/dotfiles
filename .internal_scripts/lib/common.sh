#!/bin/bash
# common.sh - Shared functions for macOS setup scripts
#
# This library provides common functionality used across all Darwin setup scripts,
# including environment variable guards, logging, and error handling.
#
# Usage:
#   source "${CHEZMOI_SOURCE_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}/.internal_scripts/lib/bootstrap.sh"

set -euo pipefail

# ANSI color codes for terminal output
readonly COLOR_RESET='\033[0m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'

# Global array to track failures (used by security_hardening.sh)
declare -a FAILURES=()

#######################################
# Check if a command exists in PATH.
# Arguments:
#   $1: Command name
# Returns:
#   0 if command exists, 1 otherwise
#######################################
check_command() {
	local cmd=$1
	if ! command -v "$cmd" >/dev/null 2>&1; then
		log_error "Required command '$cmd' not found in PATH"
		return 1
	fi
	return 0
}

#######################################
# Resolve a Brewfile path, rendering template when needed.
# Arguments:
#   $1: Brewfile source path (chezmoi source)
# Outputs:
#   Prints resolved Brewfile path to stdout
# Returns:
#   0 on success, 1 on failure
# Notes:
#   When a template is rendered, RESOLVED_BREWFILE_TMP is set
#######################################
resolve_brewfile() {
	local brewfile_source=$1
	local brewfile_target="${XDG_CONFIG_HOME:-$HOME/.config}/homebrew/Brewfile"
	local brewfile_template="${brewfile_source}.tmpl"
	local tmp_file=""

	if [ -f "$brewfile_target" ]; then
		echo "$brewfile_target"
		return 0
	fi

	if [ -f "$brewfile_source" ]; then
		echo "$brewfile_source"
		return 0
	fi

	if [ -f "$brewfile_template" ]; then
		tmp_file=$(mktemp)
		if chezmoi execute-template <"$brewfile_template" >"$tmp_file"; then
			export RESOLVED_BREWFILE_TMP="$tmp_file"
			echo "$tmp_file"
			return 0
		fi

		log_error "Failed to render Brewfile template"
		rm -f "$tmp_file"
		return 1
	fi

	log_error "Brewfile not found at $brewfile_target, $brewfile_source, or $brewfile_template"
	return 1
}

#######################################
# Require an environment variable flag to be set.
# Exits with status 1 if the flag is not set to "1".
# Arguments:
#   $1: Environment variable name (e.g., "ALLOW_DEFAULTS")
#   $2: Description of what the flag controls (e.g., "macOS defaults modification")
# Outputs:
#   Error message to stderr if flag is not set
#######################################
require_flag() {
	local flag_name=$1
	local description=$2
	local flag_value="${!flag_name:-0}"

	if [ "$flag_value" != "1" ]; then
		log_error "Refusing to proceed without ${flag_name}=1"
		echo "  Set ${flag_name}=1 to allow: ${description}" >&2
		exit 1
	fi

	log_info "Flag ${flag_name} is set - proceeding with: ${description}"
}

#######################################
# Internal: Execute macOS defaults write with flexible options.
# Arguments:
#   $1: Target user (or empty for current user)
#   $2: "current_host" flag ("1" to use -currentHost)
#   $@: Remaining arguments passed to 'defaults write'
# Returns:
#   0 on success, 1 on failure
#######################################
_safe_defaults_write_impl() {
	local target_user=$1
	local use_current_host=$2
	shift 2

	if ! check_command defaults; then
		return 1
	fi

	local defaults_cmd=(defaults)
	[ "$use_current_host" = "1" ] && defaults_cmd+=(-currentHost)
	defaults_cmd+=(write "$@")

	local cmd_str="defaults"
	[ "$use_current_host" = "1" ] && cmd_str+=" -currentHost"
	cmd_str+=" write $*"

	if [ -n "$target_user" ] && [ "$(whoami)" != "$target_user" ]; then
		if ! run_as_user "$target_user" "${defaults_cmd[@]}"; then
			log_error "Failed to execute: $cmd_str (user: $target_user)"
			return 1
		fi
	else
		if ! "${defaults_cmd[@]}"; then
			log_error "Failed to execute: $cmd_str"
			return 1
		fi
	fi
	return 0
}

#######################################
# Execute macOS defaults write with error handling.
# Arguments:
#   $@: All arguments passed to 'defaults write'
# Returns:
#   0 on success, 1 on failure
#######################################
safe_defaults_write() {
	_safe_defaults_write_impl "" "0" "$@"
}

#######################################
# Execute macOS defaults write with -currentHost.
# Arguments:
#   $@: All arguments passed to 'defaults write'
# Returns:
#   0 on success, 1 on failure
#######################################
safe_defaults_write_current_host() {
	_safe_defaults_write_impl "" "1" "$@"
}

#######################################
# Execute macOS defaults write as a specific user.
# Arguments:
#   $1: Username
#   $@: All arguments passed to 'defaults write'
# Returns:
#   0 on success, 1 on failure
#######################################
safe_defaults_write_as_user() {
	local target_user=$1
	shift

	if [ -z "$target_user" ]; then
		log_error "safe_defaults_write_as_user requires a target user"
		return 1
	fi

	_safe_defaults_write_impl "$target_user" "0" "$@"
}

#######################################
# Execute macOS defaults write with -currentHost as a specific user.
# Arguments:
#   $1: Username
#   $@: All arguments passed to 'defaults write'
# Returns:
#   0 on success, 1 on failure
#######################################
safe_defaults_write_current_host_as_user() {
	local target_user=$1
	shift

	if [ -z "$target_user" ]; then
		log_error "safe_defaults_write_current_host_as_user requires a target user"
		return 1
	fi

	_safe_defaults_write_impl "$target_user" "1" "$@"
}

#######################################
# Read a macOS defaults value safely.
# Arguments:
#   $1: Domain
#   $2: Key
# Outputs:
#   Prints the value or "not set" if not found
#######################################
read_defaults() {
	local domain=$1 key=$2
	/usr/bin/defaults read "$domain" "$key" 2>/dev/null || echo "not set"
}

#######################################
# Record a failure for later reporting.
# Appends the failure message to the global FAILURES array.
# Arguments:
#   $1: Failure description
#######################################
record_failure() {
	local message=$1
	FAILURES+=("$message")
	log_error "$message"
}

#######################################
# Report all recorded failures.
# Prints a summary of all failures and exits if any exist.
# Returns:
#   1 if failures exist, 0 otherwise
#######################################
report_failures() {
	if [ ${#FAILURES[@]} -eq 0 ]; then
		log_success "All operations completed successfully"
		return 0
	fi

	echo ""
	log_error "The following operations failed:"
	for failure in "${FAILURES[@]}"; do
		echo "  - $failure" >&2
	done
	echo ""
	return 1
}

#######################################
# Log an informational message.
# Arguments:
#   $1: Message to log
#######################################
log_info() {
	echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

#######################################
# Log a success message.
# Arguments:
#   $1: Message to log
#######################################
log_success() {
	echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

#######################################
# Log a warning message.
# Arguments:
#   $1: Message to log
#######################################
log_warning() {
	echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1" >&2
}

#######################################
# Log an error message.
# Arguments:
#   $1: Message to log
#######################################
log_error() {
	echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1" >&2
}

#######################################
# Quit a macOS application if it's running.
# Arguments:
#   $1: Application name
# Outputs:
#   Warning if osascript unavailable or app fails to quit
#######################################
quit_app() {
	local app_name=$1

	if ! command -v osascript >/dev/null 2>&1; then
		log_warning "osascript not available, cannot quit $app_name"
		return 1
	fi

	if ! osascript -e "tell application \"$app_name\" to quit" 2>/dev/null; then
		log_info "App '$app_name' not running or already quit"
		return 0
	fi

	log_info "Quit application: $app_name"
	return 0
}

#######################################
# Kill a macOS process by name (for applying changes).
# Arguments:
#   $1: Process name
# Outputs:
#   Info message on success or if process not found
#######################################
kill_process() {
	local process_name=$1

	if ! command -v killall >/dev/null 2>&1; then
		log_warning "killall not available, cannot kill $process_name"
		return 1
	fi

	if pgrep -x "$process_name" >/dev/null 2>&1; then
		if killall "$process_name" 2>/dev/null; then
			log_info "Restarted process: $process_name"
			return 0
		else
			log_warning "Failed to kill process: $process_name"
			return 1
		fi
	else
		log_info "Process '$process_name' not running"
		return 0
	fi
}

#######################################
# Get the current console user.
# Returns:
#   Username of the console user
#######################################
get_console_user() {
	stat -f %Su /dev/console
}

#######################################
# Check if running on macOS.
# Returns:
#   0 if macOS, 1 otherwise
#######################################
is_macos() {
	[[ "$(uname -s)" == "Darwin" ]]
}

#######################################
# Execute a command as a specific user.
# Arguments:
#   $1: Username
#   $@: Command and arguments to execute
#######################################
run_as_user() {
	local target_user=$1
	shift

	if [ "$(whoami)" != "$target_user" ]; then
		sudo -u "$target_user" "$@"
	else
		"$@"
	fi
}
