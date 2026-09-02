#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/debpalash/VoiceStudio.git}"
UPSTREAM_BRANCH="${UPSTREAM_BRANCH:-main}"
SYNC_BRANCH="${SYNC_BRANCH:-upstream-sync}"

set_changed_output() {
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "changed=$1" >> "$GITHUB_OUTPUT"
  fi
}

if git remote get-url upstream >/dev/null 2>&1; then
  git remote set-url upstream "$UPSTREAM_URL"
else
  git remote add upstream "$UPSTREAM_URL"
fi

git fetch origin main
git fetch upstream "$UPSTREAM_BRANCH"

# Every run starts from the current main branch. A stale sync branch from an
# interrupted run must never become part of the next merge candidate.
git checkout -B "$SYNC_BRANCH" origin/main

if ! git merge --no-edit "upstream/$UPSTREAM_BRANCH"; then
  mapfile -t conflicts < <(git diff --name-only --diff-filter=U)

  # Both repositories maintain release notes at the top of CHANGELOG.md, so
  # otherwise harmless upstream updates frequently conflict there. Keep the
  # Gemini edition's curated changelog while still failing closed for any code
  # conflict that needs a human decision.
  if [[ "${#conflicts[@]}" -eq 1 && "${conflicts[0]}" == "CHANGELOG.md" ]]; then
    git checkout --ours -- CHANGELOG.md
    git add CHANGELOG.md
    git commit --no-edit
  else
    printf 'Upstream merge requires manual conflict resolution:\n' >&2
    printf '  %s\n' "${conflicts[@]}" >&2
    exit 1
  fi
fi

if git diff --quiet origin/main..HEAD; then
  echo "The sync branch is already current."
  set_changed_output false
  exit 0
fi

git push origin "$SYNC_BRANCH"
set_changed_output true
echo "Pushed $SYNC_BRANCH. Validate it before promoting it to main."
