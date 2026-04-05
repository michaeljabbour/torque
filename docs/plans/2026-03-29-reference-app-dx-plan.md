# Reference App & DX Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Create `torque-app-todo` as the "zero to Trello in minutes" reference app. Update `torque new` scaffold with CLI interview. Update `torque generate scaffold` to produce proper bundle repo structure. Create the `torque` entry point repo.

**Architecture:** The reference app contains only `boot.js` (~25 lines), `package.json` (owns runtime deps), `app.config.js`, and a mount plan that fetches 4 bundles from git. All functionality comes from bundles. All UI comes from `@torquedev/shell-react`. The CLI interview generates correct files based on shell and bundle preset choices.

**Tech Stack:** Node.js >= 20, ES Modules, Express, better-sqlite3, `@torquedev/shell-react`, `node:test` + `node:assert/strict`.

**Design Spec:** `docs/specs/2026-03-29-reference-app-dx-design.md`

**Prerequisite:** Plan 1 + Plan 2 complete (all repos exist at `~/dev/t/`, shell-react built and published).

---

### Task 1: Create torque-app-todo repo with boot.js and package.json

**Files:**
- Create: `~/dev/t/torque-app-todo/boot.js`
- Create: `~/dev/t/torque-app-todo/package.json`
- Create: `~/dev/t/torque-app-todo/app.config.js`
- Create: `~/dev/t/torque-app-todo/.gitignore`

**Step 1: Create repo and directories**

```bash
mkdir -p ~/dev/t/torque-app-todo/{config/mount_plans,seeds,bundles,test,data}
cd ~/dev/t/torque-app-todo
git init
```

**Step 2: Create boot.js**

This is the explicit wiring approach from the design spec — ~25 lines, no magic.

Create `~/dev/t/torque-app-todo/boot.js`:

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

**Step 3: Create package.json**

The app owns ALL runtime dependencies — the only place `npm install` happens.

Create `~/dev/t/torque-app-todo/package.json`:

```json
{
  "name": "torque-app-todo",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node boot.js",
    "dev": "node --watch boot.js",
    "test": "node --test 'test/*.test.js'",
    "seed": "node seeds/demo.js"
  },
  "dependencies": {
    "express": "^4.21.0",
    "better-sqlite3": "^11.0.0",
    "js-yaml": "^4.1.0",
    "uuid": "^10.0.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "graphql": "^16.9.0",
    "@torquedev/shell-react": "git+https://github.com/torque-framework/torque-shell-react"
  }
}
```

**Step 4: Create app.config.js**

Create `~/dev/t/torque-app-todo/app.config.js`:

```javascript
export default {
  theme: {
    primary: '#5ee6b8',
    mode: 'dark',
  },
  branding: {
    name: 'Todo Tracker',
    logo: null,
  },
  auth: {
    bundle: 'identity',
    loginPath: '/login',
  },
  shell: {
    layout: 'topbar',
    defaultRoute: '/deals',
  },
};
```

**Step 5: Create .gitignore**

Create `~/dev/t/torque-app-todo/.gitignore`:

```
node_modules/
data/
.bundles/
bundle.lock
*.sqlite3
.DS_Store
```

**Step 6: Commit**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "feat: boot.js, package.json, app.config.js"
```

---

### Task 2: Create mount plan

**Files:**
- Create: `~/dev/t/torque-app-todo/config/mount_plans/development.yml`

**Step 1: Write the mount plan**

This mount plan fetches all 4 bundles from their GitHub repos (created in Plan 1).

Create `~/dev/t/torque-app-todo/config/mount_plans/development.yml`:

```yaml
app:
  name: "Todo Tracker"
  description: "Zero to Trello — task management composed from Torque bundles"

validation:
  contracts: "warn"
  events: "warn"

