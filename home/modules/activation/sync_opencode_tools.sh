#!/bin/sh

sync_opencode_tools() {
  tools_python="$1"
  tools_helper="$2"
  mapping_id="$3"
  tools_src="$4"
  tools_dest="$5"
  state_root="$6"
  dry_run_cmd="${7:-}"

  if [ ! -f "$tools_helper" ]; then
    printf 'OpenCode tools sync helper is unavailable; preserving destination: %s\n' "$tools_helper" >&2
    return 0
  fi

  if [ -n "$dry_run_cmd" ] || [ "${OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED:-}" != "1" ]; then
    if [ -z "$dry_run_cmd" ]; then
      printf 'OpenCode tools sync was not applied; set OPENCODE_TOOLS_SYNC_WRITERS_QUIESCED=1 only after quiescing all writers.\n' >&2
    fi
    "$tools_python" "$tools_helper" \
      --mapping-id "$mapping_id" \
      --source "$tools_src" \
      --destination "$tools_dest" \
      --state-root "$state_root" \
      --dry-run
  else
    "$tools_python" "$tools_helper" \
      --mapping-id "$mapping_id" \
      --source "$tools_src" \
      --destination "$tools_dest" \
      --state-root "$state_root" \
      --external-writers-quiesced
  fi
}
