#!/usr/bin/env bash
# dev-link.sh — Creates @torquedev/* symlinks for local cross-repo development.
#
# Usage:
#   cd ~/dev/t
#   bash dev-link.sh
#
# Run this after cloning the repos you need under ~/dev/t/.
# To reset: delete node_modules/@torque and re-run.

# Resolve workspace to the directory containing this script.
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINK_DIR="$WORKSPACE/node_modules/@torque"

# ---------------------------------------------------------------------------
# Package name → repo directory name mapping (14 packages)
# Each entry is "package-name:repo-dirname"
# ---------------------------------------------------------------------------
PACKAGES=(
  "core:torque-core"
  "datalayer:torque-service-datalayer"
  "eventbus:torque-service-eventbus"
  "server:torque-service-server"
  "ui-kit:torque-ui-kit"
  "cli:torque-cli"
  "test-helpers:torque-test-helpers"
  "authorization:torque-ext-authorization"
  "datalayer-soft-delete:torque-ext-soft-delete"
  "eventbus-async:torque-ext-async-events"
  "search:torque-ext-search"
  "storage:torque-ext-storage"
  "shell-react:torque-shell-react"
  "schema:torque-schema"
)

# Ensure the symlink target directory exists.
mkdir -p "$LINK_DIR"

echo "Workspace : $WORKSPACE"
echo "Link dir  : $LINK_DIR"
echo ""

for entry in "${PACKAGES[@]}"; do
  pkg="${entry%%:*}"
  repo="${entry##*:}"
  repo_path="$WORKSPACE/$repo"
  link_path="$LINK_DIR/$pkg"

  if [ -d "$repo_path" ]; then
    # Remove a stale symlink if present, then create a fresh one.
    rm -f "$link_path"
    ln -s "$repo_path" "$link_path"
    echo "  LINKED   @torquedev/$pkg  ->  $repo_path"
  else
    echo "  MISSING  @torquedev/$pkg  (expected repo: $repo)"
  fi
done

echo ""
echo "Done."
