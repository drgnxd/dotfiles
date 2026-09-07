#!/usr/bin/env bash
# Re-register the hand-deployed com.drgnxd.* scheduled LaunchAgents after a
# Nix rebuild rotates the nushell store path.
#
# Why this exists: each job's ProgramArguments[0] resolves through
# /etc/profiles/per-user/<user>/bin/nu. launchd/BTM caches a per-job managed
# LightweightCodeRequirement pinned to that binary's cdhash; when a rebuild
# swaps nushell, the kernel SIGKILLs the job at exec with OS_REASON_CODESIGNING
# -- before the job's own failure-reporting wrapper runs, so nothing notifies.
# `bootout` + `bootstrap` regenerates the LWCR against the current binary.
# Full write-up: ~/repos/accretion/system/launchd/README.md (pitfalls section).
#
# Must run in the interactive Aqua login session (a `just` recipe, not a
# nix-darwin activation script): `launchctl bootstrap gui/$UID` of a service
# that is being re-registered is not reliable from the activation context.
#
# Idempotent and sentinel-gated: does nothing unless the resolved nu path
# changed since the last successful run (override with --force).

set -euo pipefail

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

UID_NUM="$(/usr/bin/id -u)"
DOMAIN="gui/${UID_NUM}"
LA="${HOME}/Library/LaunchAgents"
STATE_DIR="${XDG_STATE_HOME:-${HOME}/.local/state}/dotfiles"
SENTINEL="${STATE_DIR}/scheduled-agents-nu"
NU_PATH="/etc/profiles/per-user/$(/usr/bin/id -un)/bin/nu"

# Explicit allow-list of the ACTIVE hand-deployed jobs. Deliberately not a live
# `com.drgnxd.*` glob: a retired job whose plist is transiently back in place
# (mid-debug) must not be silently re-armed, and drift should surface loudly.
# Keep in sync with ~/repos/accretion/system/launchd/README.md and
# ~/repos/scripts/launchd/README.md.
#   accretion: daily-trivia daily-element personal-news practice-reminder git-annex-sync
#   scripts:   repos-backup dotfiles-backup personal-news-backup conversation-sync conversation-archive
#   cultura-tracker: unext-sale-log
# NOT listed on purpose: restic-home-backup (retired, ~/repos/scripts/README.md).
ACTIVE_LABELS=(
  com.drgnxd.daily-trivia
  com.drgnxd.daily-element
  com.drgnxd.personal-news
  com.drgnxd.practice-reminder
  com.drgnxd.git-annex-sync
  com.drgnxd.repos-backup
  com.drgnxd.dotfiles-backup
  com.drgnxd.personal-news-backup
  com.drgnxd.conversation-sync
  com.drgnxd.conversation-archive
  com.drgnxd.unext-sale-log
)

# Jobs to never bootout from here even if the nu path changed: killing them
# mid-run corrupts shared state (shared lock + Proton Drive publish + Raw
# deletion). They pick up the new binary on their next scheduled start anyway
# once every other job's re-registration proves the new binary is accepted;
# if they are themselves codesigning-killed, the deferred list below reports
# them and the user re-runs with the jobs idle.
CONV_LOCK="${XDG_STATE_HOME:-${HOME}/.local/state}/accretion/conversation-sync.lock"

log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*"; }
warn() { printf '%s WARN %s\n' "$(date '+%H:%M:%S')" "$*" >&2; }

mkdir -p "$STATE_DIR"

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

# Drift check: a loaded com.drgnxd.* that is not in the allow-list.
while IFS= read -r loaded; do
  keep=0
  for l in "${ACTIVE_LABELS[@]}"; do [ "$l" = "$loaded" ] && keep=1 && break; done
  if [ "$keep" -eq 0 ]; then
    warn "loaded job '$loaded' is not in ACTIVE_LABELS -- update the allow-list or bootout the job; skipping it"
  fi
done < <(/bin/launchctl list | /usr/bin/awk '/com\.drgnxd\./ {print $3}')

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
  case "$label" in
  com.drgnxd.conversation-sync | com.drgnxd.conversation-archive)
    if [ -e "$CONV_LOCK" ]; then
      log "$label: conversation lock held -- deferring"
      deferred+=("$label")
      continue
    fi
    ;;
  esac

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

# Only advance the sentinel when nothing is outstanding, so a partial run
# retries next time.
if [ "${#deferred[@]}" -eq 0 ]; then
  printf '%s\n' "$NU_REAL" >"$SENTINEL"
  log "done; sentinel updated"
else
  log "done; sentinel NOT updated (deferrals outstanding)"
fi