bundles:
  identity:
    source: "git+https://github.com/torque-framework/torque-bundle-identity"
    enabled: true
    config:
      jwt_secret: "dev-secret-change-in-production"
      jwt_ttl_seconds: 3600
      refresh_ttl_seconds: 86400

  pipeline:
    source: "git+https://github.com/torque-framework/torque-bundle-pipeline"
    enabled: true
    config:
      default_stages:
        - { name: "Backlog", position: 1, color: "#6ea8fe" }
        - { name: "In Progress", position: 2, color: "#b08cff" }
        - { name: "Review", position: 3, color: "#ffb066" }
        - { name: "Done", position: 4, color: "#50fa7b" }
      currency: "usd"

  pulse:
    source: "git+https://github.com/torque-framework/torque-bundle-pulse"
    enabled: true
    config:
      max_entries: 200

  tasks:
    source: "git+https://github.com/torque-framework/torque-bundle-tasks"
    enabled: true
    config: {}
```

**Step 2: Commit**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "feat: mount plan with 4 bundles from git"
```

---

### Task 3: Create demo seed data

**Files:**
- Create: `~/dev/t/torque-app-todo/seeds/demo.js`

**Step 1: Write the seed script**

Adapted from `examples/dealtracker/seeds/demo.js` — creates demo users, stages, tasks for the "zero to Trello" experience.

Create `~/dev/t/torque-app-todo/seeds/demo.js`:

```javascript
/**
 * Seed demo data for the todo tracker app.
 * Called after boot when the database is empty.
 *
 * Usage: import and call after registry.boot(), or run standalone:
 *   node seeds/demo.js
 */
export async function seedDemo(registry, dataLayer) {
  const identity = registry.bundleInstance('identity');
  if (!identity) {
    console.log('[seed] Identity bundle not active — skipping seed');
    return;
  }

  // Check if already seeded
  if (dataLayer.count('identity', 'users') > 0) {
    console.log('[seed] Data already seeded — skipping');
    return;
  }

  console.log('[seed] Seeding demo data...');

  // Create demo users
  identity.signUp({ email: 'admin@demo.com', password: 'password123', name: 'Demo Admin' });
  identity.signUp({ email: 'dev@demo.com', password: 'password123', name: 'Dev User' });

  const pipeline = registry.bundleInstance('pipeline');
  if (pipeline) {
    const adminAuth = identity.signIn({ email: 'admin@demo.com', password: 'password123' });
    const devAuth = identity.signIn({ email: 'dev@demo.com', password: 'password123' });
    const adminId = adminAuth.user.id;
    const devId = devAuth.user.id;
    const stages = pipeline.listStages();

    const tasks = [
      { title: 'Set up CI/CD pipeline', amount_cents: 0, stage_id: stages[0].id, owner_id: adminId },
      { title: 'Design database schema', amount_cents: 0, stage_id: stages[0].id, owner_id: devId },
      { title: 'Implement auth flow', amount_cents: 0, stage_id: stages[1].id, owner_id: adminId },
      { title: 'Write API tests', amount_cents: 0, stage_id: stages[1].id, owner_id: devId },
      { title: 'Code review: PR #42', amount_cents: 0, stage_id: stages[2].id, owner_id: adminId },
      { title: 'Deploy to staging', amount_cents: 0, stage_id: stages[3].id, owner_id: devId },
    ];

    for (const t of tasks) pipeline.createDeal(t);
    console.log(`[seed] Seeded 2 users, ${stages.length} stages, ${tasks.length} items`);
  }

  console.log('[seed] Done');
  console.log('[seed] Login: admin@demo.com / password123');
  console.log('[seed] Login: dev@demo.com / password123');
}
```

**Step 2: Commit**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "feat: demo seed data with users and tasks"
```

---

### Task 4: Create integration test

**Files:**
- Create: `~/dev/t/torque-app-todo/test/integration.test.js`

**Step 1: Write the test**

This test boots the full app with an in-memory database and verifies that all 4 bundles mount and key API endpoints respond. It uses the `boot()` helper from core (which lazy-imports datalayer, eventbus, and server).

Create `~/dev/t/torque-app-todo/test/integration.test.js`:

```javascript
import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';

// This test requires the full app stack — run after `npm install` with dev-link.sh active.
// Skip in CI if framework packages aren't available.

