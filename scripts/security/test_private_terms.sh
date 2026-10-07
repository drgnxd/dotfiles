#!/usr/bin/env bash
set -euo pipefail

script="$(cd "$(dirname "$0")/.." && pwd)/check-private-terms.sh"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cd "$work"
git init -q .
git config user.name tester
git config user.email tester@example.invalid
printf '%s\n' '# comment' '' '(^|[^a-z])zzsecret([^a-z]|$)' >terms
export DOTFILES_PRIVATE_TERMS="$work/terms"

expect_fail() {
  if "$@" >/dev/null 2>&1; then
    printf 'FAIL: expected failure: %s\n' "$*" >&2
    exit 1
  fi
}

printf 'clean\n' >a.txt
git add a.txt
"$script" files >/dev/null

printf 'has ZZ-Secret?\nzzsecret here\n' >b.txt
git add b.txt
expect_fail "$script" files
git rm -q -f b.txt

printf 'nozzsecretx\n' >c.txt
git add c.txt
"$script" files >/dev/null
git rm -q -f c.txt

git add -A
printf 'subject\n\n# On branch zzsecret-branch\n# ------------------------ >8 ------------------------\nzzsecret\n' >msg
"$script" message msg >/dev/null
printf 'subject zzsecret\n' >msg
expect_fail "$script" message msg

git commit -q -m base
base="$(git rev-parse HEAD)"
printf 'zzsecret\n' >d.txt
git add d.txt
git commit -q -m "add file"
PRE_COMMIT_FROM_REF="$base" PRE_COMMIT_TO_REF=HEAD expect_fail "$script" push

DOTFILES_PRIVATE_TERMS="$work/missing" expect_fail "$script" files
CI=1 DOTFILES_PRIVATE_TERMS="$work/missing" "$script" files >/dev/null

printf 'test_private_terms: ok\n'
