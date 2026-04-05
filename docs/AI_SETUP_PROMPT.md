# AI Setup Prompt

Copy-paste the block below into your AI assistant (Claude, ChatGPT, etc.) to get help setting up and developing with Torque.

---

```
I'm setting up Torque, a composable monolith framework for building full-stack
apps from independent bundles. I need your help following the quickstart and
working on my project.

## What Torque is

Torque apps are defined by a "mount plan" (YAML) that declares which bundles to
load. The kernel resolves bundles from git at boot, creates SQLite tables, wires
events, and serves the app. Each bundle is its own git repo with a manifest.yml,
a logic.js class, and optional UI panels.

## Setup I've done (or need to do)

Prerequisites: Node.js 22+.

Install via npm (recommended):

    npm install -g @torquedev/cli

Or install from source (for framework contributors — requires GitHub CLI):

    mkdir -p ~/torque-dev && cd ~/torque-dev
    gh repo clone torque-framework/torque
    bash torque/install-dev.sh ~/torque-dev

The source install clones 29 repos (framework + bundles), creates @torquedev/*
symlinks so npm can resolve framework packages locally, and installs the CLI.

To create and run a sample app:

    torque new zero-to-trello --template kanban   # pick React + MUI
    cd zero-to-trello
    npm install
    AUTH_SECRET=change-me npm run seed
    AUTH_SECRET=change-me npm start

Open http://localhost:9292, log in with demo@example.com / demo1234.

## Key concepts

- Mount plan: YAML at the app root declaring bundles + config
- Bundle: independent unit with schema, events, routes, UI (lives in its own git repo)
- Kernel: resolver -> registry -> boot; reads mount plan, wires everything
- DataLayer: SQLite-backed persistence, each bundle declares its own tables
- EventBus: pub/sub for cross-bundle communication
- Coordinator: cross-bundle RPC calls
- Shell: React + MUI host that renders bundle UI panels
- Contract validation: @torquedev/schema type-checks interface inputs/outputs and event payloads at runtime
- Security: helmet headers, CORS, auth on system endpoints, JWT enforcement, token revocation
- dev-link.sh: creates node_modules/@torquedev/* symlinks pointing at local repos

## Framework packages (under @torquedev/*)

core, datalayer, eventbus, server, shell-react, ui-kit, cli, test-helpers,
authorization, datalayer-soft-delete, eventbus-async, search, storage, schema

## Workspace layout

~/torque-dev/
  torque/              <- main repo (installer, docs)
  torque-core/         <- kernel
  torque-cli/          <- CLI tool
  torque-schema/       <- contract validation
  torque-foundation/   <- catalog, context docs, agents
  torque-service-*/    <- datalayer, eventbus, server
  torque-shell-react/  <- React shell
  torque-ui-kit/       <- component library
  torque-ext-*/        <- extensions
  torque-bundle-*/     <- bundles
  node_modules/@torquedev/* <- symlinks to the above

## CLI commands

torque new <name> --template kanban
torque generate scaffold <name> <field:type ...>
torque generate intent <bundle> <name>
torque start / torque dev
torque validate / torque doctor / torque console

## Troubleshooting

- "torque: command not found" -> add ~/.local/bin to PATH
- npm install fails on @torquedev/* -> run: bash ~/torque-dev/dev-link.sh
- gh clone fails -> run: gh auth login

Help me with [describe what you need].
```
