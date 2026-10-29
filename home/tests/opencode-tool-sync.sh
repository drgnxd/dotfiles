#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$repo_root/home/modules/activation/sync_opencode_tools.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp:?}"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

args_file="$tmp/args"
fake_python="$tmp/fake-python"
helper="$tmp/helper.py"
mkdir -p "$tmp/source tree"
printf 'not executed\n' >"$helper"
cat >"$fake_python" <<'EOF'
#!/bin/sh
: >"$ARGS_FILE"
for arg in "$@"; do
  printf '%s\n' "$arg" >>"$ARGS_FILE"
done
EOF
chmod u+x "$fake_python"

ARGS_FILE="$args_file" sync_opencode_tools \
  "$fake_python" \
  "$helper" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  echo
grep -Fxq "$helper" "$args_file" || fail 'dry-run omitted helper path'
grep -Fxq -- '--mapping-id' "$args_file" || fail 'dry-run omitted mapping ID option'
grep -Fxq 'dotfiles-opencode-tools' "$args_file" || fail 'dry-run omitted stable mapping ID'
grep -Fxq "$tmp/source tree" "$args_file" || fail 'dry-run split source path'
grep -Fxq "$tmp/destination tree" "$args_file" || fail 'dry-run split destination path'
grep -Fxq "$tmp/state tree" "$args_file" || fail 'dry-run split state path'
grep -Fxq -- '--dry-run' "$args_file" || fail 'dry-run option was not forwarded'
if grep -Fxq -- '--external-writers-quiesced' "$args_file"; then
  fail 'dry-run asserted writer quiescence'
fi

OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED=1 ARGS_FILE="$args_file" sync_opencode_tools \
  "$fake_python" \
  "$helper" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  echo
grep -Fxq -- '--dry-run' "$args_file" || fail 'activation dry-run was bypassed by a quiescence attestation'
if grep -Fxq -- '--external-writers-quiesced' "$args_file"; then
  fail 'activation dry-run asserted writer quiescence'
fi

unset OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED || true
if ARGS_FILE="$args_file" sync_opencode_tools \
  "$fake_python" \
  "$helper" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  "" 2>"$tmp/no-attestation-error"; then
  :
else
  fail 'missing quiescence attestation prevented safe dry-run'
fi
grep -Fxq -- '--dry-run' "$args_file" || fail 'activation mutated without a quiescence attestation'
grep -q 'OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED=1' "$tmp/no-attestation-error" || fail 'default dry-run lacked an explicit explanation'

OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED=1 ARGS_FILE="$args_file" sync_opencode_tools \
  "$fake_python" \
  "$helper" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  ""
grep -Fxq -- '--external-writers-quiesced' "$args_file" || fail 'mutation did not assert writer quiescence'
if grep -Fxq -- '--dry-run' "$args_file"; then
  fail 'mutation unexpectedly used dry-run'
fi

OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED=invalid ARGS_FILE="$args_file" sync_opencode_tools \
  "$fake_python" \
  "$helper" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  ""
grep -Fxq -- '--dry-run' "$args_file" || fail 'invalid quiescence attestation allowed mutation'

missing_args="$tmp/missing-args"
if ARGS_FILE="$missing_args" sync_opencode_tools \
  "$fake_python" \
  "$tmp/missing-helper.py" \
  "dotfiles-opencode-tools" \
  "$tmp/source tree" \
  "$tmp/destination tree" \
  "$tmp/state tree" \
  "" 2>"$tmp/missing-error"; then
  :
else
  fail 'missing optional helper prevented activation'
fi
[ ! -e "$missing_args" ] || fail 'missing helper unexpectedly invoked the interpreter'
grep -q 'preserving destination' "$tmp/missing-error" || fail 'missing helper lacked a diagnostic'

printf 'OpenCode tool sync wrapper tests passed\n'
