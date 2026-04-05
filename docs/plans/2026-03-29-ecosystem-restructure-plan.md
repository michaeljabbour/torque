# Ecosystem Restructure Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Split the monorepo at `~/dev/torque` into 23 independent repos at `~/dev/t/`, each with isolated tests, correct dependency posture, and pushed to private GitHub repos under `torque-framework/*`.

**Architecture:** Fresh `git init` per repo — no history preserved. Each repo gets source extracted from the monorepo, a `package.json` with the correct dependency posture (zero deps, peer deps, or app-owns-all), and is pushed to GitHub. A lightweight `dev-link.sh` script provides cross-repo symlinks for local development.

**Tech Stack:** Node.js >= 20, ES Modules (`"type": "module"`), `node:test` + `node:assert/strict`, SQLite via `better-sqlite3`, Express, `gh` CLI for GitHub repo creation.

**Design Spec:** `docs/specs/2026-03-29-ecosystem-restructure-design.md`

---

## Phase 0: Infrastructure

### Task 1: Create workspace directory and dev-link.sh

**Files:**
- Create: `~/dev/t/dev-link.sh`

**Step 1: Create the workspace directory**

```bash
mkdir -p ~/dev/t
```

**Step 2: Write dev-link.sh**

Create `~/dev/t/dev-link.sh` with the following content:

```bash
#!/usr/bin/env bash
# dev-link.sh — Creates @torquedev/* symlinks for local cross-repo development.
# Run from ~/dev/t/ after cloning all repos.
# Delete node_modules/@torque to reset.

set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
LINK_DIR="$WORKSPACE/node_modules/@torque"

echo "[dev-link] Workspace: $WORKSPACE"

rm -rf "$LINK_DIR"
mkdir -p "$LINK_DIR"

# Map: npm package name -> repo directory name
declare -A PACKAGES=(
  [core]=torque-core
  [datalayer]=torque-service-datalayer
  [eventbus]=torque-service-eventbus
  [server]=torque-service-server
  [ui-kit]=torque-ui-kit
  [cli]=torque-cli
  [test-helpers]=torque-test-helpers
  [authorization]=torque-ext-authorization
  [datalayer-soft-delete]=torque-ext-soft-delete
  [eventbus-async]=torque-ext-async-events
  [search]=torque-ext-search
  [storage]=torque-ext-storage
  [shell-react]=torque-shell-react
)

for pkg in "${!PACKAGES[@]}"; do
  repo="${PACKAGES[$pkg]}"
  target="$WORKSPACE/$repo"
  if [ -d "$target" ]; then
    ln -sf "$target" "$LINK_DIR/$pkg"
    echo "  @torquedev/$pkg -> $repo/"
  else
    echo "  @torquedev/$pkg -> MISSING ($repo/)"
  fi
done

echo "[dev-link] Done. ${#PACKAGES[@]} packages linked."
echo "[dev-link] Usage: NODE_PATH=$WORKSPACE/node_modules node your-script.js"
```

**Step 3: Make it executable**

```bash
chmod +x ~/dev/t/dev-link.sh
```

**Step 4: Verify it runs (with no repos yet)**

Run: `cd ~/dev/t && bash dev-link.sh`

Expected: Script runs, prints "MISSING" for all packages since no repos exist yet.

**Step 5: Commit**

No commit needed yet — this is a standalone script in the workspace root.

---

## Phase 1: Kernel

### Task 2: Extract torque-core

**Files:**
- Create: `~/dev/t/torque-core/` (new repo)
- Source: `packages/core/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-core
cd ~/dev/t/torque-core
git init

# Copy source files from monorepo
cp -r ~/dev/torque/packages/core/kernel ~/dev/t/torque-core/kernel
cp ~/dev/torque/packages/core/index.js ~/dev/t/torque-core/index.js
cp ~/dev/torque/packages/core/boot.js ~/dev/t/torque-core/boot.js
cp -r ~/dev/torque/packages/core/test ~/dev/t/torque-core/test
```

The file tree will be:
```
torque-core/
├── kernel/
│   ├── resolver/
│   │   ├── cache.js
│   │   ├── deps.js
│   │   ├── git.js
│   │   ├── lock.js
│   │   └── path.js
│   ├── errors.js
│   ├── hooks.js
│   ├── registry.js
│   └── resolver.js
├── test/
│   ├── deps.test.js
│   ├── errors.test.js
│   ├── hooks.test.js
│   ├── lock.test.js
│   ├── registry-boot-preparsed.test.js
│   ├── registry-errors.test.js
│   ├── registry.test.js
│   ├── resolver-deps.test.js
│   ├── resolver.test.js
│   └── validation-modes.test.js
├── index.js
└── boot.js
```

**Step 2: Create package.json**

Create `~/dev/t/torque-core/package.json`:

