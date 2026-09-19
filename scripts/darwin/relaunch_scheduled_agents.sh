#!/usr/bin/env bash
# Re-register externally managed scheduled LaunchAgents after a Nix rebuild
# rotates the nushell store path.
#
# Why this exists: each job's ProgramArguments[0] resolves through
# /etc/profiles/per-user/<user>/bin/nu. launchd/BTM caches a per-job managed
# LightweightCodeRequirement pinned to that binary's cdhash; when a rebuild
# swaps nushell, the kernel SIGKILLs the job at exec with OS_REASON_CODESIGNING
# -- before the job's own failure-reporting wrapper runs, so nothing notifies.
# `bootout` + `bootstrap` regenerates the LWCR against the current binary.
# Keep the private job manifest outside the public repository.
#
# Must run in the interactive Aqua login session (a `just` recipe, not a
# nix-darwin activation script): `launchctl bootstrap gui/$UID` of a service
# that is being re-registered is not reliable from the activation context.
#
# Idempotent and sentinel-gated: does nothing unless the resolved nu path
# changed since the last successful run (override with --force).

set -euo pipefail

FORCE=0
DRY_RUN=0
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd -P)"
MANIFEST="${SCRIPT_DIR}/../security/external-agents.local"
ACTIVE_LABELS=()
LOCKED_LABELS=()
AGENT_PREFIX=""
LOCK_PATH=""
PREFIX_SET=0
LOCK_PATH_SET=0

usage() {
  printf 'Usage: %s [--force] [--dry-run]\n' "$0" >&2
}

for arg in "$@"; do
  case "$arg" in
  --force) FORCE=1 ;;
  --dry-run) DRY_RUN=1 ;;
  *)
    usage
    exit 2
    ;;
  esac
done

log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '%s WARN %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }

contains() {
  local needle=$1
  shift
  local value

  for value in "$@"; do
    [ "$value" = "$needle" ] && return 0
  done

  return 1
}

config_error() {
  warn "invalid local manifest: $*"
  exit 1
}

trim() {
  local value=$1

  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  TRIMMED_VALUE=$value
}

if [ ! -f "$MANIFEST" ]; then
  warn "local manifest not found at $MANIFEST; nothing to do"
  exit 0
