#!/usr/bin/env bash
set -euo pipefail

# Catches "test-taskwarrior"-class drift: a required status check left behind
# in the repo's GitHub ruleset after the workflow job that used to produce it
# was renamed or removed. Rulesets live outside this repo's tracked files, so
# nothing else here notices that kind of drift on its own (confirmed
# 2026-07-29: this exact situation left every PR showing "Some checks
# haven't completed yet" indefinitely).
#
# This runs locally, not in CI: GITHUB_TOKEN in Actions cannot read rulesets
# (there is no "administration" scope grantable to it, confirmed via
# actionlint's permission scope list), so it only works against your own
# authenticated `gh` session, which already has full repo admin read access.

repo="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"

job_ids=$(for f in .github/workflows/*.yml; do
  nix run nixpkgs#yq-go -- -r '.jobs | keys[]' "$f"
done | sort -u)

ruleset_ids=$(gh api "repos/${repo}/rulesets" --jq '.[].id')

errors=0
for rid in $ruleset_ids; do
  name=$(gh api "repos/${repo}/rulesets/${rid}" --jq '.name')
  required=$(gh api "repos/${repo}/rulesets/${rid}" --jq \
    '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context')
  for ctx in $required; do
    if ! grep -qxF "$ctx" <<<"$job_ids"; then
      echo "ERROR: ruleset '${name}' requires status check '${ctx}', but no workflow job with that id exists" >&2
      errors=$((errors + 1))
    fi
  done
done

if [ "$errors" -gt 0 ]; then
  exit 1
fi
echo "OK: required status checks across all rulesets match an existing workflow job id."