```json
{
  "name": "@torquedev/core",
  "version": "0.1.0",
  "description": "Torque kernel: Registry, Resolver, HookBus for composable monolith applications",
  "type": "module",
  "main": "index.js",
  "exports": {
    ".": "./index.js",
    "./boot": "./boot.js"
  },
  "keywords": ["torque", "composable", "monolith", "framework", "kernel"],
  "license": "MIT",
  "dependencies": {
    "js-yaml": "^4.1.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

Create `~/dev/t/torque-core/.gitignore`:

```
node_modules/
data/
.bundles/
bundle.lock
*.sqlite3
.DS_Store
.tmp-test-deps/
```

**Step 4: Install dependencies and run tests**

```bash
cd ~/dev/t/torque-core
npm install
node --test 'test/*.test.js'
```

Expected: All core tests pass. The core package has `js-yaml` as its only dependency and all tests use local mocks — no cross-repo imports needed.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-core
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-core --private --source=. --push
```

---

## Phase 2: Services + UI Kit + Test Helpers (parallel)

### Task 3: Extract torque-service-datalayer

**Files:**
- Create: `~/dev/t/torque-service-datalayer/` (new repo)
- Source: `packages/datalayer/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-service-datalayer
cd ~/dev/t/torque-service-datalayer
git init

cp ~/dev/torque/packages/datalayer/index.js ~/dev/t/torque-service-datalayer/index.js
cp -r ~/dev/torque/packages/datalayer/test ~/dev/t/torque-service-datalayer/test
```

The file tree will be:
```
torque-service-datalayer/
├── test/
│   ├── datalayer.test.js
│   └── transaction.test.js
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

The monorepo version has `better-sqlite3` and `uuid` as `dependencies`. In the multi-repo world, these become `peerDependencies` — the app provides them. For isolated testing, we add them as `devDependencies`.

Create `~/dev/t/torque-service-datalayer/package.json`:

```json
{
  "name": "@torquedev/datalayer",
  "version": "0.1.0",
  "description": "Torque data layer with bundle-scoped SQLite storage",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "better-sqlite3": ">=11.0.0",
    "uuid": ">=10.0.0"
  },
  "devDependencies": {
    "better-sqlite3": "^11.0.0",
    "uuid": "^10.0.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

Create `~/dev/t/torque-service-datalayer/.gitignore`:

```
node_modules/
data/
*.sqlite3
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-service-datalayer
npm install
node --test 'test/*.test.js'
```

Expected: All datalayer tests pass. The tests create in-memory SQLite databases — no cross-repo imports needed.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-service-datalayer
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-service-datalayer --private --source=. --push
```

---

### Task 4: Extract torque-service-eventbus

**Files:**
- Create: `~/dev/t/torque-service-eventbus/` (new repo)
- Source: `packages/eventbus/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-service-eventbus
cd ~/dev/t/torque-service-eventbus
git init

cp ~/dev/torque/packages/eventbus/index.js ~/dev/t/torque-service-eventbus/index.js
cp -r ~/dev/torque/packages/eventbus/test ~/dev/t/torque-service-eventbus/test
```

File tree:
```
torque-service-eventbus/
├── test/
│   ├── contract-violation-error.test.js
│   └── eventbus.test.js
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

The eventbus imports `ContractViolationError` from `@torquedev/core`. In the multi-repo world, this is a peer dependency. For isolated test execution, we need to handle this import.

Create `~/dev/t/torque-service-eventbus/package.json`:

```json
{
  "name": "@torquedev/eventbus",
  "version": "0.1.0",
  "description": "Torque event bus with durable persistence and contract validation",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/core": ">=0.1.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

Create `~/dev/t/torque-service-eventbus/.gitignore`:

```
node_modules/
data/
*.sqlite3
.DS_Store
```

**Step 4: Handle the @torquedev/core import for isolated testing**

The `index.js` starts with `import { ContractViolationError } from '@torquedev/core';`. For tests to pass in isolation, we need to create a local mock of this import. Create a directory structure that satisfies this:

```bash
mkdir -p ~/dev/t/torque-service-eventbus/node_modules/@torquedev/core
```

Create `~/dev/t/torque-service-eventbus/node_modules/@torquedev/core/index.js`:

```javascript
// Test-only mock of @torquedev/core for isolated eventbus testing
export class ContractViolationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ContractViolationError';
    this.code = 'CONTRACT_VIOLATION';
  }
}
```

Add `!node_modules/@torquedev/` to `.gitignore` so this test mock is tracked:

Update `~/dev/t/torque-service-eventbus/.gitignore` to:

```
node_modules/
!node_modules/@torquedev/
data/
*.sqlite3
.DS_Store
```

**Step 5: Run tests**

```bash
cd ~/dev/t/torque-service-eventbus
node --test 'test/*.test.js'
```

Expected: All eventbus tests pass. The tests create an EventBus with `{}` (no db) — the only cross-repo import is ContractViolationError which is now mocked.

**Step 6: Commit and push**

```bash
cd ~/dev/t/torque-service-eventbus
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-service-eventbus --private --source=. --push
```

---

### Task 5: Extract torque-service-server

**Files:**
- Create: `~/dev/t/torque-service-server/` (new repo)
- Source: `packages/server/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-service-server
cd ~/dev/t/torque-service-server
git init

