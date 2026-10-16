set shell := ["bash", "-cu"]

default:
  @just --list

# Format the whole tree with treefmt
fmt:
  nix fmt

# Check whole-tree formatting
fmt-check:
  nix fmt -- --fail-on-change

# Run all CI checks locally
check:
  nix flake check

# Install the tracked commit-message validator without replacing other hooks
install-commit-msg-hook:
  sh scripts/install_commit_msg_hook.sh

# Build Darwin configuration (no activation)
build-darwin:
  nix build path:.#packages.aarch64-darwin.default --no-link

# Apply Darwin configuration
switch-darwin:
  sudo /run/current-system/sw/bin/darwin-rebuild switch --flake path:.
  bash scripts/darwin/relaunch_scheduled_agents.sh

# Re-register eligible external scheduled LaunchAgents after a Nushell
# store-path change; targeted dry-run and explicit one-Label recovery are available.
relaunch-agents *args:
  bash scripts/darwin/relaunch_scheduled_agents.sh {{args}}

# Build Linux home-manager configuration
build-linux:
  nix build path:.#packages.x86_64-linux.default --no-link

# Apply Linux home-manager configuration
switch-linux:
  home-manager switch --flake path:.

# Update all flake inputs; nixpkgs only to a settled revision (see update-settled)
update:
  nix flake update agenix git-hooks home-manager nix-darwin nix-hazkey nix-index-database nixgl treefmt-nix
  just update-settled

# Update a single input other than nixpkgs
update-one input:
  nix flake update {{input}}

# Pin nixpkgs to the newest nixpkgs-unstable channel head that is at least `days` old, or to `rev`
update-settled days="7" allow_downgrade="false" rev="":
  #!/usr/bin/env bash
  set -euo pipefail
  days={{quote(days)}}
  [[ "$days" =~ ^[0-9]+$ ]] || { echo "days must be a non-negative integer" >&2; exit 1; }
  until="$(python3 -I -c 'import datetime, sys; print((datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=int(sys.argv[1]))).strftime("%Y-%m-%dT%H:%M:%SZ"))' "$days")"
  rev={{quote(rev)}}
  if [ -z "$rev" ]; then
    # The channel branch is advanced by a bot only when Hydra's unstable job passes, so its push history
    # (not master commit dates) is what "settled on the channel" means.
    rev="$(gh api "repos/NixOS/nixpkgs/activity?ref=refs/heads/nixpkgs-unstable&per_page=100" --jq "[.[] | select(.timestamp <= \"${until}\")][0].after // empty")"
    [[ "$rev" =~ ^[0-9a-f]{40}$ ]] || { echo "no nixpkgs-unstable head found at or before ${until} in the last 100 pushes" >&2; exit 1; }
    echo "nixpkgs-unstable head at or before ${until}: ${rev}"
  else
    # An explicit revision is what the update watcher recommends after judging its own soak time.
    [[ "$rev" =~ ^[0-9a-f]{40}$ ]] || { echo "rev must be a 40 character commit hash" >&2; exit 1; }
    echo "pinning the requested revision: ${rev}"
  fi
  meta="$(nix flake prefetch --json "github:NixOS/nixpkgs/${rev}")"
  # Edit only the locked node so `original` keeps tracking nixpkgs-unstable and Nix does not relock it.
  python3 -I - "$meta" "$rev" {{quote(allow_downgrade)}} <<'PY'
  import json, os, sys
  meta, rev, allow_downgrade = json.loads(sys.argv[1]), sys.argv[2], sys.argv[3] == "true"
  locked = {**meta["locked"], "narHash": meta["hash"]}
  assert locked["rev"] == rev and locked["owner"] == "NixOS" and locked["repo"] == "nixpkgs", "unexpected prefetch result"
  with open("flake.lock") as f:
      lock = json.load(f)
  node = lock["nodes"]["nixpkgs"]
  if locked["lastModified"] < node["locked"]["lastModified"] and not allow_downgrade:
      sys.exit("refusing to move nixpkgs backwards; pass allow_downgrade=true to override")
  node["locked"] = {k: locked[k] for k in ("lastModified", "narHash", "owner", "repo", "rev", "type")}
  with open("flake.lock.tmp", "w") as f:
      json.dump(lock, f, indent=2)
      f.write("\n")
  os.replace("flake.lock.tmp", "flake.lock")
  PY
  nix flake metadata path:. > /dev/null
  git --no-pager diff --stat flake.lock

# Run shfmt on all shell scripts
fmt-shell:
  git ls-files -z '*.sh' | xargs -0 shfmt -w

# Run statix and the CI ruff check
lint:
  nix run nixpkgs#statix -- check .
  uv tool run ruff check xdg/config/opencode

# Show dead Nix code
dead:
  nix run nixpkgs#deadnix -- --fail .

# Rekey agenix secrets
rekey:
  cd secrets && nix run github:ryantm/agenix -- -r

# Show OpenCode subscription usage (pinned npm CLI)
usage:
  bunx opencode-usage@0.5.15

# Report the read-only macOS security posture
security-audit *args:
  scripts/security/audit_darwin.sh {{args}}

# Test the local external LaunchAgent inventory parser
test-external-agents:
  bash scripts/security/test_external_agents.sh

test-private-terms:
  bash scripts/security/test_private_terms.sh

# Test the worktree removal helper bundled with the git-workflow skill
test-worktree-remove:
  uv run --python 3.11 --with pytest pytest -q xdg/config/opencode/skills/git-workflow/scripts/test_safe_worktree_remove.py

# Test the worktree create/audit helpers bundled with the git-workflow skill
test-worktree-tools:
  uv run --python 3.11 --with pytest pytest -q xdg/config/opencode/skills/git-workflow/scripts/test_worktree_tools.py xdg/config/opencode/skills/git-workflow/scripts/test_worktree_guard.py

test-worktree-task:
  uv run --python 3.11 python -m unittest discover -s xdg/config/opencode/skills/git-workflow/scripts -p test_worktree_task.py

# Check that machine-local paths and manifests are not tracked
check-public-boundary:
  scripts/check-public-boundary.sh

# Verify GitHub ruleset required status checks match existing workflow job ids
check-required-checks-sync:
  scripts/check-required-checks-sync.sh
