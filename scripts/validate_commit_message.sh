#!/usr/bin/env sh

set -eu

LC_ALL=C
export LC_ALL

if [ "$#" -ne 1 ] || [ ! -r "$1" ]; then
  printf '%s\n' "commit-message: expected one readable commit-message file" >&2
  exit 1
fi

header="$(sed -n '1p' "$1")"
pattern='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\([a-z0-9][a-z0-9/-]*\))?!?: [a-z][A-Za-z0-9 ,:;!?()/_+-]*[^.]$'

if ! printf '%s\n' "$header" | grep -Eq "$pattern"; then
  printf '%s\n' "commit-message: header must follow docs/COMMIT_CONVENTION.md" >&2
  printf '%s\n' "expected: fix(scope): describe the change" >&2
  exit 1
fi
