# Quickstart

Get a Torque app running from scratch.

## Prerequisites

- **Node.js 22+** (`node --version`)

## 1. Install

### Option A: npm (recommended)

```bash
npm install -g @torquedev/cli
```

That's it -- the CLI pulls framework packages (`@torquedev/core`, `@torquedev/schema`, etc.) as needed when you create and run apps.

### Option B: From source (for framework contributors)

Requires GitHub CLI (`gh auth status`).

```bash
mkdir -p ~/torque-dev && cd ~/torque-dev
gh repo clone torque-framework/torque
bash torque/install-dev.sh ~/torque-dev
```

This clones all 29 repos (framework, services, extensions, bundles), creates `@torquedev/*` symlinks so packages resolve locally, and installs the `torque` CLI to `~/.local/bin/torque`.

If `torque` isn't on your PATH afterwards:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## 2. Create an app

```bash
torque new zero-to-trello --template kanban
```

Pick **React + MUI** when prompted.

## 3. Run it

```bash
cd zero-to-trello
npm install
AUTH_SECRET=change-me npm run seed
AUTH_SECRET=change-me npm start
```

Open http://localhost:9292 and log in with `demo@example.com` / `demo1234`.

## What just happened

1. `install-dev.sh` cloned the framework repos and bundle repos side-by-side under `~/torque-dev/`
2. `dev-link.sh` (called automatically) created `node_modules/@torquedev/*` symlinks so `npm install` can resolve the framework packages (`@torquedev/core`, `@torquedev/schema`, `@torquedev/datalayer`, `@torquedev/eventbus`, `@torquedev/server`, `@torquedev/shell-react`)
3. `torque new` scaffolded an app with a mount plan pointing at the identity, workspace, and kanban bundles
4. At boot, the kernel reads the mount plan, resolves bundles from git, creates SQLite tables, wires events, and starts the server

## Updating

Pull latest across all repos:

```bash
bash ~/torque-dev/torque/install-dev.sh ~/torque-dev
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `torque: command not found` | Add `~/.local/bin` to PATH (see step 1) |
| `npm install` fails on `@torquedev/*` | Run `bash ~/torque-dev/dev-link.sh` from `~/torque-dev/` |
| `gh repo clone` fails | Run `gh auth login` first |
| Port 9292 in use | `AUTH_SECRET=change-me PORT=3000 npm start` |
