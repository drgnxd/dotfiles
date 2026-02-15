#!/usr/bin/env bash
set -euo pipefail

ALLOW_MISSING=0
TARGET="."

PYTHON_FILES=()
SHELL_FILES=()

print_error() {
	printf "ERROR: %s\n" "$*" >&2
}

usage() {
	cat <<'EOF'
Usage: check_style.sh [--allow-missing] [target]

Options:
  --allow-missing  Skip missing linters instead of failing
  -h, --help       Show this help

Target:
  File or directory to lint (default: .)
EOF
}

parse_args() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--allow-missing)
			ALLOW_MISSING=1
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			if [[ "$TARGET" != "." ]]; then
				print_error "Only one target path can be provided"
				exit 1
			fi
			TARGET="$1"
			;;
		esac
		shift
	done
}

collect_files() {
	local target="$1"

	if [[ -f "$target" ]]; then
		case "$target" in
		*.py) PYTHON_FILES+=("$target") ;;
		*.sh) SHELL_FILES+=("$target") ;;
		*)
			print_error "Unsupported file type: $target"
			exit 1
			;;
		esac
		return
	fi

	if [[ ! -d "$target" ]]; then
		print_error "$target not found"
		exit 1
	fi

	while IFS= read -r -d '' file; do
		case "$file" in
		*.py) PYTHON_FILES+=("$file") ;;
		*.sh) SHELL_FILES+=("$file") ;;
		esac
	done < <(find "$target" \
		\( -type d \( -name ".git" -o -name ".venv" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name "__pycache__" \) -prune \) \
		-o \( -type f \( -name "*.py" -o -name "*.sh" \) -print0 \))
}

tool_available_with_uv() {
	local tool="$1"
	uv run "$tool" --version >/dev/null 2>&1
}

run_python_checks() {
	if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
		return
	fi

	printf "Checking %d Python files\n" "${#PYTHON_FILES[@]}"

	local missing_tools=()
	local has_flake8=0
	local has_black=0
	local has_mypy=0

	if ! command -v uv >/dev/null 2>&1; then
		missing_tools+=("uv")
	else
		if tool_available_with_uv "flake8"; then
			has_flake8=1
		else
			missing_tools+=("flake8")
		fi

		if tool_available_with_uv "black"; then
			has_black=1
		else
			missing_tools+=("black")
		fi

		if tool_available_with_uv "mypy"; then
			has_mypy=1
		else
			missing_tools+=("mypy")
		fi
	fi

	if [[ ${#missing_tools[@]} -gt 0 && $ALLOW_MISSING -ne 1 ]]; then
		print_error "Missing Python lint tools: ${missing_tools[*]}"
		print_error "Install tools or run with --allow-missing"
		exit 1
	fi

	if [[ $has_flake8 -eq 1 ]]; then
		uv run flake8 "${PYTHON_FILES[@]}"
	fi

	if [[ $has_black -eq 1 ]]; then
		uv run black --check "${PYTHON_FILES[@]}"
	fi

	if [[ $has_mypy -eq 1 ]]; then
		uv run mypy "${PYTHON_FILES[@]}"
	fi
}

run_shell_checks() {
	if [[ ${#SHELL_FILES[@]} -eq 0 ]]; then
		return
	fi

	printf "Checking %d shell scripts\n" "${#SHELL_FILES[@]}"

	if ! command -v shellcheck >/dev/null 2>&1; then
		if [[ $ALLOW_MISSING -eq 1 ]]; then
			return
		fi
		print_error "Missing shell linter: shellcheck"
		print_error "Install shellcheck or run with --allow-missing"
		exit 1
	fi

	shellcheck "${SHELL_FILES[@]}"
}

main() {
	parse_args "$@"
	collect_files "$TARGET"
	run_python_checks
	run_shell_checks
}

main "$@"
