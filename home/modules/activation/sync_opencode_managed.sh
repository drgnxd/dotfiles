#!/usr/bin/env bash

# Deploy the regular files of a managed directory as real files (not store
# symlinks) and leave every other file in the destination alone.
#
# Replacement is a same-directory rename, so a running reader never sees a
# partial file and no writer quiescence is needed. A destination that no
# longer matches what was last deployed was edited by hand; it is kept as
# <name>.before-nix.<timestamp> before being replaced.

_oc_act() {
  if [[ -n ${DRY_RUN_CMD:-} ]]; then
    printf 'would run: %s\n' "$*" >&2
  else
    "$@"
  fi
}

_oc_sha() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

_oc_record_hash() {
  mkdir -p "$(dirname "$2")"
  printf '%s\n' "$1" >"$2.tmp"
  mv -f "$2.tmp" "$2"
}

# sync_opencode_managed_dir <src-dir> <dest-dir> <state-dir> [require-real-dir]
# Anomalies (symlinked destinations) are skipped with a warning so one odd
# path does not abort the whole home-manager activation.
sync_opencode_managed_dir() {
  local src_dir="$1" dest_dir="$2" state_dir="$3" require_real="${4:-}"

  if [[ -L $dest_dir && ! -d $dest_dir ]]; then
    printf 'warning: OpenCode managed path is a non-directory symlink, skipping: %s\n' "$dest_dir" >&2
    return 0
  fi
  if [[ $require_real == real && -L $dest_dir ]]; then
    printf 'warning: OpenCode managed directory must be a real directory, skipping: %s\n' "$dest_dir" >&2
    return 0
  fi

  _oc_act mkdir -p "$dest_dir"

  local src base dest src_hash dest_hash recorded stamp
  stamp="$(date +%Y%m%d%H%M%S)"
  for src in "$src_dir"/*; do
    if [[ -d $src ]]; then
      printf 'warning: OpenCode managed source subdirectory is not synced: %s\n' "$src" >&2
      continue
    fi
    [[ -f $src ]] || continue
    base="$(basename "$src")"
    dest="$dest_dir/$base"

    if [[ -L $dest ]]; then
      printf 'warning: OpenCode managed destination is a symlink, skipping: %s\n' "$dest" >&2
      continue
    fi

    src_hash="$(_oc_sha "$src")"
    if [[ -f $dest ]]; then
      dest_hash="$(_oc_sha "$dest")"
      if [[ $dest_hash == "$src_hash" ]]; then
        # Content already matches; only repair the executable bit and the record.
        if [[ -x $src && ! -x $dest ]]; then
          _oc_act chmod 0755 "$dest"
        elif [[ ! -x $src && -x $dest ]]; then
          _oc_act chmod 0644 "$dest"
        fi
        recorded="$(cat "$state_dir/$base.sha256" 2>/dev/null || true)"
        [[ $recorded == "$src_hash" ]] || _oc_act _oc_record_hash "$src_hash" "$state_dir/$base.sha256"
        continue
      fi
      recorded="$(cat "$state_dir/$base.sha256" 2>/dev/null || true)"
      if [[ $recorded != "$dest_hash" ]]; then
        printf 'OpenCode managed file differs from the last deployment; keeping %s.before-nix.%s\n' "$dest" "$stamp" >&2
        _oc_act cp -p -n "$dest" "$dest.before-nix.$stamp"
      fi
    elif [[ -e $dest ]]; then
      printf 'warning: OpenCode managed destination is not a regular file, skipping: %s\n' "$dest" >&2
      continue
    fi

    # Dot-prefixed and not ending in .ts/.js, so an interrupted run leaves
    # nothing OpenCode would load.
    local tmp="$dest_dir/.$base.tmp.$$"
    _oc_act cp -fL "$src" "$tmp"
    if [[ -x $src ]]; then
      _oc_act chmod 0755 "$tmp"
    else
      _oc_act chmod 0644 "$tmp"
    fi
    _oc_act mv -f "$tmp" "$dest"
    _oc_act _oc_record_hash "$src_hash" "$state_dir/$base.sha256"
  done
}

# retire_opencode_managed_file <dest-dir> <name> <sha256>
# Moves a tool that was removed from the repository aside, but only while it
# still has the exact content that was deployed.
retire_opencode_managed_file() {
  local dest="$1/$2" sha="$3"
  [[ -f $dest && ! -L $dest ]] || return 0
  if [[ "$(_oc_sha "$dest")" != "$sha" ]]; then
    printf 'warning: retired OpenCode file was modified, leaving it in place: %s\n' "$dest" >&2
    return 0
  fi
  _oc_act mv -n "$dest" "$dest.retired.$(date +%Y%m%d%H%M%S)"
}
