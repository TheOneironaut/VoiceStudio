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

if git fetch origin "$SYNC_BRANCH" 2>/dev/null; then
  git checkout -B "$SYNC_BRANCH" "origin/$SYNC_BRANCH"
  git merge --no-edit origin/main
else
  git checkout -B "$SYNC_BRANCH" origin/main
fi

git merge --no-edit "upstream/$UPSTREAM_BRANCH"

if git diff --quiet origin/main..HEAD; then
  echo "The sync branch is already current."
  set_changed_output false
  exit 0
fi

git push origin "$SYNC_BRANCH"
set_changed_output true
echo "Pushed $SYNC_BRANCH. Validate it before promoting it to main."
