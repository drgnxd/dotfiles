#!/bin/bash
set -euo pipefail

REQUIRED_COMMANDS=(chezmoi git uv nu task)
MISSING=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		MISSING+=("$cmd")
	fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
	echo "Missing commands: ${MISSING[*]}" >&2
	echo "Install via: brew bundle install" >&2
	exit 1
fi

echo "All dependencies satisfied"