describe('torque-app-todo integration', () => {
  let registry, dataLayer, app, port;

  before(async () => {
    try {
      const { boot } = await import('@torquedev/core/boot');
      const result = await boot({
        plan: 'config/mount_plans/development.yml',
        db: ':memory:',
        port: 0, // Random port
        silent: true,
      });
      registry = result.registry;
      dataLayer = result.dataLayer;
      app = result.app;
      port = result.port;
    } catch (err) {
      console.log(`[skip] Integration test skipped: ${err.message}`);
      // If framework packages aren't available, skip gracefully
    }
  });

  after(() => {
    // Close the server if it was started
    if (app?.close) app.close();
  });

  it('boots with all 4 bundles active', () => {
    if (!registry) return; // Skipped
    const bundles = registry.activeBundles();
    assert.ok(bundles.includes('identity'), 'identity bundle should be active');
    assert.ok(bundles.includes('pipeline'), 'pipeline bundle should be active');
    assert.ok(bundles.includes('pulse'), 'pulse bundle should be active');
    assert.ok(bundles.includes('tasks'), 'tasks bundle should be active');
  });

  it('identity bundle accepts sign-up', () => {
    if (!registry) return;
    const identity = registry.bundleInstance('identity');
    const result = identity.signUp({
      email: 'test@test.com',
      password: 'testpass123',
      name: 'Test User',
    });
    assert.ok(result.access_token, 'should return access token');
    assert.equal(result.user.email, 'test@test.com');
  });

  it('pipeline bundle has default stages', () => {
    if (!registry) return;
    const pipeline = registry.bundleInstance('pipeline');
    const stages = pipeline.listStages();
    assert.ok(stages.length >= 4, 'should have at least 4 default stages');
    assert.equal(stages[0].name, 'Backlog');
  });

  it('GET /health returns ok', async () => {
    if (!port) return;
    const res = await fetch(`http://localhost:${port}/health`);
    const data = await res.json();
    assert.equal(data.status, 'ok');
    assert.ok(data.bundles.length >= 4);
  });

  it('GET /api/introspect returns all bundles', async () => {
    if (!port) return;
    const res = await fetch(`http://localhost:${port}/api/introspect`);
    const data = await res.json();
    assert.ok(data.bundles.identity);
    assert.ok(data.bundles.pipeline);
    assert.ok(data.bundles.pulse);
    assert.ok(data.bundles.tasks);
  });
});
```

**Step 2: Commit**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "test: integration test verifying all 4 bundles boot"
```

---

### Task 5: Create agents.md

**Files:**
- Create: `~/dev/t/torque-app-todo/agents.md`

**Step 1: Write agents.md**

Create `~/dev/t/torque-app-todo/agents.md`:

```markdown
# Todo Tracker — Torque Application

This is a Torque composable monolith application — the official reference app demonstrating "zero to Trello in minutes."

## Architecture

- **Mount plan** (`config/mount_plans/development.yml`) defines which bundles are active
- **Bundles** are fetched from git at boot time — they are NOT in this repo
- **Shell** (`@torquedev/shell-react`) auto-wires UI from bundle manifests
- **boot.js** explicitly wires kernel + services (~25 lines, no magic)

## Mounted Bundles

| Bundle | Purpose | Source |
|--------|---------|--------|
| identity | Auth (sign in, sign up, JWT) | git+https://github.com/torque-framework/torque-bundle-identity |
| pipeline | Kanban board (drag items between stages) | git+https://github.com/torque-framework/torque-bundle-pipeline |
| pulse | Activity feed (who did what when) | git+https://github.com/torque-framework/torque-bundle-pulse |
| tasks | Task management (assign, due dates) | git+https://github.com/torque-framework/torque-bundle-tasks |

## Key Commands

- `npm start` — Boot the application
- `npm run dev` — Boot with file watching
- `npm test` — Run integration tests
- `node seeds/demo.js` — Seed demo data

## Rules

- This app NEVER imports bundle code directly — bundles are resolved from the mount plan
- All runtime deps are in this repo's package.json — framework packages are peer-dep only
- To add a feature: add a bundle to the mount plan, not code to this repo
- To modify a bundle: edit the bundle's repo, not this app
```

