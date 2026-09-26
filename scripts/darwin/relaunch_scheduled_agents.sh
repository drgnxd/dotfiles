#!/usr/bin/env bash
# Re-register externally managed scheduled LaunchAgents after a Nix rebuild
# rotates the nushell store path.
#
# launchd/BTM caches a per-job managed LightweightCodeRequirement pinned to a
# binary's cdhash. When a rebuild swaps Nushell, affected jobs can be
# SIGKILLed at exec with OS_REASON_CODESIGNING before their failure reporters
# run. `bootout` + `bootstrap` regenerates the requirement against the current
# binary. Keep the private job manifest outside the public repository.
#
# Must run in the interactive Aqua login session (a `just` recipe, not a
# nix-darwin activation script): `launchctl bootstrap gui/$UID` of a service
# being re-registered is not reliable from the activation context.
#
# Idempotent and sentinel-gated: does nothing unless the resolved nu path
# changed since the last successful run (override with --force).

set -euo pipefail

FORCE=0
DRY_RUN=0
TARGET_LABEL=''
RECOVER_LABEL=''
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd -P)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "$SCRIPT_PATH")"
MANIFEST="${SCRIPT_DIR}/../security/external-agents.local"
# shellcheck disable=SC1091
# shellcheck source=../security/external_agents.sh
source "${SCRIPT_DIR}/../security/external_agents.sh"

usage() {
  printf 'Usage: %s [--force] [--dry-run [--label <label>]] | --recover <label>\n' "$0" >&2
}

while (($# > 0)); do
  case "$1" in
  --force)
    FORCE=1
    shift
    ;;
  --dry-run)
    DRY_RUN=1
    shift
    ;;
  --label)
    (($# >= 2)) || {
      usage
      exit 2
    }
    TARGET_LABEL=$2
    shift 2
    ;;
  --recover)
    (($# >= 2)) || {
      usage
      exit 2
    }
    [[ -z $RECOVER_LABEL ]] || {
      usage
      exit 2
    }
    RECOVER_LABEL=$2
    shift 2
    ;;
  *)
    usage
    exit 2
    ;;
  esac
done

if [[ -n $TARGET_LABEL && $DRY_RUN -ne 1 ]]; then
  usage
  exit 2
fi
if [[ -n $RECOVER_LABEL && ($FORCE -ne 0 || $DRY_RUN -ne 0 || -n $TARGET_LABEL) ]]; then
  usage
  exit 2
fi

log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '%s WARN %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }
config_error() {
  warn "invalid local manifest: $*"
  exit 1
}
preflight_error() {
  warn "preflight failed: $*"
  exit 1
}

if [[ ! -f $MANIFEST ]]; then
  warn "local manifest not found at $MANIFEST; scheduled-agent state cannot be verified"
  exit 1
fi
external_agents_load_manifest "$MANIFEST" || exit 1

UID_NUM="$(/usr/bin/id -u)"
DOMAIN="gui/${UID_NUM}"
LA="${HOME}/Library/LaunchAgents"
STATE_DIR="${XDG_STATE_HOME:-${HOME}/.local/state}/dotfiles"
SENTINEL="${STATE_DIR}/scheduled-agents-nu"
NU_PATH="/etc/profiles/per-user/$(/usr/bin/id -un)/bin/nu"

if [[ ! -e $NU_PATH ]]; then
  warn "nu not found at $NU_PATH; no jobs were re-registered"
  exit 1
fi
NU_REAL="$(/usr/bin/readlink -f "$NU_PATH")"

if [[ -n $RECOVER_LABEL ]]; then
  [[ $RECOVER_LABEL =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $RECOVER_LABEL != *.plist ]] || {
    usage
    exit 2
  }
  if external_agents_contains "$RECOVER_LABEL" "${EXTERNAL_AGENT_LOCKED_LABELS[@]}"; then
    # shellcheck disable=SC2016
    recovery_command='source "$1"; external_agents_recover_one "$2" "$3" "$4" "$5" || { printf "recovery failed: %s\n" "$EXTERNAL_AGENTS_ERROR" >&2; exit 1; }'
    if ! /usr/bin/lockf -t 0 "$EXTERNAL_AGENT_LOCK_PATH" /bin/bash -c "$recovery_command" _ "${SCRIPT_DIR}/../security/external_agents.sh" "$MANIFEST" "$LA" "$DOMAIN" "$RECOVER_LABEL"; then
      preflight_error "recovery failed or shared lock is held for $RECOVER_LABEL; run the full relaunch after resolving the cause"
    fi
  else
    external_agents_recover_one "$MANIFEST" "$LA" "$DOMAIN" "$RECOVER_LABEL" || preflight_error "$EXTERNAL_AGENTS_ERROR"
  fi
  log "recovery complete for $RECOVER_LABEL; run 'just relaunch-agents --force' to converge all eligible jobs"
  exit 0
