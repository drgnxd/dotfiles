#!/usr/bin/env bash
# UV enforcement checker for Python projects

set -euo pipefail

readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[1;33m'
readonly COLOR_RESET='\033[0m'

print_error() {
	printf "%b\n" "${COLOR_RED}ERROR${COLOR_RESET} $*"
}

print_ok() {
	printf "%b\n" "${COLOR_GREEN}OK${COLOR_RESET} $*"
}

print_warn() {
	printf "%b\n" "${COLOR_YELLOW}WARN${COLOR_RESET} $*"
}

check_uv_installed() {
	if ! command -v uv >/dev/null 2>&1; then
		print_error "uv is not installed"
		printf "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh\n"
		return 1
	fi
	print_ok "uv is installed"
	return 0
}

grep_matches() {
	local target="$1"
	local pattern="$2"

	grep -R -n \
		--include="*.sh" \
		--include="*.py" \
		--include="Makefile" \
		--exclude="check_uv_usage.sh" \
		--exclude-dir=".git" \
		--exclude-dir=".venv" \
		"${pattern}" "${target}" 2>/dev/null || true
}

filter_actionable_lines() {
	local matches="$1"

	if [[ -z "${matches}" ]]; then
		return 0
	fi

	printf "%s\n" "${matches}" |
		grep -v -E ':[[:space:]]*@?(echo|printf)\b' |
		grep -v -E ':[[:space:]]*#' || true
}

check_forbidden_commands() {
	local target="${1:-.}"
	local found_issues=0
	local matches=""

	printf "Checking for forbidden pip/venv commands in: %s\n" "${target}"

	matches="$(grep_matches "${target}" "pip install")"
	matches="$(filter_actionable_lines "${matches}")"
	if [[ -n "${matches}" ]]; then
		matches="$(printf "%s\n" "${matches}" | grep -v -E '(^|[[:space:]]|@)uv[[:space:]]+pip[[:space:]]+install' || true)"
	fi
	if [[ -n "${matches}" ]]; then
		print_error "Found 'pip install' - use 'uv pip install' instead"
		printf "%s\n" "${matches}"
		found_issues=1
	fi

	matches="$(grep_matches "${target}" "python -m venv")"
	matches="$(filter_actionable_lines "${matches}")"
	if [[ -n "${matches}" ]]; then
		print_error "Found 'python -m venv' - use 'uv venv' instead"
		printf "%s\n" "${matches}"
		found_issues=1
	fi

	matches="$(grep_matches "${target}" "virtualenv")"
	matches="$(filter_actionable_lines "${matches}")"
	if [[ -n "${matches}" ]]; then
		print_error "Found 'virtualenv' - use 'uv venv' instead"
		printf "%s\n" "${matches}"
		found_issues=1
	fi

	if [[ ${found_issues} -eq 0 ]]; then
		print_ok "No forbidden commands found"
	fi

	return ${found_issues}
}

suggest_uv_alternatives() {
	printf "\n"
	print_warn "UV command reference:"
	printf "  pip install <pkg>           -> uv pip install <pkg>\n"
	printf "  pip install -r requirements -> uv pip install -r requirements.txt\n"
	printf "  python -m venv .venv        -> uv venv\n"
	printf "  python script.py            -> uv run script.py\n"
	printf "  pip freeze > requirements   -> uv pip freeze > requirements.txt\n"
}

main() {
	local target="${1:-.}"
	local exit_code=0

	printf "=== UV Enforcement Check ===\n\n"

	if ! check_uv_installed; then
		exit_code=1
	fi

	printf "\n"

	if ! check_forbidden_commands "${target}"; then
		exit_code=1
		suggest_uv_alternatives
	fi

	printf "\n"

	if [[ ${exit_code} -eq 0 ]]; then
		print_ok "All checks passed"
	else
		print_error "Some checks failed"
	fi

	return ${exit_code}
}

main "$@"
