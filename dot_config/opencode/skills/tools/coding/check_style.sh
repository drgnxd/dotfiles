#!/usr/bin/env bash
set -euo pipefail

check_python() {
	local file="$1"

	echo "Checking Python file: $file"

	if uv run flake8 --version >/dev/null 2>&1; then
		uv run flake8 "$file"
	fi

	if uv run black --version >/dev/null 2>&1; then
		uv run black --check "$file"
	fi

	if uv run mypy --version >/dev/null 2>&1; then
		uv run mypy "$file"
	fi
}

check_shell() {
	local file="$1"

	echo "Checking shell script: $file"

	if command -v shellcheck >/dev/null 2>&1; then
		shellcheck "$file"
	fi
}

main() {
	local target="${1:-.}"

	if [[ -f "$target" ]]; then
		case "$target" in
		*.py) check_python "$target" ;;
		*.sh) check_shell "$target" ;;
		*) echo "Unknown file type: $target" ;;
		esac
	elif [[ -d "$target" ]]; then
		while IFS= read -r file; do
			case "$file" in
			*.py) check_python "$file" ;;
			*.sh) check_shell "$file" ;;
			esac
		done < <(find "$target" -type f \( -name "*.py" -o -name "*.sh" \))
	else
		echo "Error: $target not found"
		exit 1
	fi
}

main "$@"
