#!/usr/bin/env bash

sync_opencode_plugins() {
  local plugins_src="$1"
  local plugins_dest="$2"

  if [[ -L $plugins_dest && ! -d $plugins_dest ]]; then
    printf 'OpenCode plugins path is a non-directory symlink: %s\n' "$plugins_dest" >&2
    return 1
  fi

  $DRY_RUN_CMD mkdir -p "$plugins_dest"

  for src_file in "$plugins_src"/*; do
    [[ -f $src_file ]] || continue
    local base
    base="$(basename "$src_file")"
    local dest_file="$plugins_dest/$base"
    if [[ -L $dest_file ]]; then
      printf 'OpenCode plugin destination is a symlink: %s\n' "$dest_file" >&2
      return 1
    fi
    if [[ -f $dest_file ]] && diff -q "$src_file" "$dest_file" >/dev/null 2>&1; then
      continue
    fi
    $DRY_RUN_CMD cp -fL "$src_file" "$dest_file"
    $DRY_RUN_CMD chmod u+w "$dest_file"
  done
}
