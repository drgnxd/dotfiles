#!/usr/bin/env bash
set -euo pipefail

errors=0

while IFS= read -r -d '' file_path; do
  case "$file_path" in
  scripts/security/external-agents.local)
    printf 'ERROR: machine-local file is tracked: %s\n' "$file_path" >&2
    errors=$((errors + 1))
    ;;
  *.local | local/*.nix)
    printf 'ERROR: machine-local file is tracked: %s\n' "$file_path" >&2
    errors=$((errors + 1))
    ;;
  esac
done < <(git ls-files -z)

# Concrete home/repository paths are machine-local data even when they are not
# credentials, and are easy to copy into public documentation accidentally.
if git grep -nE '(^|[^$[:alnum:]])(/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|~/repos/[A-Za-z0-9._-]+/)' -- ':!local/**' >/dev/null; then
  printf 'ERROR: tracked files contain a concrete local home or repository path\n' >&2
  errors=$((errors + 1))
fi

if [ "$errors" -gt 0 ]; then
  exit 1
fi

printf '%s\n' 'OK: tracked files stay within the public repository boundary.'