fi

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  trim "$line"
  line=$TRIMMED_VALUE

  case "$line" in
  '')
    continue
    ;;
  '# relaunch-prefix='*)
    [ "$PREFIX_SET" -eq 0 ] || config_error "duplicate relaunch-prefix"
    trim "${line#\# relaunch-prefix=}"
    AGENT_PREFIX=$TRIMMED_VALUE
    case "$AGENT_PREFIX" in
    '' | *[!A-Za-z0-9._-]*) config_error "relaunch-prefix must be a non-empty label prefix" ;;
    esac
    PREFIX_SET=1
    ;;
  '# relaunch-lock-path='*)
    [ "$LOCK_PATH_SET" -eq 0 ] || config_error "duplicate relaunch-lock-path"
    trim "${line#\# relaunch-lock-path=}"
    LOCK_PATH=$TRIMMED_VALUE
    case "$LOCK_PATH" in
    /*) ;;
    *) config_error "relaunch-lock-path must be an absolute path" ;;
    esac
    LOCK_PATH_SET=1
    ;;
  '# relaunch-lock-label='*)
    trim "${line#\# relaunch-lock-label=}"
    lock_label=$TRIMMED_VALUE
    case "$lock_label" in
    '' | *[!A-Za-z0-9._-]*) config_error "relaunch-lock-label is not a valid label" ;;
    esac
    contains "$lock_label" "${LOCKED_LABELS[@]}" &&
      config_error "duplicate relaunch-lock-label: $lock_label"
    LOCKED_LABELS+=("$lock_label")
    ;;
  '# relaunch-'*)
    config_error "unknown relaunch directive"
    ;;
  '# ' | '#'*)
    continue
    ;;
  *)
    line="${line%%#*}"
    trim "$line"
    line=$TRIMMED_VALUE
    [ -n "$line" ] || continue
    case "$line" in
    *.plist) label=${line%.plist} ;;
    *) config_error "agent entries must end in .plist" ;;
    esac
    case "$label" in
    '' | *[!A-Za-z0-9._-]*) config_error "invalid LaunchAgent label: $label" ;;
    esac
    contains "$label" "${ACTIVE_LABELS[@]}" &&
      config_error "duplicate LaunchAgent label: $label"
    ACTIVE_LABELS+=("$label")
    ;;
  esac
done <"$MANIFEST"

if [ "${#ACTIVE_LABELS[@]}" -eq 0 ]; then
  warn "local manifest has no active LaunchAgents; nothing to do"
  exit 0
fi

if [ -n "$LOCK_PATH" ] && [ "${#LOCKED_LABELS[@]}" -eq 0 ]; then
  config_error "relaunch-lock-path requires at least one relaunch-lock-label"
fi
if [ -z "$LOCK_PATH" ] && [ "${#LOCKED_LABELS[@]}" -gt 0 ]; then
  config_error "relaunch-lock-label requires relaunch-lock-path"
fi
for lock_label in "${LOCKED_LABELS[@]}"; do
  contains "$lock_label" "${ACTIVE_LABELS[@]}" ||
    config_error "relaunch-lock-label is not an active LaunchAgent: $lock_label"
done

UID_NUM="$(/usr/bin/id -u)"
DOMAIN="gui/${UID_NUM}"
LA="${HOME}/Library/LaunchAgents"
STATE_DIR="${XDG_STATE_HOME:-${HOME}/.local/state}/dotfiles"
SENTINEL="${STATE_DIR}/scheduled-agents-nu"
NU_PATH="/etc/profiles/per-user/$(/usr/bin/id -un)/bin/nu"

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$STATE_DIR"
fi

if [ ! -e "$NU_PATH" ]; then
  warn "nu not found at $NU_PATH; nothing to do"
  exit 0
fi
NU_REAL="$(/usr/bin/readlink -f "$NU_PATH")"
PREV_REAL="$(cat "$SENTINEL" 2>/dev/null || true)"

if [ "$FORCE" -eq 0 ] && [ "$NU_REAL" = "$PREV_REAL" ] && [ -n "$PREV_REAL" ]; then
  exit 0
fi
log "nu changed: ${PREV_REAL:-<none>} -> ${NU_REAL}"

# Drift check: a loaded job under the configured prefix that is not in the
# local allow-list.
if [ -n "$AGENT_PREFIX" ]; then
  while IFS= read -r loaded; do
    case "$loaded" in
    "$AGENT_PREFIX"*)
      if ! contains "$loaded" "${ACTIVE_LABELS[@]}"; then
        warn "loaded job '$loaded' is not in the local allow-list; skipping it"
      fi
      ;;
    esac
  done < <(/bin/launchctl list | /usr/bin/awk '{print $3}')
fi

failed=()
deferred=()

for label in "${ACTIVE_LABELS[@]}"; do
  plist="${LA}/${label}.plist"
  if [ ! -f "$plist" ]; then
    warn "$label: no plist at $plist -- not deployed?"
    failed+=("$label")
    continue
  fi
  real_label="$(/usr/bin/plutil -extract Label raw -o - "$plist" 2>/dev/null || true)"
  if [ "$real_label" != "$label" ]; then
    warn "$label: plist Label key is '$real_label' -- skipping (fix the plist)"
    failed+=("$label")
    continue
  fi

  # Don't kill an in-flight job.
  state="$(/bin/launchctl print "${DOMAIN}/${label}" 2>/dev/null || true)"
  case "$state" in
  *"state = running"*)
    log "$label: currently running -- deferring"
    deferred+=("$label")
    continue
    ;;
  esac
  if [ -n "$LOCK_PATH" ] && contains "$label" "${LOCKED_LABELS[@]}" && [ -e "$LOCK_PATH" ]; then
    log "$label: configured lock held -- deferring"
    deferred+=("$label")
    continue
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "$label: would bootout and bootstrap (dry-run)"
    continue
  fi

  /bin/launchctl bootout "$DOMAIN" "$plist" 2>/dev/null || true

  # bootout is async; wait (up to 60s) for the service to leave the domain.
  n=0
  while /bin/launchctl print "${DOMAIN}/${label}" >/dev/null 2>&1; do
    n=$((n + 1))
    [ "$n" -ge 240 ] && break
    /bin/sleep 0.25
  done

  ok=0
  for try in 1 2 3; do
    if /bin/launchctl bootstrap "$DOMAIN" "$plist" 2>/dev/null; then
      ok=1
      break
    fi
    /bin/sleep "$((try * 3))"
  done
  if [ "$ok" -eq 0 ]; then
    warn "$label: bootstrap failed after retries"
    failed+=("$label")
    continue
  fi

  props="$(/bin/launchctl print "${DOMAIN}/${label}" 2>/dev/null || true)"
  case "$props" in
  *"managed LWCR"*) warn "$label: re-bootstrapped but still carries a managed LWCR" ;;
  esac
  log "$label: re-registered"
done

if [ "${#deferred[@]}" -gt 0 ]; then
  warn "deferred (running / lock held): ${deferred[*]} -- re-run '$0' when idle"
fi

if [ "${#failed[@]}" -gt 0 ]; then
  warn "FAILED to re-register: ${failed[*]}"
  warn "fix and re-run: $0 --force"
  exit 1
fi

if [ "$DRY_RUN" -eq 1 ]; then
  log "dry-run complete; sentinel NOT updated"
  exit 0
fi

# Only advance the sentinel when nothing is outstanding, so a partial run
# retries next time.
if [ "${#deferred[@]}" -eq 0 ]; then
  printf '%s\n' "$NU_REAL" >"$SENTINEL"
  log "done; sentinel updated"
else
  log "done; sentinel NOT updated (deferrals outstanding)"
fi
