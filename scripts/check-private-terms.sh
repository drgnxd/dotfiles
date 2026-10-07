#!/usr/bin/env bash
# Scans for private terms (service names, job names, host names) that must not
# reach this public repository. The pattern list lives outside the repository,
# one extended regex per line, so the terms themselves are never published.
# Matched text is never printed: output could be pasted into a PR or issue.
#
# Usage:
#   check-private-terms.sh files            tracked file names and contents
#   check-private-terms.sh message <file>   a commit message file
#   check-private-terms.sh push             commits, added lines, and ref names about to be pushed
set -euo pipefail

terms_file="${DOTFILES_PRIVATE_TERMS:-${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles-private/public-boundary-terms}"

if [ ! -r "$terms_file" ]; then
  # CI and the Nix sandbox cannot hold the private list; a developer shell must.
  if [ -n "${CI:-}" ] || [ -n "${NIX_BUILD_TOP:-}" ]; then
    printf 'NOTICE: private term list not available here; skipping.\n' >&2
    exit 0
  fi
  printf 'ERROR: private term list is missing: %s\n' "$terms_file" >&2
  exit 1
fi

patterns="$(mktemp)"
trap 'rm -f "$patterns"' EXIT
grep -v -E '^[[:space:]]*(#|$)' "$terms_file" >"$patterns" || true
if [ ! -s "$patterns" ]; then
  printf 'ERROR: private term list has no patterns: %s\n' "$terms_file" >&2
  exit 1
fi

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

has_term() {
  grep -q -i -E -f "$patterns"
}

case "${1:-}" in
files)
  git ls-files | has_term && fail "a tracked file name contains a private term"
  hits="$(git grep -l -I -i -E -f "$patterns" -- . || true)"
  if [ -n "$hits" ]; then
    printf '%s\n' "$hits" >&2
    fail "tracked files above contain a private term"
  fi
  ;;
message)
  [ -n "${2:-}" ] || fail "message mode needs a file"
  sed '/^# -* >8 -*$/,$d' "$2" | grep -v '^#' | has_term && fail "the commit message contains a private term"
  ;;
push)
  to="${PRE_COMMIT_TO_REF:-HEAD}"
  from="${PRE_COMMIT_FROM_REF:-}"
  if [ -z "$from" ] || [ "$from" = "0000000000000000000000000000000000000000" ]; then
    from="$(git rev-parse --verify -q '@{upstream}' || git rev-parse --verify -q origin/main || true)"
  fi
  [ -n "$from" ] || fail "cannot determine the range being pushed"
  range="$from..$to"
  git log --format='%B%n%an%n%ae%n%cn%n%ce' "$range" | has_term && fail "a pushed commit message or identity contains a private term"
  git log -p --format= --no-color "$range" | grep -E '^(\+|diff --git)' | has_term && fail "a pushed change adds a private term"
  printf '%s\n%s\n' "${PRE_COMMIT_LOCAL_BRANCH:-}" "${PRE_COMMIT_REMOTE_BRANCH:-}" | has_term && fail "the pushed ref name contains a private term"
  ;;
*)
  fail "usage: check-private-terms.sh files | message <file> | push"
  ;;
esac

printf '%s\n' 'OK: no private terms found.'