fi

if ! external_agents_validate_records "$LA" "$DOMAIN"; then
  config_error "$EXTERNAL_AGENTS_ERROR"
fi

if ! external_agents_loaded_labels "$DOMAIN"; then
  preflight_error "could not read loaded services in $DOMAIN"
fi
for loaded_label in "${EXTERNAL_AGENTS_LOADED_LABELS[@]}"; do
  case "$loaded_label" in
  "$EXTERNAL_AGENT_PREFIX"*)
    if ! external_agents_contains "$loaded_label" "${EXTERNAL_AGENT_LABELS[@]}"; then
      preflight_error "loaded job '$loaded_label' is missing from the external inventory"
    fi
    ;;
  esac
done

shopt -s nullglob
for deployed_file in "$LA"/"$EXTERNAL_AGENT_PREFIX"*.plist "$LA"/"$EXTERNAL_AGENT_PREFIX"*.plist.disabled; do
  deployed_name=${deployed_file##*/}
  deployed_label=${deployed_name%.plist.disabled}
  deployed_label=${deployed_label%.plist}
  if ! external_agents_contains "$deployed_label" "${EXTERNAL_AGENT_LABELS[@]}"; then
    shopt -u nullglob
    preflight_error "deployed plist '$deployed_name' is missing from the external inventory"
  fi
done
shopt -u nullglob

ACTIVE_LABELS=()
for index in "${!EXTERNAL_AGENT_LABELS[@]}"; do
  if [[ ${EXTERNAL_AGENT_STATES[index]} == enabled && ${EXTERNAL_AGENT_RELAUNCH[index]} == true ]]; then
    ACTIVE_LABELS+=("${EXTERNAL_AGENT_LABELS[index]}")
  fi
done

if [[ -n $TARGET_LABEL ]]; then
  [[ $TARGET_LABEL =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && $TARGET_LABEL != *.plist ]] || {
    usage
    exit 2
  }
  if ! external_agents_contains "$TARGET_LABEL" "${ACTIVE_LABELS[@]}"; then
    preflight_error "target '$TARGET_LABEL' is not an enabled relaunch target"
  fi
  ACTIVE_LABELS=("$TARGET_LABEL")
fi

if ((${#ACTIVE_LABELS[@]} == 0)); then
  log 'no enabled relaunch targets; nothing to do'
  exit 0
fi

PREV_REAL="$(/bin/cat "$SENTINEL" 2>/dev/null || true)"
if [[ -n $TARGET_LABEL ]]; then
  log "targeted dry-run for $TARGET_LABEL"
elif [[ $FORCE -eq 0 && $NU_REAL == "$PREV_REAL" && -n $PREV_REAL ]]; then
  exit 0
else
  log "nu changed: ${PREV_REAL:-<none>} -> ${NU_REAL}"
fi

FAILED=()
DEFERRED=()

for label in "${ACTIVE_LABELS[@]}"; do
  index=-1
  for candidate in "${!EXTERNAL_AGENT_LABELS[@]}"; do
    if [[ ${EXTERNAL_AGENT_LABELS[candidate]} == "$label" ]]; then
      index=$candidate
      break
    fi
  done
  [[ $index -ge 0 ]] || preflight_error "internal error: missing inventory row for $label"
  plist=${EXTERNAL_AGENT_DEPLOYED[index]}

  state="$(/bin/launchctl print "${DOMAIN}/${label}" 2>/dev/null || true)"
  if [[ -z $state ]]; then
    warn "$label: enabled job is not loaded; leaving it unloaded"
    FAILED+=("$label")
    continue
  fi
  case "$state" in
  *"path = ${plist}"*) ;;
  *)
    warn "$label: loaded service path does not match $plist; leaving it untouched"
    FAILED+=("$label")
    continue
    ;;
  esac
  case "$state" in
  *"state = running"*)
    log "$label: currently running -- deferring"
    DEFERRED+=("$label")
    continue
    ;;
  esac
  if [[ -n $EXTERNAL_AGENT_LOCK_PATH ]] && external_agents_contains "$label" "${EXTERNAL_AGENT_LOCKED_LABELS[@]}" && [[ -e $EXTERNAL_AGENT_LOCK_PATH ]]; then
    log "$label: configured lock held -- deferring"
    DEFERRED+=("$label")
    continue
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    log "$label: would bootout and bootstrap (dry-run)"
    continue
  fi

  if ! external_agents_validate_files "$LA"; then
    warn "$label: plist provenance changed before bootout: $EXTERNAL_AGENTS_ERROR"
    FAILED+=("$label")
    continue
  fi
  if ! external_agents_get_disabled_state "$(/bin/launchctl print-disabled "$DOMAIN" 2>/dev/null || true)" "$label"; then
    warn "$label: cannot confirm disabled state; leaving it untouched"
    FAILED+=("$label")
    continue
  fi
  if [[ $EXTERNAL_AGENTS_DISABLED_STATE == disabled ]]; then
    log "$label: disabled before bootout -- deferring"
    DEFERRED+=("$label")
    continue
  fi
  if [[ -n $EXTERNAL_AGENT_LOCK_PATH ]] && external_agents_contains "$label" "${EXTERNAL_AGENT_LOCKED_LABELS[@]}" && [[ -e $EXTERNAL_AGENT_LOCK_PATH ]]; then
    log "$label: configured lock became held -- deferring"
    DEFERRED+=("$label")
    continue
  fi
  state="$(/bin/launchctl print "${DOMAIN}/${label}" 2>/dev/null || true)"
  case "$state" in
  *"path = ${plist}"*) ;;
  *)
    warn "$label: loaded plist changed before bootout; leaving it untouched"
    FAILED+=("$label")
    continue
    ;;
  esac
  case "$state" in
  *"state = running"*)
    log "$label: became active before bootout -- deferring"
    DEFERRED+=("$label")
    continue
    ;;
  esac

  if ! /bin/launchctl bootout "$DOMAIN" "$plist" 2>/dev/null; then
    warn "$label: bootout failed; verify its state; if unloaded, recover with 'just relaunch-agents --recover $label'"
    FAILED+=("$label")
    continue
  fi

  n=0
  while /bin/launchctl print "${DOMAIN}/${label}" >/dev/null 2>&1; do
    n=$((n + 1))
    if [[ $n -ge 240 ]]; then
      break
    fi
    /bin/sleep 0.25
  done
  if /bin/launchctl print "${DOMAIN}/${label}" >/dev/null 2>&1; then
    warn "$label: bootout did not complete; service may remain loaded"
    FAILED+=("$label")
    continue
  fi

  if ! external_agents_get_disabled_state "$(/bin/launchctl print-disabled "$DOMAIN" 2>/dev/null || true)" "$label"; then
    warn "$label: cannot confirm disabled state after bootout; leaving it unloaded"
    FAILED+=("$label")
    continue
  fi
  if [[ $EXTERNAL_AGENTS_DISABLED_STATE == disabled ]]; then
    log "$label: disabled during bootout -- not bootstrapping"
    DEFERRED+=("$label")
    continue
  fi
  if ! external_agents_validate_files "$LA"; then
    warn "$label: plist provenance changed before bootstrap: $EXTERNAL_AGENTS_ERROR"
    FAILED+=("$label")
    continue
  fi

  ok=0
  for try in 1 2 3; do
    if /bin/launchctl bootstrap "$DOMAIN" "$plist" 2>/dev/null; then
      ok=1
      break
    fi
    /bin/sleep "$((try * 3))"
  done
  if [[ $ok -eq 0 ]]; then
    warn "$label: bootstrap failed after retries; it may remain unloaded. Resolve the cause, then recover with 'just relaunch-agents --recover $label'."
    FAILED+=("$label")
    continue
  fi

  props="$(/bin/launchctl print "${DOMAIN}/${label}" 2>/dev/null || true)"
  case "$props" in
  *"path = ${plist}"*) ;;
  *)
    warn "$label: bootstrap did not load the expected plist; inspect launchctl before retrying"
    FAILED+=("$label")
    continue
    ;;
  esac
  if ! external_agents_get_disabled_state "$(/bin/launchctl print-disabled "$DOMAIN" 2>/dev/null || true)" "$label" || [[ $EXTERNAL_AGENTS_DISABLED_STATE == disabled ]]; then
    warn "$label: bootstrap state could not be confirmed; inspect launchctl before retrying"
    FAILED+=("$label")
    continue
  fi
  case "$props" in
  *"managed LWCR"*) warn "$label: re-bootstrapped but still carries a managed LWCR" ;;
  esac
  log "$label: re-registered"
done

if ((${#DEFERRED[@]} > 0)); then
  warn "deferred (running / lock held / disabled): ${DEFERRED[*]} -- re-run '$0' when idle"
fi

if ((${#FAILED[@]} > 0)); then
  warn "FAILED to re-register: ${FAILED[*]}"
  exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
  log 'dry-run complete; sentinel NOT updated'
  exit 0
fi

if ((${#DEFERRED[@]} == 0)); then
  /bin/mkdir -p "$STATE_DIR"
  /usr/bin/printf '%s\n' "$NU_REAL" >"$SENTINEL"
  log 'done; sentinel updated'
else
  log 'done; sentinel NOT updated (deferrals outstanding)'
fi
