#!/usr/bin/env bash
# install-dev.sh — Clone ALL Torque repos for framework development.
#
# For npm install (preferred for app development), use:
#   npm install -g @torquedev/cli
#
# Usage:
#   bash install-dev.sh              # installs to ~/dev/t
#   bash install-dev.sh ~/my-workspace
#
# Use this if you're working on Torque itself (core, services, extensions,
# bundles). For app development, use npm install instead — bundles compose
# via git sources in mount plans.
set -euo pipefail

WORKSPACE="${1:-$HOME/dev/t}"
GITHUB_ORG="torque-framework"

echo ""
echo "  Torque — Full development install"
echo ""
echo "  Installing to: $WORKSPACE"
echo ""

mkdir -p "$WORKSPACE"

REPOS=(
  # Core (also installed by install.sh)
  torque
  torque-core
  torque-foundation
  torque-cli
  # Schema
  torque-schema
  # Services
  torque-service-datalayer
  torque-service-eventbus
  torque-service-server
  # UI
  torque-ui-kit
  torque-shell-react
  # Tooling
  torque-test-helpers
  # Extensions
  torque-ext-authorization
  torque-ext-soft-delete
  torque-ext-async-events
  torque-ext-search
  torque-ext-storage
  # Bundles
  torque-bundle-identity
  torque-bundle-pipeline
  torque-bundle-pulse
  torque-bundle-tasks
  torque-bundle-graphql
  torque-bundle-workspace
  torque-bundle-boards
  torque-bundle-kanban
  torque-bundle-activity
  torque-bundle-realtime
  torque-bundle-profile
  torque-bundle-admin
  torque-bundle-search
)

echo "  Cloning ${#REPOS[@]} repos..."
echo ""

for repo in "${REPOS[@]}"; do
  if [ -d "$WORKSPACE/$repo" ]; then
    echo "  ✓ $repo (pulling latest)"
    (cd "$WORKSPACE/$repo" && git pull --quiet 2>/dev/null) || true
  else
    echo "  ↓ $repo"
    gh repo clone "$GITHUB_ORG/$repo" "$WORKSPACE/$repo" -- --quiet 2>/dev/null || {
      echo "    ⚠ Failed to clone $repo"
    }
  fi
done

# ── Set up @torquedev/* symlinks for cross-repo development ────────────────────
echo ""
echo "  Setting up @torquedev/* symlinks..."
if [ -f "$WORKSPACE/dev-link.sh" ]; then
  (cd "$WORKSPACE" && bash dev-link.sh)
elif [ -f "$WORKSPACE/torque/dev-link.sh" ]; then
  cp "$WORKSPACE/torque/dev-link.sh" "$WORKSPACE/dev-link.sh"
  (cd "$WORKSPACE" && bash dev-link.sh)
fi

# ── Install CLI (reuse install.sh logic) ────────────────────────────────────
echo ""
bash "$WORKSPACE/torque/install.sh" "$WORKSPACE" 2>/dev/null || true

echo ""
echo "  Dev install complete! ${#REPOS[@]} repos ready."
echo "  Run 'bash dev-link.sh' after adding new repos."
echo ""
