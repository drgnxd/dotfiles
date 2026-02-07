#!/bin/bash
set -euo pipefail

FORCE=${FORCE:-0}
CLOUD_DIR="$HOME/Library/CloudStorage"
HOME_DIR="$HOME"

if [ ! -d "$CLOUD_DIR" ]; then
	echo "CloudStorage directory not found: $CLOUD_DIR"
	echo "Skipping cloud symlink setup"
	exit 0
fi

if [ "$FORCE" != "1" ]; then
	echo "Refusing to proceed without FORCE=1" >&2
	echo "Set FORCE=1 to allow cloud storage symlink creation" >&2
	exit 1
fi

echo "Checking CloudStorage directories..."

for target in "$CLOUD_DIR"/*; do
	if [ -d "$target" ]; then
		default_name=$(basename "$target")

		if [ -c /dev/tty ]; then
			echo "---------------------------------------------------"
			echo "Found: $default_name"
			echo -n "Create symlink for '$default_name'? [y/N]: "
			read -r answer </dev/tty

			case "$answer" in
			[yY]*)
				echo -n "Enter link name [default: $default_name]: "
				read -r input_name </dev/tty

				link_name="${input_name:-$default_name}"
				link_path="$HOME_DIR/$link_name"

				if [ -e "$link_path" ] && [ ! -L "$link_path" ]; then
					echo "Path exists and is not a symlink: $link_path" >&2
					echo "Move or remove it before creating a symlink" >&2
					continue
				fi

				if ln -sFn "$target" "$link_path"; then
					echo "Created: $link_path -> $target"
				else
					echo "Failed to create symlink: $link_path -> $target" >&2
				fi
				;;
			*)
				echo "Skipped: $default_name"
				;;
			esac
		else
			echo "No TTY available, cannot prompt for '$default_name'" >&2
			echo "Run this script in an interactive terminal to create symlinks" >&2
		fi
	fi
done
