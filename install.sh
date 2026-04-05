#!/usr/bin/env bash
# install.sh — Install the Torque framework from source.
#
# For npm install (preferred), use:
#   npm install -g @torquedev/cli
#   npm install @torquedev/core @torquedev/schema
#
# Usage:
#   bash install.sh              # installs to ~/dev/t
#   bash install.sh ~/my-workspace
#
# What it does:
#   1. Clones the 4 core repos (torque, core, foundation, cli)
#   2. Installs CLI dependencies
#   3. Installs the `torque` command to ~/.local/bin
#
# Everything else (bundles, services, extensions, shell) is composed
# via git sources in mount plans — resolved automatically at boot time.
set -euo pipefail

WORKSPACE="${1:-$HOME/dev/t}"
GITHUB_ORG="torque-framework"

echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │  Torque — Composable Monolith Framework  │"
echo "  └──────────────────────────────────────────┘"
echo ""
echo "  Installing to: $WORKSPACE"
echo ""

mkdir -p "$WORKSPACE"

# ── Core repos (only what's needed to run the CLI) ──────────────────────────
REPOS=(
  torque              # This repo — installer, docs
  torque-core         # Kernel — resolver, registry, boot
  torque-foundation   # Catalog, context docs, mount plans, agents
  torque-cli          # The CLI tool
)

for repo in "${REPOS[@]}"; do
  if [ -d "$WORKSPACE/$repo" ]; then
    echo "  ✓ $repo (pulling latest)"
    (cd "$WORKSPACE/$repo" && git pull --quiet 2>/dev/null) || true
  else
    echo "  ↓ $repo"
    gh repo clone "$GITHUB_ORG/$repo" "$WORKSPACE/$repo" -- --quiet 2>/dev/null || {
      echo "    ⚠ Failed to clone $repo (may not exist or no access)"
      continue
    }
  fi
done

# ── Install CLI dependencies ────────────────────────────────────────────────
echo ""
echo "  Installing CLI dependencies..."
if [ -f "$WORKSPACE/torque-cli/package.json" ]; then
  (cd "$WORKSPACE/torque-cli" && npm install --silent 2>/dev/null) || {
    echo "  ⚠ npm install failed — you may need to run it manually"
  }
fi

# ── Install the torque CLI command ──────────────────────────────────────────
echo ""
echo "  Installing torque CLI..."

CLI_BIN="$WORKSPACE/torque-cli/bin/torque.js"
INSTALL_DIR="$HOME/.local/bin"

if [ -f "$CLI_BIN" ]; then
  mkdir -p "$INSTALL_DIR"

  # Create a wrapper script (not a symlink — works across shells and nvm states)
  cat > "$INSTALL_DIR/torque" << WRAPPER
#!/usr/bin/env node
import('$CLI_BIN');
WRAPPER
  chmod +x "$INSTALL_DIR/torque"

  # Check if ~/.local/bin is on PATH
  if echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "  ✓ torque CLI installed to $INSTALL_DIR/torque"
  else
    echo "  ✓ torque CLI written to $INSTALL_DIR/torque"
    echo ""
    echo "  ⚠ Add ~/.local/bin to your PATH:"
    echo ""
    echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
    echo "    source ~/.zshrc"
  fi
else
  echo "  ⚠ torque-cli not found — skipping CLI install"
fi

# ── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "  ┌──────────────────────────────────┐"
echo "  │  Installation complete!          │"
echo "  └──────────────────────────────────┘"
echo ""
echo "  Get started:"
echo ""
echo "    torque new my-app --template kanban"
echo "    cd my-app && npm install"
echo "    AUTH_SECRET=change-me npm run seed"
echo "    AUTH_SECRET=change-me npm start"
echo ""
echo "  Login: demo@example.com / demo1234"
echo ""
echo "  Update later:"
echo ""
echo "    bash $WORKSPACE/torque/install.sh"
echo ""
echo "  For framework development (all repos + symlinks):"
echo ""
echo "    bash $WORKSPACE/torque/install-dev.sh"
echo ""
