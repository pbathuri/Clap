#!/usr/bin/env bash
# Push to GitHub using a token from the environment.
# Usage: export GITHUB_TOKEN=ghp_xxxx; ./scripts/git_push_with_token.sh
# Or:    GITHUB_TOKEN=ghp_xxxx ./scripts/git_push_with_token.sh
set -e
cd "$(dirname "$0")/../.."
if [[ -z "${GITHUB_TOKEN}" ]]; then
  echo "Set GITHUB_TOKEN first, e.g. export GITHUB_TOKEN=ghp_xxxx"
  exit 1
fi
git push "https://${GITHUB_TOKEN}@github.com/pbathuri/Clap.git" main