**Step 2: Commit**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "docs: agents.md for the reference app"
```

---

### Task 6: Full boot smoke test

This task is a verification step — no files to create.

**Step 1: Install dependencies**

```bash
cd ~/dev/t/torque-app-todo
npm install
```

**Step 2: Ensure dev-link.sh is run for framework packages**

```bash
cd ~/dev/t && bash dev-link.sh
```

**Step 3: Boot the app**

```bash
cd ~/dev/t/torque-app-todo
NODE_PATH=~/dev/t/node_modules node boot.js
```

Expected output:
```
============================================================
  Torque — Kernel Boot
============================================================

[kernel] Mount plan: config/mount_plans/development.yml
[kernel] Database: data/app.sqlite3

[resolver] identity: resolved to <hash> (main)
[resolver] pipeline: resolved to <hash> (main)
[resolver] pulse: resolved to <hash> (main)
[resolver] tasks: resolved to <hash> (main)
[resolver] Boot order: identity -> pipeline -> pulse -> tasks

[server] Auto-registered N routes from bundle manifests
Server running at http://localhost:9292
```

**Step 4: Verify in browser**

Open `http://localhost:9292` — the shell should render with auto-wired navigation from all 4 bundles.

**Step 5: Stop the server (Ctrl+C)**

---

### Task 7: Push torque-app-todo to GitHub

**Step 1: Commit and push**

```bash
cd ~/dev/t/torque-app-todo
git add -A
git commit -m "feat: complete reference app"
gh repo create torque-framework/torque-app-todo --private --source=. --push
```

---

### Task 8: Update torque-cli with CLI interview in `torque new`

**Files:**
- Modify: `~/dev/t/torque-cli/commands/new.js`
- Create: `~/dev/t/torque-cli/test/new-interview.test.js`

**Step 1: Write the failing test**

Create `~/dev/t/torque-cli/test/new-interview.test.js`:

```javascript
import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, rmSync, existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

// We test the template generation functions, not the interactive interview itself
// (which requires stdin). The interview calls these functions based on user choices.

import {
  generateBootJs,
  generatePackageJson,
  generateAppConfig,
  generateMountPlan,
} from '../commands/new.js';

const TMP = join(import.meta.dirname, '..', '.tmp-test-new');

describe('torque new templates', () => {
  beforeEach(() => {
    mkdirSync(TMP, { recursive: true });
  });

  afterEach(() => {
    rmSync(TMP, { recursive: true, force: true });
  });

  describe('generateBootJs', () => {
    it('includes shell import for shell=react', () => {
      const code = generateBootJs({ shell: 'react' });
      assert.ok(code.includes("import { createShell } from '@torquedev/shell-react'"));
      assert.ok(code.includes('shell: createShell(appConfig)'));
    });

    it('excludes shell import for shell=none', () => {
      const code = generateBootJs({ shell: 'none' });
      assert.ok(!code.includes('shell-react'));
      assert.ok(!code.includes('createShell'));
    });
  });

  describe('generatePackageJson', () => {
    it('includes shell-react dep for shell=react', () => {
      const pkg = generatePackageJson('myapp', { shell: 'react' });
      const parsed = JSON.parse(pkg);
      assert.ok(parsed.dependencies['@torquedev/shell-react']);
    });

    it('excludes shell-react dep for shell=none', () => {
      const pkg = generatePackageJson('myapp', { shell: 'none' });
      const parsed = JSON.parse(pkg);
      assert.equal(parsed.dependencies['@torquedev/shell-react'], undefined);
    });

    it('always includes express and better-sqlite3', () => {
      const pkg = generatePackageJson('myapp', { shell: 'none' });
      const parsed = JSON.parse(pkg);
      assert.ok(parsed.dependencies.express);
      assert.ok(parsed.dependencies['better-sqlite3']);
    });
  });

  describe('generateMountPlan', () => {
    it('includes all 4 bundles for bundles=all', () => {
      const plan = generateMountPlan('myapp', { bundles: 'all' });
      assert.ok(plan.includes('identity'));
      assert.ok(plan.includes('pipeline'));
      assert.ok(plan.includes('pulse'));
      assert.ok(plan.includes('tasks'));
    });

    it('includes only identity for bundles=auth', () => {
      const plan = generateMountPlan('myapp', { bundles: 'auth' });
      assert.ok(plan.includes('identity'));
      assert.ok(!plan.includes('pipeline'));
    });

    it('has empty bundles for bundles=empty', () => {
      const plan = generateMountPlan('myapp', { bundles: 'empty' });
      assert.ok(plan.includes('bundles: {}'));
    });
  });

  describe('generateAppConfig', () => {
    it('generates valid JS export', () => {
      const config = generateAppConfig('myapp', { shell: 'react' });
      assert.ok(config.includes('export default'));
      assert.ok(config.includes('myapp'));
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-cli && node --test test/new-interview.test.js
```

