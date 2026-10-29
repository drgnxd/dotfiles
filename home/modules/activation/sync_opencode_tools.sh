#!/bin/sh

sync_opencode_tools() {
  tools_src="$1"
  tools_dest="$2"
  dry_run_cmd="${3:-}"

  if [ -L "$tools_dest" ]; then
    printf 'refusing to sync OpenCode tools: destination is a directory symlink: %s\n' "$tools_dest" >&2
    return 1
  fi
  if [ -n "$dry_run_cmd" ]; then
    $dry_run_cmd mkdir -p "$tools_dest"
  else
    mkdir -p "$tools_dest"
  fi

  for src_file in "$tools_src"/*; do
    [ -e "$src_file" ] || continue
    base="$(basename "$src_file")"
    dest_file="$tools_dest/$base"
    if [ -L "$dest_file" ]; then
      printf 'refusing to sync OpenCode tool: destination is a file symlink: %s\n' "$dest_file" >&2
      return 1
    fi
    if [ -f "$dest_file" ] && diff -q "$src_file" "$dest_file" >/dev/null 2>&1; then
      continue
    fi
    if [ -n "$dry_run_cmd" ]; then
      $dry_run_cmd cp -fL "$src_file" "$dest_file"
      $dry_run_cmd chmod u+w "$dest_file"
    else
      cp -fL "$src_file" "$dest_file"
      chmod u+w "$dest_file"
    fi
  done
}
