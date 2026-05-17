#!/usr/bin/env bash
set -euo pipefail

staged_files="$(git diff --cached --name-only --diff-filter=ACMR)"

while IFS= read -r file_path; do
  case "$file_path" in
    flake.local.nix|*/flake.local.nix|local/identity.nix|*/local/identity.nix)
      printf 'ERROR: local identity/override file is staged (%s).\n' "$file_path" >&2
      printf 'Please unstage it with: git restore --staged "%s"\n' "$file_path" >&2
      exit 1
      ;;
  esac
done <<< "$staged_files"