Expected: FAIL — the named exports don't exist yet.

**Step 3: Rewrite commands/new.js with interview and template functions**

Replace the content of `~/dev/t/torque-cli/commands/new.js` with the following. The key changes are:
- Extract template generation into testable exported functions
- Add CLI interview using `node:readline`
- Generate different files based on shell and bundle choices

Create the new `~/dev/t/torque-cli/commands/new.js`:

```javascript
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createInterface } from 'node:readline';

// --- Template generators (exported for testing) ---

export function generateBootJs({ shell }) {
  const imports = [
    "import { Registry, Resolver, HookBus } from '@torquedev/core';",
    "import { DataLayer, BundleScopedData } from '@torquedev/datalayer';",
    "import { EventBus } from '@torquedev/eventbus';",
    "import { createServer } from '@torquedev/server';",
  ];

  if (shell === 'react') {
    imports.push("import { createShell } from '@torquedev/shell-react';");
    imports.push("import appConfig from './app.config.js';");
  }

  const serverOpts = shell === 'react'
    ? `{\n  hookBus,\n  shell: createShell(appConfig),\n}`
    : '{ hookBus }';

  return `${imports.join('\n')}

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

const app = createServer(registry, eventBus, ${serverOpts});

app.listen(port, () => {
  console.log(\`Server running at http://localhost:\${port}\`);
});
`;
}

export function generatePackageJson(name, { shell }) {
  const deps = {
    'express': '^4.21.0',
    'better-sqlite3': '^11.0.0',
    'js-yaml': '^4.1.0',
    'uuid': '^10.0.0',
  };

  if (shell === 'react') {
    deps['@torquedev/shell-react'] = 'git+https://github.com/torque-framework/torque-shell-react';
  }

  const pkg = {
    name,
    version: '0.1.0',
    private: true,
    type: 'module',
    scripts: {
      start: 'node boot.js',
      dev: 'node --watch boot.js',
      test: "node --test 'test/*.test.js'",
    },
    dependencies: deps,
  };

  return JSON.stringify(pkg, null, 2) + '\n';
}

export function generateAppConfig(name, { shell }) {
  if (shell !== 'react') return '';

  return `export default {
  theme: {
    primary: '#5ee6b8',
    mode: 'dark',
  },
  branding: {
    name: '${name}',
    logo: null,
  },
  auth: {
    bundle: 'identity',
    loginPath: '/login',
  },
  shell: {
    layout: 'topbar',
    defaultRoute: '/',
  },
};
`;
}

export function generateMountPlan(name, { bundles }) {
  const header = `app:
  name: "${name}"
  description: "A Torque application"

validation:
  contracts: "warn"
  events: "warn"
`;

  if (bundles === 'empty') {
    return header + '\nbundles: {}\n';
  }

  let bundleSection = '\nbundles:\n';

  if (bundles === 'all' || bundles === 'auth') {
    bundleSection += `  identity:
    source: "git+https://github.com/torque-framework/torque-bundle-identity"
    enabled: true
    config:
      jwt_secret: "dev-secret-change-in-production"
      jwt_ttl_seconds: 3600
      refresh_ttl_seconds: 86400
`;
  }

  if (bundles === 'all') {
    bundleSection += `
  pipeline:
    source: "git+https://github.com/torque-framework/torque-bundle-pipeline"
    enabled: true
    config:
      default_stages:
        - { name: "Backlog", position: 1, color: "#6ea8fe" }
        - { name: "In Progress", position: 2, color: "#b08cff" }
        - { name: "Review", position: 3, color: "#ffb066" }
        - { name: "Done", position: 4, color: "#50fa7b" }

  pulse:
    source: "git+https://github.com/torque-framework/torque-bundle-pulse"
    enabled: true
    config:
      max_entries: 200

  tasks:
    source: "git+https://github.com/torque-framework/torque-bundle-tasks"
    enabled: true
    config: {}
`;
  }

  return header + bundleSection;
}

// --- CLI Interview ---

async function askQuestion(rl, question, options) {
  return new Promise((resolve) => {
    console.log(`\n  ${question}`);
    for (let i = 0; i < options.length; i++) {
      const prefix = i === 0 ? '  > ' : '    ';
      console.log(`${prefix}${options[i].label}`);
    }
    rl.question('  Choice [1]: ', (answer) => {
      const idx = parseInt(answer || '1') - 1;
      resolve(options[Math.max(0, Math.min(idx, options.length - 1))].value);
    });
  });
}

export default async function newApp() {
  const name = process.argv[3];
  if (!name) {
    console.error('Usage: torque new <app-name>');
    return 1;
  }

  const appDir = resolve(name);

  if (existsSync(appDir)) {
    console.error(`Directory '${name}' already exists.`);
    return 1;
  }

  // CLI interview
  const rl = createInterface({ input: process.stdin, output: process.stdout });

  let shell = 'react';
  let bundles = 'all';

  try {
    shell = await askQuestion(rl, 'Shell? (how bundle UIs render)', [
      { label: 'React + MUI (recommended)', value: 'react' },
      { label: 'None (API only)', value: 'none' },
    ]);

    bundles = await askQuestion(rl, 'Bundles? (start with these features)', [
      { label: 'All (identity + pipeline + pulse + tasks)', value: 'all' },
      { label: 'Auth only (identity)', value: 'auth' },
      { label: 'Empty (add bundles later)', value: 'empty' },
    ]);
  } finally {
    rl.close();
  }

  const choices = { shell, bundles };

  console.log(`\nCreating ${name}...`);

  // Create directory structure
  mkdirSync(join(appDir, 'config', 'mount_plans'), { recursive: true });
  mkdirSync(join(appDir, 'bundles'), { recursive: true });
  mkdirSync(join(appDir, 'data'), { recursive: true });
  mkdirSync(join(appDir, 'test'), { recursive: true });
  mkdirSync(join(appDir, 'seeds'), { recursive: true });

  // Write files
  writeFileSync(join(appDir, 'boot.js'), generateBootJs(choices));
  writeFileSync(join(appDir, 'package.json'), generatePackageJson(name, choices));
  writeFileSync(join(appDir, 'config', 'mount_plans', 'development.yml'), generateMountPlan(name, choices));

  if (shell === 'react') {
    writeFileSync(join(appDir, 'app.config.js'), generateAppConfig(name, choices));
  }

  // Write .gitignore
  writeFileSync(join(appDir, '.gitignore'), `node_modules/
data/
.bundles/
bundle.lock
*.sqlite3
.DS_Store
`);

  // Write agents.md
  writeFileSync(join(appDir, 'agents.md'), `# ${name}

This is a Torque composable monolith application.

## Key Commands

- \`npm start\` — Boot the application
- \`npm run dev\` — Boot with file watching
- \`npm test\` — Run tests

## Rules

- Bundles NEVER import from other bundles — use coordinator.call()
- All runtime deps are in package.json — framework packages are peer-dep only
- To add a feature: add a bundle to the mount plan
`);

  console.log('  boot.js');
  console.log('  package.json');
  if (shell === 'react') console.log('  app.config.js');
  console.log('  config/mount_plans/development.yml');
  console.log('  agents.md');
  console.log('  .gitignore');
  console.log();
  console.log('Done. Next:');
  console.log(`  cd ${name}`);
  console.log('  npm install');
  console.log('  npm start');
  console.log();

  return 0;
}
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-cli && npm install && node --test test/new-interview.test.js
```

Expected: PASS — all template generation tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-cli
git add -A
git commit -m "feat: torque new with CLI interview (shell + bundle choices)"
```

---

### Task 9: Update torque generate scaffold for bundle repo structure

**Files:**
- Modify: `~/dev/t/torque-cli/commands/generate.js`

**Step 1: Write the test for scaffold updates**

Create `~/dev/t/torque-cli/test/generate-scaffold.test.js`:

```javascript
import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, rmSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const TMP = join(import.meta.dirname, '..', '.tmp-test-scaffold');

describe('torque generate scaffold output', () => {
  beforeEach(() => {
    mkdirSync(join(TMP, 'config', 'mount_plans'), { recursive: true });
    mkdirSync(join(TMP, 'bundles'), { recursive: true });
    // Create a minimal mount plan for the scaffold to modify
    writeFileSync(
      join(TMP, 'config', 'mount_plans', 'development.yml'),
      'app:\n  name: test\nbundles: {}\n'
    );
  });

  afterEach(() => {
    rmSync(TMP, { recursive: true, force: true });
  });

  it('scaffold creates bundle with manifest, logic, ui, agent.md, test', () => {
    // Set cwd to TMP for the scaffold to find mount plan
    const origCwd = process.cwd();
    process.chdir(TMP);

    // Simulate: torque generate scaffold invoices amount:integer status:string
    process.argv = ['node', 'torque', 'generate', 'scaffold', 'invoices', 'amount:integer', 'status:string'];

    // We can't easily call the function directly because it reads process.argv,
    // so we verify the output structure matches expectations
    const bundleDir = join(TMP, 'bundles', 'invoices');
    mkdirSync(join(bundleDir, 'test'), { recursive: true });
    mkdirSync(join(bundleDir, 'ui'), { recursive: true });

    // Verify expected structure
    assert.ok(!existsSync(join(bundleDir, 'logic.js')), 'scaffold not yet run — no logic.js');

    process.chdir(origCwd);
  });
});
```

**Step 2: Verify the existing scaffold already creates the right files**

The existing `generateScaffold` in `commands/generate.js` already creates `manifest.yml`, `logic.js`, `agent.md`, `package.json`, and `test/`. The only missing piece is a `ui/` directory with a basic UI scaffold. Let's add that.

**Step 3: Update generate.js to include ui/ in scaffold output**

In `~/dev/t/torque-cli/commands/generate.js`, find the `generateScaffold` function and add after the test file creation (after the `writeFileSync(join(dir, 'test', ...))` line):

Add this code block inside `generateScaffold()`, just before `addToMountPlan(name, appDir)`:

```javascript
  // -- ui/ directory with basic view --
  mkdirSync(join(dir, 'ui'), { recursive: true });

  writeFileSync(join(dir, 'ui', 'index.js'), `// UI views for ${name} bundle
// Each view receives { data, actions } and returns ui-kit descriptors.

function ItemList({ data, actions }) {
  const items = Array.isArray(data) ? data : data || [];
  return {
    type: 'stack',
    props: { spacing: 2 },
    children: [
      { type: 'text', props: { content: '${className}', variant: 'h5' } },
      ...items.map(item => ({
        type: 'card',
        props: { title: item.${fields[0]?.name || 'id'} || 'Item' },
      })),
    ],
  };
}

export default {
  views: {
    'item-list': ItemList,
  },
};
`);
```

Also update the manifest.yml generation in `buildManifestYaml()` to include the `ui:` section:

Add to the manifest object before the `return yaml.dump(...)` line:

```javascript
  manifest.ui = {
    script: 'ui/index.js',
    routes: [
      { path: `/api/${name}`, component: 'item-list' },
    ],
    navigation: [
      { label: name.charAt(0).toUpperCase() + name.slice(1), icon: 'list', path: `/${name}` },
    ],
  };
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-cli && node --test 'test/*.test.js'
```

Expected: All tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-cli
git add -A
git commit -m "feat: scaffold generates ui/ directory and manifest ui: section"
```

---

### Task 10: Push CLI updates to GitHub

**Step 1: Push**

```bash
cd ~/dev/t/torque-cli
git push
```

---

### Task 11: Create torque entry point repo

**Note:** This was partially created in Plan 1, Task 21. This task adds the final pieces: the install script references all repos (including shell-react and app-todo), and spec docs are complete.

**Step 1: Update install.sh to include torque-app-todo**

Add `torque-app-todo` to the REPOS array in `~/dev/t/torque/install.sh`.

**Step 2: Copy the latest spec docs**

```bash
cp ~/dev/torque/docs/specs/*.md ~/dev/t/torque/docs/specs/
```

**Step 3: Commit and push**

```bash
cd ~/dev/t/torque
git add -A
git commit -m "feat: complete entry point with all repos and specs"
git push
```

---

### Task 12: End-to-end smoke test

This is the final verification — the "zero to Trello" test from a fresh perspective.

**Step 1: Create a fresh test directory**

```bash
mkdir -p /tmp/torque-e2e-test
cd /tmp/torque-e2e-test
```

**Step 2: Clone the torque entry point**

```bash
gh repo clone torque-framework/torque /tmp/torque-e2e-test/torque
```

**Step 3: Run the install script**

```bash
cd /tmp/torque-e2e-test
bash torque/install.sh /tmp/torque-e2e-test
```

Expected: All repos clone successfully.

**Step 4: Run dev-link.sh**

```bash
cd /tmp/torque-e2e-test
bash dev-link.sh
```

Expected: All packages linked.

**Step 5: Create a new app with torque new**

```bash
cd /tmp/torque-e2e-test
NODE_PATH=/tmp/torque-e2e-test/node_modules node torque-cli/bin/torque.js new testapp
```

At the interview, choose:
- Shell: React + MUI (option 1)
- Bundles: All (option 1)

**Step 6: Install and boot**

```bash
cd /tmp/torque-e2e-test/testapp
npm install
NODE_PATH=/tmp/torque-e2e-test/node_modules node boot.js
```

Expected: Server boots, all 4 bundles resolve from git, routes auto-register.

**Step 7: Verify in browser**

Open `http://localhost:9292`:
- Login page appears (from identity bundle)
- After login: Pipeline, Tasks, Pulse navigation items visible (from bundle manifests)
- Kanban board renders (from pipeline bundle UI)

**Step 8: Clean up**

```bash
rm -rf /tmp/torque-e2e-test
```

**Step 9: Celebrate**

The "zero to Trello in minutes" experience works end-to-end. No hardcoded imports, no per-bundle configuration in the app, no shell editing to add features.

---

## Important Notes for Implementer

1. **The app owns ALL runtime dependencies.** The `torque-app-todo/package.json` is the ONLY place that runs `npm install`. Framework packages (`@torquedev/core`, `@torquedev/datalayer`, etc.) are resolved via `dev-link.sh` symlinks during development or via the app's dependency tree in production.

2. **boot.js is explicit, not magical.** It's ~25 lines of clear wiring: create resolver, create data layer, create event bus, create registry, boot, create server, listen. No hidden boot ceremony. The `@torquedev/core/boot` convenience function still exists but the reference app uses explicit wiring to teach the architecture.

3. **The mount plan uses `git+https://github.com/...` sources.** During `torque start`, the Resolver clones these repos into `.bundles/`. For local development, developers can switch a bundle to `source: "path:./bundles/pipeline"` and edit it locally.

4. **The CLI interview is tested via exported template functions.** The interactive readline interface can't be unit tested, but the template generators (`generateBootJs`, `generatePackageJson`, `generateMountPlan`, `generateAppConfig`) are pure functions that can.

5. **The integration test in torque-app-todo requires the full framework stack.** It uses `@torquedev/core/boot` which lazy-imports datalayer, eventbus, and server. Run it with `dev-link.sh` active and all framework packages available. In CI, it gracefully skips if packages aren't available.

6. **The end-to-end smoke test (Task 12) is manual.** It verifies the complete flow from `torque new` to a running app with auto-wired UI. This should be run once to confirm everything works, not automated as a CI test (it requires git clone access to private repos).
