#!/usr/bin/env bash

# Enforce the managed keys of OpenCode's cli.json and keep every other key.
#
# OpenCode v2 reads CLI settings from cli.json and rewrites it with the user's
# persisted preferences, so the file cannot be a read-only store symlink. Only
# the keys present in the template are set; an unreadable target is kept as is.
# A symlinked target belongs to the user and is left alone.

sync_opencode_cli_config() {
  local jaq="$1" template="$2" target="$3" merged

  if [[ -n ${DRY_RUN_CMD:-} ]]; then
    printf 'would sync managed keys into %s\n' "$target" >&2
    return 0
  fi
  if [[ -L $target ]]; then
    echo "warning: $target is a symlink; leaving it unmanaged" >&2
    return 0
  fi

  mkdir -p "$(dirname "$target")"
  if [[ ! -s $target ]]; then
    cp -f "$template" "$target"
    chmod u+w "$target"
    return 0
  fi

  merged="$target.tmp.$$"
  # The jaq program must stay literal.
  # shellcheck disable=SC2016
  if "$jaq" --slurpfile managed "$template" --slurpfile current "$target" -n '
    def deepmerge($base; $override):
      if ($base | type) != "object" or ($override | type) != "object"
      then $override
      else reduce ($override | keys_unsorted[]) as $key ($base;
        .[$key] = deepmerge(.[$key]; $override[$key])
      )
      end;
    deepmerge($current[0]; $managed[0])
  ' >"$merged" 2>/dev/null; then
    if ! cmp -s "$merged" "$target"; then
      mv -f "$merged" "$target"
    else
      rm -f "$merged"
    fi
    chmod u+w "$target"
  else
    rm -f "$merged"
    echo "warning: $target could not be merged (invalid JSON?); keeping it as is" >&2
  fi
}
