# Extract torque-test-helpers Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.
>
> **Spec Review Warning:** The spec review loop exhausted 3 iterations before approval.
> The final verdict was APPROVED with all criteria met. Human reviewer should verify
> the implementation matches expectations during the approval gate.

**Goal:** Extract `packages/test-helpers/` from the monorepo into a standalone repo at `~/dev/t/torque-test-helpers/` with smoke tests and push to GitHub.
**Architecture:** Copy the single `index.js` (119 lines, zero dependencies, 4 exported factory functions) into a new git repo with `package.json`, `.gitignore`, and a smoke test file. No build step, no dependencies to install.
**Tech Stack:** Node.js (ESM), `node:test` + `node:assert/strict` for testing, GitHub CLI for repo creation.

**Dependency:** Task 2 (workspace setup at `~/dev/t/`) must be complete before starting.

---

### Task 1: Initialize the repo directory and git

**Files:**
- Create: `~/dev/t/torque-test-helpers/` (directory)

**Step 1: Create directory and initialize git**
```bash
mkdir -p ~/dev/t/torque-test-helpers
cd ~/dev/t/torque-test-helpers
git init
```
Expected: `Initialized empty Git repository in ~/dev/t/torque-test-helpers/.git/`

---

### Task 2: Copy index.js from monorepo

**Files:**
- Create: `~/dev/t/torque-test-helpers/index.js`
- Source: `~/dev/torque/packages/test-helpers/index.js`

**Step 1: Copy the source file**
```bash
cp ~/dev/torque/packages/test-helpers/index.js ~/dev/t/torque-test-helpers/index.js
```

**Step 2: Verify the copy is byte-for-byte identical**
```bash
diff ~/dev/torque/packages/test-helpers/index.js ~/dev/t/torque-test-helpers/index.js
```
Expected: No output (files are identical).

The file exports 4 functions: `createMockData`, `createMockEvents`, `createMockCoordinator`, `createSpyCoordinator`. It is 119 lines, uses ESM `export`, has zero imports and zero dependencies.

---

### Task 3: Create package.json

**Files:**
- Create: `~/dev/t/torque-test-helpers/package.json`

**Step 1: Write package.json**

Create `~/dev/t/torque-test-helpers/package.json` with exactly this content:

```json
{
  "name": "@torquedev/test-helpers",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js"
}
```

Requirements per spec:
- `name`: `@torquedev/test-helpers`
- `version`: `0.1.0`
- `type`: `module`
- `main`: `index.js`
- No `dependencies` field (package has zero dependencies)

---

### Task 4: Create .gitignore

**Files:**
- Create: `~/dev/t/torque-test-helpers/.gitignore`

**Step 1: Write .gitignore**

Create `~/dev/t/torque-test-helpers/.gitignore` with exactly this content:

```
node_modules/
.DS_Store
```

Two lines, no trailing newline after `.DS_Store`.

---

### Task 5: Write the smoke test

**Files:**
- Create: `~/dev/t/torque-test-helpers/test/smoke.test.js`

**Step 1: Create the test directory**
```bash
mkdir -p ~/dev/t/torque-test-helpers/test
```

**Step 2: Write test/smoke.test.js**

Create `~/dev/t/torque-test-helpers/test/smoke.test.js` with this content:

```javascript
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  createMockData,
  createMockEvents,
  createMockCoordinator,
  createSpyCoordinator,
} from '../index.js';

describe('createMockData', () => {
  it('supports insert/find/query', () => {
    const db = createMockData();

    // insert returns the record with id
    const record = db.insert('users', { name: 'Alice' });
    assert.ok(record.id, 'inserted record should have an id');
    assert.equal(record.name, 'Alice');

    // find retrieves by id
    const found = db.find('users', record.id);
    assert.deepEqual(found, record);

    // query with filters
    db.insert('users', { name: 'Bob' });
    const results = db.query('users', { name: 'Alice' });
    assert.equal(results.length, 1);
    assert.equal(results[0].name, 'Alice');
  });
});

describe('createMockEvents', () => {
  it('captures published events', () => {
    const events = createMockEvents();

    events.publish('user.created', { id: '1', name: 'Alice' });
    events.publish('user.updated', { id: '1', name: 'Alice Updated' });

    assert.equal(events._published.length, 2);
    assert.equal(events._published[0].name, 'user.created');
    assert.deepEqual(events._published[0].payload, { id: '1', name: 'Alice' });
    assert.equal(events._published[1].name, 'user.updated');
  });
});

describe('createMockCoordinator', () => {
  it('returns canned responses', async () => {
    const coordinator = createMockCoordinator({
      'accounts.getUser': (args) => ({ id: args.id, name: 'Alice' }),
    });

    const result = await coordinator.call('accounts', 'getUser', { id: '42' });
    assert.deepEqual(result, { id: '42', name: 'Alice' });

    // Unknown key returns null
    const missing = await coordinator.call('accounts', 'unknownMethod', {});
    assert.equal(missing, null);
  });
});

describe('createSpyCoordinator', () => {
  it('tracks calls', async () => {
    const coordinator = createSpyCoordinator({
      'orders.list': () => [{ id: 'o-1' }],
    });

    await coordinator.call('orders', 'list', { userId: '99' });
    await coordinator.call('orders', 'list', { userId: '100' });

    assert.equal(coordinator._calls.length, 2);
    assert.equal(coordinator._calls[0].bundle, 'orders');
    assert.equal(coordinator._calls[0].iface, 'list');
    assert.deepEqual(coordinator._calls[0].args, { userId: '99' });
    assert.equal(coordinator._calls[1].args.userId, '100');
  });
});
```

The test has exactly 4 tests verifying:
1. `createMockData` supports insert/find/query
2. `createMockEvents` captures published events
3. `createMockCoordinator` returns canned responses and null for unknown keys
4. `createSpyCoordinator` tracks calls with bundle/iface/args

**Step 3: Run the tests**
```bash
cd ~/dev/t/torque-test-helpers
node --test 'test/*.test.js'
```
Expected output includes:
```
# tests 4
# suites 4
# pass 4
# fail 0
```

---

### Task 6: Commit and push to GitHub

**Files:**
- All files in `~/dev/t/torque-test-helpers/`

**Step 1: Stage all files and commit**
```bash
cd ~/dev/t/torque-test-helpers
git add .
git commit -m "feat: extract torque-test-helpers from monorepo"
```

**Step 2: Create private GitHub repo and push**
```bash
cd ~/dev/t/torque-test-helpers
gh repo create torque-framework/torque-test-helpers --private --source=. --push
```
Expected: Repo created at `github.com/torque-framework/torque-test-helpers` (private).

**Step 3: Verify the push**
```bash
cd ~/dev/t/torque-test-helpers
git remote -v
```
Expected: Shows `origin` pointing to `github.com:torque-framework/torque-test-helpers.git`.

```bash
gh repo view torque-framework/torque-test-helpers --json isPrivate
```
Expected: `{"isPrivate": true}`

---

## Acceptance Criteria Checklist

- [ ] `~/dev/t/torque-test-helpers/` exists as a git repo
- [ ] `index.js` matches monorepo `packages/test-helpers/index.js` exactly
- [ ] `package.json` has name `@torquedev/test-helpers`, version `0.1.0`, type `module`, main `index.js`, no dependencies
- [ ] `.gitignore` contains `node_modules/` and `.DS_Store`
- [ ] `test/smoke.test.js` exists with 4 tests
- [ ] `node --test 'test/*.test.js'` passes all 4 tests
- [ ] Repo pushed to GitHub at `torque-framework/torque-test-helpers` (private)
