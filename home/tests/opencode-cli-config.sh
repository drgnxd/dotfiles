#!/usr/bin/env bash
# shellcheck disable=SC1091,SC2016 # jq keys and JSON stay literal
set -euo pipefail

source "$(dirname "$0")/../modules/activation/sync_opencode_cli_config.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp:?}"' EXIT

jaq="${JAQ:-$(command -v jaq)}"
template="$tmp/template.json"
target="$tmp/config/cli.json"
printf '{"$schema":"https://opencode.ai/v2/cli.json","theme":{"name":"managed"}}\n' >"$template"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}
value() { "$jaq" -r "$1" "$target"; }

sync_opencode_cli_config "$jaq" "$template" "$target"
[[ "$(value .theme.name)" == managed ]] || fail 'missing target was not created from the template'

printf '{"theme":{"name":"other","mode":"dark"},"diffs":{"wrap":"word"},"animations":true}\n' >"$target"
sync_opencode_cli_config "$jaq" "$template" "$target"
[[ "$(value .theme.name)" == managed ]] || fail 'managed theme was not enforced'
[[ "$(value .theme.mode)" == dark ]] || fail 'sibling theme key was lost'
[[ "$(value .diffs.wrap)" == word && "$(value .animations)" == true ]] || fail 'user preference was lost'
[[ "$(value '.["$schema"]')" == https://opencode.ai/v2/cli.json ]] || fail 'schema was not added'

printf '{not json\n' >"$target"
sync_opencode_cli_config "$jaq" "$template" "$target" 2>/dev/null
[[ "$(<"$target")" == '{not json' ]] || fail 'invalid target was modified'
[[ -z "$(find "$tmp/config" -name '*.tmp.*')" ]] || fail 'temp file left behind'
printf 'OK\n'