cp ~/dev/torque/packages/server/index.js ~/dev/t/torque-service-server/index.js
cp -r ~/dev/torque/packages/server/test ~/dev/t/torque-service-server/test
```

File tree:
```
torque-service-server/
├── test/
│   ├── frontend-spa.test.js
│   └── server.test.js
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/server",
  "version": "0.1.0",
  "description": "Torque HTTP server with auto-registered bundle routes and SPA serving",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "express": ">=4.21.0"
  },
  "devDependencies": {
    "express": "^4.21.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
data/
*.sqlite3
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-service-server
npm install
node --test 'test/*.test.js'
```

Expected: All server tests pass. The tests use mock registries and event buses — no cross-repo imports in test files. The source `index.js` imports only `express` which is provided as a dev dependency.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-service-server
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-service-server --private --source=. --push
```

---

### Task 6: Extract torque-ui-kit

**Files:**
- Create: `~/dev/t/torque-ui-kit/` (new repo)
- Source: `packages/ui-kit/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ui-kit
cd ~/dev/t/torque-ui-kit
git init

# Copy all source files (multiple .js files at root + src/ + test/)
cp ~/dev/torque/packages/ui-kit/index.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/create-element.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/custom.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/data-display.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/data-table.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/feedback.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/inputs.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/layout.js ~/dev/t/torque-ui-kit/
cp ~/dev/torque/packages/ui-kit/navigation.js ~/dev/t/torque-ui-kit/
cp -r ~/dev/torque/packages/ui-kit/src ~/dev/t/torque-ui-kit/src
cp -r ~/dev/torque/packages/ui-kit/test ~/dev/t/torque-ui-kit/test
```

File tree:
```
torque-ui-kit/
├── src/
│   └── utils/
│       └── formatTimeAgo.js
├── test/
│   └── *.test.js
├── create-element.js
├── custom.js
├── data-display.js
├── data-table.js
├── feedback.js
├── index.js
├── inputs.js
├── layout.js
├── navigation.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/ui-kit",
  "version": "0.1.0",
  "description": "Torque UI component kit with declarative element descriptors",
  "type": "module",
  "main": "index.js",
  "exports": {
    ".": "./index.js"
  },
  "license": "MIT",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-ui-kit
node --test 'test/*.test.js'
```

Expected: All ui-kit tests pass. Zero dependencies — pure JS descriptor functions.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ui-kit
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ui-kit --private --source=. --push
```

---

### Task 7: Extract torque-test-helpers

**Files:**
- Create: `~/dev/t/torque-test-helpers/` (new repo)
- Source: `packages/test-helpers/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-test-helpers
cd ~/dev/t/torque-test-helpers
git init

cp ~/dev/torque/packages/test-helpers/index.js ~/dev/t/torque-test-helpers/index.js
```

File tree:
```
torque-test-helpers/
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/test-helpers",
  "version": "0.1.0",
  "description": "Shared test mock factories for Torque bundles",
  "type": "module",
  "main": "index.js",
  "license": "MIT"
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Write a smoke test**

Create `~/dev/t/torque-test-helpers/test/smoke.test.js`:

```javascript
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createMockData, createMockEvents, createMockCoordinator, createSpyCoordinator } from '../index.js';

describe('test-helpers', () => {
  it('createMockData supports insert/find/query', () => {
    const data = createMockData();
    const record = data.insert('items', { name: 'test' });
    assert.ok(record.id);
    assert.equal(record.name, 'test');

    const found = data.find('items', record.id);
    assert.equal(found.name, 'test');

    const all = data.query('items');
    assert.equal(all.length, 1);
  });

  it('createMockEvents captures published events', () => {
    const events = createMockEvents();
    events.publish('test.event', { key: 'value' });
    assert.equal(events._published.length, 1);
    assert.equal(events._published[0].name, 'test.event');
  });

  it('createMockCoordinator returns canned responses', async () => {
    const coordinator = createMockCoordinator({
      'identity.getUser': () => ({ id: 'u1', name: 'Test' }),
    });
    const result = await coordinator.call('identity', 'getUser', {});
    assert.equal(result.name, 'Test');
  });

  it('createSpyCoordinator tracks calls', async () => {
    const coordinator = createSpyCoordinator({
      'pipeline.getDeal': () => ({ id: 'd1' }),
    });
    await coordinator.call('pipeline', 'getDeal', { dealId: 'd1' });
    assert.equal(coordinator._calls.length, 1);
    assert.equal(coordinator._calls[0].bundle, 'pipeline');
  });
});
```

**Step 5: Run test**

```bash
cd ~/dev/t/torque-test-helpers
node --test 'test/*.test.js'
```

Expected: PASS — all 4 tests.

**Step 6: Commit and push**

```bash
cd ~/dev/t/torque-test-helpers
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-test-helpers --private --source=. --push
```

---

## Phase 3: CLI + Foundation (parallel)

### Task 8: Extract torque-cli

**Files:**
- Create: `~/dev/t/torque-cli/` (new repo)
- Source: `packages/cli/` + `packages/create-app/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-cli
cd ~/dev/t/torque-cli
git init

# Copy CLI source
cp -r ~/dev/torque/packages/cli/bin ~/dev/t/torque-cli/bin
cp -r ~/dev/torque/packages/cli/commands ~/dev/t/torque-cli/commands
cp -r ~/dev/torque/packages/cli/lib ~/dev/t/torque-cli/lib
cp -r ~/dev/torque/packages/cli/test ~/dev/t/torque-cli/test

# Copy create-app as a subcommand module
cp ~/dev/torque/packages/create-app/index.js ~/dev/t/torque-cli/create-app.js
```

File tree:
```
torque-cli/
├── bin/
│   └── torque.js
├── commands/
│   ├── clean.js
│   ├── console.js
│   ├── context.js
│   ├── dev.js
│   ├── doctor.js
│   ├── generate.js
│   ├── info.js
│   ├── list.js
│   ├── new.js
│   ├── recipe.js
│   ├── start.js
│   ├── update.js
│   └── validate.js
├── lib/
│   ├── plans.js
│   ├── port.js
│   └── workspace.js
├── test/
│   └── *.test.js
├── create-app.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/cli",
  "version": "0.1.0",
  "description": "Torque command-line interface for server management and code generation",
  "type": "module",
  "bin": {
    "torque": "./bin/torque.js"
  },
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/core": ">=0.1.0"
  },
  "dependencies": {
    "js-yaml": "^4.1.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
data/
.bundles/
bundle.lock
*.sqlite3
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-cli
npm install
node --test 'test/*.test.js'
```

Expected: CLI tests pass. The generate and new commands use only `node:fs` and `js-yaml` — no kernel imports in test execution paths.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-cli
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-cli --private --source=. --push
```

---

### Task 9: Extract torque-foundation

**Files:**
- Create: `~/dev/t/torque-foundation/` (new repo)
- Source: `foundation/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-foundation
cd ~/dev/t/torque-foundation
git init

# Copy all foundation content
cp -r ~/dev/torque/foundation/agents ~/dev/t/torque-foundation/agents
cp -r ~/dev/torque/foundation/behaviors ~/dev/t/torque-foundation/behaviors
cp -r ~/dev/torque/foundation/catalog ~/dev/t/torque-foundation/catalog
cp -r ~/dev/torque/foundation/context ~/dev/t/torque-foundation/context
cp -r ~/dev/torque/foundation/mount-plans ~/dev/t/torque-foundation/mount-plans
cp -r ~/dev/torque/foundation/recipes ~/dev/t/torque-foundation/recipes
cp -r ~/dev/torque/foundation/skills ~/dev/t/torque-foundation/skills
```

File tree:
```
torque-foundation/
├── agents/
├── behaviors/
├── catalog/
├── context/
├── mount-plans/
├── recipes/
├── skills/
└── .gitignore
```

**Step 2: Create .gitignore**

```
.DS_Store
```

**Step 3: No tests needed — git-only repo with no npm package**

**Step 4: Commit and push**

```bash
cd ~/dev/t/torque-foundation
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-foundation --private --source=. --push
```

---

## Phase 4: Extensions (parallel)

### Task 10: Extract torque-ext-authorization

**Files:**
- Create: `~/dev/t/torque-ext-authorization/` (new repo)
- Source: `packages/authorization/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ext-authorization
cd ~/dev/t/torque-ext-authorization
git init

cp ~/dev/torque/packages/authorization/index.js ~/dev/t/torque-ext-authorization/
cp ~/dev/torque/packages/authorization/checks.js ~/dev/t/torque-ext-authorization/
cp ~/dev/torque/packages/authorization/errors.js ~/dev/t/torque-ext-authorization/
cp -r ~/dev/torque/packages/authorization/test ~/dev/t/torque-ext-authorization/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/authorization",
  "version": "0.1.0",
  "description": "Authorization extension for Torque — role-based access checks",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/core": ">=0.1.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-ext-authorization
node --test 'test/*.test.js'
```

Expected: Tests pass. The current `package.json` shows `"dependencies": {}` — the source has zero imports from `@torquedev/core` (the checks use pure functions).

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ext-authorization
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ext-authorization --private --source=. --push
```

---

### Task 11: Extract torque-ext-soft-delete

**Files:**
- Create: `~/dev/t/torque-ext-soft-delete/` (new repo)
- Source: `packages/datalayer-soft-delete/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ext-soft-delete
cd ~/dev/t/torque-ext-soft-delete
git init

cp ~/dev/torque/packages/datalayer-soft-delete/index.js ~/dev/t/torque-ext-soft-delete/
cp -r ~/dev/torque/packages/datalayer-soft-delete/test ~/dev/t/torque-ext-soft-delete/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/datalayer-soft-delete",
  "version": "0.1.0",
  "description": "Soft-delete enhancement for @torquedev/datalayer. Apply these methods to BundleScopedData.",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/datalayer": ">=0.1.0"
  },
  "devDependencies": {
    "better-sqlite3": "^12.8.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-ext-soft-delete
npm install
node --test 'test/*.test.js'
```

Expected: Tests pass — uses `better-sqlite3` directly for in-memory tests.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ext-soft-delete
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ext-soft-delete --private --source=. --push
```

---

### Task 12: Extract torque-ext-async-events

**Files:**
- Create: `~/dev/t/torque-ext-async-events/` (new repo)
- Source: `packages/eventbus-async/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ext-async-events
cd ~/dev/t/torque-ext-async-events
git init

cp ~/dev/torque/packages/eventbus-async/index.js ~/dev/t/torque-ext-async-events/
cp ~/dev/torque/packages/eventbus-async/async-queue.js ~/dev/t/torque-ext-async-events/
cp -r ~/dev/torque/packages/eventbus-async/test ~/dev/t/torque-ext-async-events/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/eventbus-async",
  "version": "0.1.0",
  "description": "Async job queue enhancement for @torquedev/eventbus. Adds subscribeAsync() with retry logic.",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/eventbus": ">=0.1.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```

Expected: Tests pass — the current package has `"dependencies": {}` meaning no external imports.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ext-async-events
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ext-async-events --private --source=. --push
```

---

### Task 13: Extract torque-ext-search

**Files:**
- Create: `~/dev/t/torque-ext-search/` (new repo)
- Source: `packages/search/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ext-search
cd ~/dev/t/torque-ext-search
git init

cp ~/dev/torque/packages/search/index.js ~/dev/t/torque-ext-search/
cp -r ~/dev/torque/packages/search/adapters ~/dev/t/torque-ext-search/
cp -r ~/dev/torque/packages/search/test ~/dev/t/torque-ext-search/
```

File tree:
```
torque-ext-search/
├── adapters/
│   └── fts5.js
├── test/
│   └── *.test.js
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/search",
  "version": "0.1.0",
  "description": "Full-text search extension for Torque using SQLite FTS5",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/core": ">=0.1.0",
    "better-sqlite3": ">=11.0.0"
  },
  "devDependencies": {
    "better-sqlite3": "^12.8.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-ext-search
npm install
node --test 'test/*.test.js'
```

Expected: Tests pass — uses `better-sqlite3` directly for FTS5 testing.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ext-search
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ext-search --private --source=. --push
```

---

### Task 14: Extract torque-ext-storage

**Files:**
- Create: `~/dev/t/torque-ext-storage/` (new repo)
- Source: `packages/storage/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-ext-storage
cd ~/dev/t/torque-ext-storage
git init

cp ~/dev/torque/packages/storage/index.js ~/dev/t/torque-ext-storage/
cp -r ~/dev/torque/packages/storage/adapters ~/dev/t/torque-ext-storage/
cp -r ~/dev/torque/packages/storage/test ~/dev/t/torque-ext-storage/
```

File tree:
```
torque-ext-storage/
├── adapters/
│   └── local.js
├── test/
│   └── *.test.js
├── index.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/storage",
  "version": "0.1.0",
  "description": "File storage extension for Torque with local adapter",
  "type": "module",
  "main": "index.js",
  "license": "MIT",
  "peerDependencies": {
    "@torquedev/core": ">=0.1.0"
  },
  "devDependencies": {
    "better-sqlite3": "^12.8.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-ext-storage
npm install
node --test 'test/*.test.js'
```

Expected: Tests pass.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-ext-storage
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-ext-storage --private --source=. --push
```

---

## Phase 5: Bundles (parallel)

All bundles follow the same pattern: zero declared dependencies, receive everything via constructor injection `{ data, events, config, coordinator }`. Tests use inline mocks (same pattern as `@torquedev/test-helpers`).

### Task 15: Extract torque-bundle-identity

**Files:**
- Create: `~/dev/t/torque-bundle-identity/` (new repo)
- Source: `examples/bundles/identity/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-bundle-identity
cd ~/dev/t/torque-bundle-identity
git init

cp ~/dev/torque/examples/bundles/identity/manifest.yml ~/dev/t/torque-bundle-identity/
cp ~/dev/torque/examples/bundles/identity/logic.js ~/dev/t/torque-bundle-identity/
cp ~/dev/torque/examples/bundles/identity/agent.md ~/dev/t/torque-bundle-identity/
cp -r ~/dev/torque/examples/bundles/identity/ui ~/dev/t/torque-bundle-identity/
cp -r ~/dev/torque/examples/bundles/identity/test ~/dev/t/torque-bundle-identity/
```

File tree:
```
torque-bundle-identity/
├── ui/
│   ├── LoginForm.js
│   └── index.js
├── test/
│   └── *.test.js
├── logic.js
├── manifest.yml
├── agent.md
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

The monorepo version has `bcryptjs`, `jsonwebtoken`, `uuid`, `@torquedev/ui-kit` as dependencies. In the multi-repo world, the identity bundle gets everything via injection — these runtime deps are provided by the app. For isolated testing, the logic.js imports `bcrypt`, `jwt`, and `uuid` directly, so they need to be devDependencies. The `@torquedev/ui-kit` import in `ui/` files is only used at runtime (loaded by the shell), not in tests.

```json
{
  "name": "@torquedev/bundle-identity",
  "version": "0.1.0",
  "description": "Authentication, sessions, JWT lifecycle",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "devDependencies": {
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "uuid": "^10.0.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-bundle-identity
npm install
node --test 'test/*.test.js'
```

Expected: Tests pass — the identity logic.js imports bcrypt/jwt/uuid directly (now devDependencies), and tests use inline mock data/events/coordinator.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-bundle-identity
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-bundle-identity --private --source=. --push
```

---

### Task 16: Extract torque-bundle-pipeline

**Files:**
- Create: `~/dev/t/torque-bundle-pipeline/` (new repo)
- Source: `examples/bundles/pipeline/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-bundle-pipeline
cd ~/dev/t/torque-bundle-pipeline
git init

cp ~/dev/torque/examples/bundles/pipeline/manifest.yml ~/dev/t/torque-bundle-pipeline/
cp ~/dev/torque/examples/bundles/pipeline/logic.js ~/dev/t/torque-bundle-pipeline/
cp ~/dev/torque/examples/bundles/pipeline/agent.md ~/dev/t/torque-bundle-pipeline/
cp -r ~/dev/torque/examples/bundles/pipeline/ui ~/dev/t/torque-bundle-pipeline/
cp -r ~/dev/torque/examples/bundles/pipeline/test ~/dev/t/torque-bundle-pipeline/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/bundle-pipeline",
  "version": "0.1.0",
  "description": "Stage-based workflow engine for deals, tickets, or any item-through-stages process",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-bundle-pipeline
node --test 'test/*.test.js'
```

Expected: Tests pass — pipeline has zero imports (receives everything via constructor injection), tests use inline mocks.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-bundle-pipeline
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-bundle-pipeline --private --source=. --push
```

---

### Task 17: Extract torque-bundle-pulse

**Files:**
- Create: `~/dev/t/torque-bundle-pulse/` (new repo)
- Source: `examples/bundles/pulse/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-bundle-pulse
cd ~/dev/t/torque-bundle-pulse
git init

cp ~/dev/torque/examples/bundles/pulse/manifest.yml ~/dev/t/torque-bundle-pulse/
cp ~/dev/torque/examples/bundles/pulse/logic.js ~/dev/t/torque-bundle-pulse/
cp ~/dev/torque/examples/bundles/pulse/agent.md ~/dev/t/torque-bundle-pulse/
cp -r ~/dev/torque/examples/bundles/pulse/ui ~/dev/t/torque-bundle-pulse/
cp -r ~/dev/torque/examples/bundles/pulse/test ~/dev/t/torque-bundle-pulse/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/bundle-pulse",
  "version": "0.1.0",
  "description": "Activity timeline — subscribes to events, writes human-readable activity feed",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-bundle-pulse
node --test 'test/*.test.js'
```

Expected: Tests pass — zero external imports.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-bundle-pulse
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-bundle-pulse --private --source=. --push
```

---

### Task 18: Extract torque-bundle-tasks

**Files:**
- Create: `~/dev/t/torque-bundle-tasks/` (new repo)
- Source: `examples/bundles/tasks/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-bundle-tasks
cd ~/dev/t/torque-bundle-tasks
git init

cp ~/dev/torque/examples/bundles/tasks/manifest.yml ~/dev/t/torque-bundle-tasks/
cp ~/dev/torque/examples/bundles/tasks/logic.js ~/dev/t/torque-bundle-tasks/
cp ~/dev/torque/examples/bundles/tasks/agent.md ~/dev/t/torque-bundle-tasks/
cp -r ~/dev/torque/examples/bundles/tasks/ui ~/dev/t/torque-bundle-tasks/
cp -r ~/dev/torque/examples/bundles/tasks/test ~/dev/t/torque-bundle-tasks/
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/bundle-tasks",
  "version": "0.1.0",
  "description": "Task management — create, assign, and track tasks linked to deals or other entities",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Run tests**

```bash
cd ~/dev/t/torque-bundle-tasks
node --test 'test/*.test.js'
```

Expected: Tests pass — zero external imports.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-bundle-tasks
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-bundle-tasks --private --source=. --push
```

---

### Task 19: Extract torque-bundle-graphql

**Files:**
- Create: `~/dev/t/torque-bundle-graphql/` (new repo)
- Source: `packages/graphql/` from monorepo

**Step 1: Create repo and copy source**

```bash
mkdir -p ~/dev/t/torque-bundle-graphql
cd ~/dev/t/torque-bundle-graphql
git init

cp ~/dev/torque/packages/graphql/logic.js ~/dev/t/torque-bundle-graphql/
cp ~/dev/torque/packages/graphql/manifest.yml ~/dev/t/torque-bundle-graphql/
cp ~/dev/torque/packages/graphql/graphiql.js ~/dev/t/torque-bundle-graphql/
cp ~/dev/torque/packages/graphql/projector.js ~/dev/t/torque-bundle-graphql/
cp ~/dev/torque/packages/graphql/schema-gen.js ~/dev/t/torque-bundle-graphql/
cp -r ~/dev/torque/packages/graphql/test ~/dev/t/torque-bundle-graphql/
```

File tree:
```
torque-bundle-graphql/
├── test/
│   └── *.test.js
├── graphiql.js
├── logic.js
├── manifest.yml
├── projector.js
├── schema-gen.js
├── package.json
└── .gitignore
```

**Step 2: Create package.json**

The graphql bundle imports the `graphql` library directly. In the multi-repo world, this becomes a devDependency for testing (the app provides it at runtime).

```json
{
  "name": "@torquedev/bundle-graphql",
  "version": "0.1.0",
  "description": "Auto-generated GraphQL API — derives schema from bundle manifests",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "devDependencies": {
    "graphql": "^16.9.0"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 4: Install and run tests**

```bash
cd ~/dev/t/torque-bundle-graphql
npm install
node --test 'test/*.test.js'
```

Expected: Tests pass.

**Step 5: Commit and push**

```bash
cd ~/dev/t/torque-bundle-graphql
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque-bundle-graphql --private --source=. --push
```

---

## Phase 6: Verification

### Task 20: Run dev-link.sh and verify cross-repo resolution

**Step 1: Run dev-link.sh**

```bash
cd ~/dev/t
bash dev-link.sh
```

Expected: All 13 packages linked successfully, no "MISSING" entries.

**Step 2: Verify symlinks exist**

```bash
ls -la ~/dev/t/node_modules/@torquedev/
```

Expected: 13 symlinks pointing to their respective repo directories.

**Step 3: Verify cross-repo import resolution**

Create a temporary test script:

```bash
cat > ~/dev/t/verify-imports.mjs << 'EOF'
// Verify that cross-repo imports resolve through symlinks
import { Registry, Resolver, HookBus } from '@torquedev/core';
import { DataLayer, BundleScopedData } from '@torquedev/datalayer';
import { EventBus } from '@torquedev/eventbus';
import { createServer } from '@torquedev/server';

console.log('Registry:', typeof Registry);
console.log('Resolver:', typeof Resolver);
console.log('HookBus:', typeof HookBus);
console.log('DataLayer:', typeof DataLayer);
console.log('BundleScopedData:', typeof BundleScopedData);
console.log('EventBus:', typeof EventBus);
console.log('createServer:', typeof createServer);
console.log('\nAll cross-repo imports resolved successfully.');
EOF

cd ~/dev/t && NODE_PATH=~/dev/t/node_modules node verify-imports.mjs
```

Expected: All imports resolve, prints types for each, ends with "All cross-repo imports resolved successfully."

**Step 4: Clean up**

```bash
rm ~/dev/t/verify-imports.mjs
```

---

## Phase 7: Entry Point

### Task 21: Create torque entry point repo

**Files:**
- Create: `~/dev/t/torque/` (new repo)

**Step 1: Create repo**

```bash
mkdir -p ~/dev/t/torque
cd ~/dev/t/torque
git init
```

**Step 2: Create install script**

Create `~/dev/t/torque/install.sh`:

```bash
#!/usr/bin/env bash
# install.sh — Clone all Torque framework repos into ~/dev/t/
set -euo pipefail

WORKSPACE="${1:-$HOME/dev/t}"
GITHUB_ORG="torque-framework"

echo "[torque] Installing to: $WORKSPACE"
mkdir -p "$WORKSPACE"

REPOS=(
  torque-core
  torque-service-datalayer
  torque-service-eventbus
  torque-service-server
  torque-ui-kit
  torque-test-helpers
  torque-cli
  torque-foundation
  torque-ext-authorization
  torque-ext-soft-delete
  torque-ext-async-events
  torque-ext-search
  torque-ext-storage
  torque-bundle-identity
  torque-bundle-pipeline
  torque-bundle-pulse
  torque-bundle-tasks
  torque-bundle-graphql
  torque-shell-react
)

for repo in "${REPOS[@]}"; do
  if [ -d "$WORKSPACE/$repo" ]; then
    echo "  $repo: already exists, pulling..."
    (cd "$WORKSPACE/$repo" && git pull --quiet)
  else
    echo "  $repo: cloning..."
    gh repo clone "$GITHUB_ORG/$repo" "$WORKSPACE/$repo" -- --quiet
  fi
done

# Copy dev-link.sh to workspace if not present
if [ ! -f "$WORKSPACE/dev-link.sh" ]; then
  cp "$WORKSPACE/torque/dev-link.sh" "$WORKSPACE/dev-link.sh" 2>/dev/null || true
fi

echo ""
echo "[torque] All repos cloned. Run:"
echo "  cd $WORKSPACE && bash dev-link.sh"
```

**Step 3: Copy dev-link.sh into this repo too**

```bash
cp ~/dev/t/dev-link.sh ~/dev/t/torque/dev-link.sh
```

**Step 4: Copy spec docs from monorepo**

```bash
mkdir -p ~/dev/t/torque/docs/specs
cp ~/dev/torque/docs/specs/*.md ~/dev/t/torque/docs/specs/
```

**Step 5: Create README.md**

Create `~/dev/t/torque/README.md`:

```markdown
# Torque

Composable monolith framework for Node.js.

## Quick Start

```bash
# Clone all framework repos
bash install.sh ~/dev/t

# Set up cross-repo symlinks
cd ~/dev/t && bash dev-link.sh

# Create a new app
cd ~/dev/t && npx torque new myapp
cd myapp && npm install && npm start
```

## Repository Map

| Tier | Repo | Package |
|------|------|---------|
| Kernel | torque-core | @torquedev/core |
| Service | torque-service-datalayer | @torquedev/datalayer |
| Service | torque-service-eventbus | @torquedev/eventbus |
| Service | torque-service-server | @torquedev/server |
| UI | torque-ui-kit | @torquedev/ui-kit |
| Shell | torque-shell-react | @torquedev/shell-react |
| Tooling | torque-cli | @torquedev/cli |
| Tooling | torque-test-helpers | @torquedev/test-helpers |
| Tooling | torque-foundation | (git-only) |
| Extension | torque-ext-authorization | @torquedev/authorization |
| Extension | torque-ext-soft-delete | @torquedev/datalayer-soft-delete |
| Extension | torque-ext-async-events | @torquedev/eventbus-async |
| Extension | torque-ext-search | @torquedev/search |
| Extension | torque-ext-storage | @torquedev/storage |
| Bundle | torque-bundle-identity | (git-only) |
| Bundle | torque-bundle-pipeline | (git-only) |
| Bundle | torque-bundle-pulse | (git-only) |
| Bundle | torque-bundle-tasks | (git-only) |
| Bundle | torque-bundle-graphql | (git-only) |
| App | torque-app-todo | (reference app) |
```

**Step 6: Create .gitignore**

```
node_modules/
.DS_Store
```

**Step 7: Make install.sh executable, commit and push**

```bash
cd ~/dev/t/torque
chmod +x install.sh
git add -A
git commit -m "initial commit"
gh repo create torque-framework/torque --private --source=. --push
```

---

## Important Notes for Implementer

1. **Test isolation is critical.** Every repo must pass `node --test` without `dev-link.sh` symlinks. If a test file imports from `@torquedev/*`, either:
   - Mock the import with a vendored stub in `node_modules/@torquedev/` (tracked in git via `!node_modules/@torquedev/` in `.gitignore`)
   - Or ensure the test doesn't actually execute that import path (e.g., `boot.js` uses lazy `import()` so it's not called in tests)

2. **The `boot.js` in torque-core uses `await import('@torquedev/datalayer')`.** This is a lazy import — it only runs when `boot()` is called, not at module load time. Since no core tests call `boot()`, this doesn't break test isolation.

3. **The eventbus is the only service that imports from core at the top level.** The `import { ContractViolationError } from '@torquedev/core'` in `eventbus/index.js` requires the vendored mock in `node_modules/@torquedev/core/index.js` for tests to pass in isolation.

4. **Bundle UI files import from `@torquedev/ui-kit`.** These imports are only executed at runtime by the shell (which dynamically imports bundle UI scripts). Bundle tests never import UI files, so this doesn't affect test isolation.

5. **Run tasks within each phase in parallel.** Phase 2 (5 tasks), Phase 4 (5 tasks), and Phase 5 (5 tasks) are all independently executable within their phase.

6. **If any test fails,** check what it imports. Read the actual test file to understand whether it needs a vendored mock or if there's a real dependency issue. Never skip a failing test — fix the isolation issue.
