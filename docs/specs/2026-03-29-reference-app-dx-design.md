# Reference App & DX Design

## Goal

Create `torque-app-todo` as the "zero to Trello in minutes" reference app. Redesign `torque new` scaffold with a CLI interview. Demonstrate every Torque capability in the smallest possible business frame: task management.

## Background

The current dealtracker example is too large and too domain-specific to serve as an onboarding reference. A task tracker hits the sweet spot — familiar domain, small surface area, but exercises every framework capability: auth, data, events, UI composition, and bundle orchestration.

## Approach

Replace the dealtracker with a single reference app (`torque-app-todo`) that mounts four bundles from git. Redesign the `torque new` CLI to scaffold apps with a short interview choosing shell and bundle presets. The app repo contains only configuration and boot wiring — all functionality comes from bundles.

## Architecture

### What the User Sees After `torque new myapp`

- Auth (sign in / sign up) — from `torque-bundle-identity`
- Kanban board (drag tasks between stages) — from `torque-bundle-pipeline`
- Activity feed (who did what when) — from `torque-bundle-pulse`
- Task management (assign, due dates, link to entities) — from `torque-bundle-tasks`
- Dashboard with stats — auto-composed from bundle data
- All UI auto-wired from bundle manifests via `torque-shell-react`

### What `torque-app-todo` Actually Contains

```
torque-app-todo/
├── boot.js                    ← wires kernel + services (~25 lines)
├── package.json               ← owns runtime deps (express, better-sqlite3, etc.)
├── app.config.js              ← theme, branding, auth config
├── config/
│   └── mount_plans/
│       └── development.yml    ← mounts all 4 bundles from git URLs
├── seeds/
│   └── demo.js                ← optional demo data
├── bundles/                   ← empty (bundles fetched from git)
├── .bundles/                  ← git-fetched cache (gitignored)
├── bundle.lock                ← pinned commits
├── data/                      ← SQLite (gitignored)
├── test/                      ← integration tests
└── agents.md
```

No `frontend/` directory. No `shell/` directory. No per-bundle imports. Display comes entirely from `@torquedev/shell-react` + bundle manifests.

## Components

### `torque new` — Scaffold with CLI Interview

```
$ torque new myapp

  Shell? (how bundle UIs render)
  > React + MUI (recommended)
    Vanilla (no build step)
    None (API only)

  Bundles? (start with these features)
  > All (identity + pipeline + pulse + tasks)
    Auth only (identity)
    Empty (add bundles later)

Creating myapp...
  boot.js
  package.json
  app.config.js
  config/mount_plans/development.yml
  seeds/demo.js
  agents.md
  .gitignore

Done. Next:
  cd myapp
  npm install        ← installs express, better-sqlite3, etc.
  torque start       ← boots kernel, fetches bundles, seeds data
```

### What Gets Generated Based on Choices

**Shell = React**: `package.json` includes `@torquedev/shell-react` as dependency, `boot.js` imports `createShell`, `app.config.js` has theme/branding defaults.

**Shell = Vanilla**: `package.json` has no React deps, `boot.js` uses a lightweight vanilla shell.

**Shell = None**: No shell at all, `boot.js` creates server without frontend, pure API.

**Bundles = All**: `development.yml` mount plan lists all 4 bundles with `git+https://github.com/torque-framework/torque-bundle-*` sources.

**Bundles = Auth only**: Just identity bundle.

**Bundles = Empty**: Empty bundles section, user adds their own.

The `npm install` step is the ONLY time npm runs — it installs the app's declared runtime deps. Bundles are fetched by the Resolver at boot time from git, not by npm.

### `torque generate scaffold`

```
torque generate scaffold invoices amount:integer status:string
```

Creates a new bundle locally in `bundles/invoices/` with manifest, logic, ui, agent.md, and test — adds one line to the mount plan. Same DX as Rails generators, but the output is a composable bundle, not coupled controller code.

### Framework Dependency Separation

The app's `package.json` is the ONLY place that declares runtime deps. The framework packages are zero-dep or peer-dep only.

```json
// API-only app (Shell = None)
{
  "dependencies": {
    "express": "^4.21.0",
    "better-sqlite3": "^11.0.0",
    "js-yaml": "^4.1.0",
    "uuid": "^10.0.0"
  }
}
```

```json
// Full-stack app (Shell = React)
{
  "dependencies": {
    "express": "^4.21.0",
    "better-sqlite3": "^11.0.0",
    "js-yaml": "^4.1.0",
    "uuid": "^10.0.0",
    "@torquedev/shell-react": "git+https://github.com/torque-framework/torque-shell-react"
  }
}
```

## Data Flow

### Boot Sequence (Generated `boot.js`)

```javascript
import { Registry, Resolver, HookBus } from '@torquedev/core';
import { DataLayer, BundleScopedData } from '@torquedev/datalayer';
import { EventBus } from '@torquedev/eventbus';
import { createServer } from '@torquedev/server';
import { createShell } from '@torquedev/shell-react';
import appConfig from './app.config.js';

const planPath = process.env.MOUNT_PLAN || 'config/mount_plans/development.yml';
const dbPath   = process.env.DB_PATH || 'data/app.sqlite3';
const port     = parseInt(process.env.PORT || '9292');

const resolver = new Resolver();
const resolved = await resolver.resolve(planPath);

const dataLayer = new DataLayer(dbPath);
const hookBus   = new HookBus();
const eventBus  = new EventBus({ db: dataLayer.db, hookBus });

const registry = new Registry({
  dataLayer, eventBus, hookBus,
  createScopedData: (dl, name) => new BundleScopedData(dl, name),
});

await registry.boot(planPath, resolved);

const app = createServer(registry, eventBus, {
  hookBus,
  shell: createShell(appConfig),
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
```

This is ~25 lines of wiring. The app never references bundle names, never imports bundle code. Everything is resolved dynamically from the mount plan.

## Error Handling

- **Bundle fetch fails at boot**: Resolver reports which bundle URL failed, boot aborts with clear message
- **Missing auth bundle**: Shell's `LoginPage` shows config error pointing to `app.config.js`
- **Seed data fails**: Non-fatal, app boots without demo data, logs warning
- **Port in use**: Standard Express error with suggestion to set `PORT` env var

## Testing Strategy

- **`torque-app-todo` integration tests**: Boot the full app, verify all 4 bundles mount, API endpoints respond, UI routes exist
- **`torque new` scaffold tests**: Run generator with each combination of choices, verify output files are correct
- **`torque generate scaffold` tests**: Generate a bundle, verify manifest/logic/ui/test structure
- **Boot.js smoke test**: Verify the generated boot.js wires kernel → services → server correctly

## Open Questions

None — all sections validated.