#!/usr/bin/env bash
# Fortnightly NDIS watch, built for cron: silent when nothing has moved.
#
# 1. check the ten official sources plus the shipped library
# 2. on change: refresh the library, commit, push, and print what moved so the cron can deliver it
#
# Run by hand any time with:  bash scripts/ndis_watch_cron.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

PY=${PY:-python}
OUT=$("$PY" scripts/ndis_watch.py --json 2>&1)
CODE=$?

if [ "$CODE" -eq 0 ]; then
  exit 0                     # nothing changed: say nothing
fi

echo "$OUT" | tail -c 4000
echo

"$PY" scripts/fetch-ndis-docs.py >/dev/null 2>&1 || echo "library refresh failed; sources above still stand"

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git -c user.name="${GIT_AUTHOR_NAME:-Individual Agent NDIS Watch}" \
      -c user.email="${GIT_AUTHOR_EMAIL:-noreply@localhost}" \
      commit -q -m "NDIS watch: refresh library $(date +%F)"

  # Push with your normal Git credentials: a credential helper, `gh auth setup-git`,
  # an SSH key, or your OS credential manager. Never pass a secret on the command
  # line -- arguments are visible to other processes and leak into error output.
  REMOTE=$(git config --get remote.origin.url || true)
  if [ -z "$REMOTE" ]; then
    echo "no git remote configured: commit made locally, push skipped"
  elif GIT_TERMINAL_PROMPT=0 git push origin HEAD:main 2>/dev/null; then
    echo "pushed to $REMOTE"
  else
    echo "commit made locally; push skipped."
    echo "Set up push credentials once with: gh auth setup-git   (or add an SSH key), then re-run."
  fi
fi
