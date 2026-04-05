# Phase 2: Kernel Injection + Call-Time Validation

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Wire `@torquedev/schema` into the kernel so that Registry validates interface inputs/outputs at call time, and EventBus validates event payload types at publish time.

**Architecture:** The kernel (Registry, EventBus) accepts an optional `typeValidator` function via constructor injection. When present, it calls `typeValidator(declaredType, actualValue, fieldName)` at every contract boundary -- input args, output results, and event payloads. When absent, all new validation is skipped (full backward compatibility). The boot layer creates the validator from `@torquedev/schema` and passes it down.

**Tech Stack:** Node.js ESM, `node --test`, `node:assert/strict`. No new dependencies in kernel packages.

**Depends on:** Phase 1 (`@torquedev/schema` package at `torque-schema/`). Phase 1 must be complete and linkable before starting.

**Design doc:** `docs/specs/2026-03-30-contract-validation-design.md` (Sections 2 and 3)

---

## Repo Map

| Repo | Path | Test command |
|------|------|-------------|
| torque-core | `~/dev/t/torque-core` | `cd ~/dev/t/torque-core && npm test` |
| torque-service-eventbus | `~/dev/t/torque-service-eventbus` | `cd ~/dev/t/torque-service-eventbus && npm test` |
| torque-schema (Phase 1) | `~/dev/t/torque-schema` | `cd ~/dev/t/torque-schema && npm test` |

---

## Key Existing Patterns

**Registry constructor** (`torque-core/kernel/registry.js:55`):
```js
constructor({ dataLayer, eventBus, createScopedData, hookBus = null, silent = false })
```

**Registry.call() output validation** (`torque-core/kernel/registry.js:265-279`) -- this is the block we extend:
```js
if (manifest?.interfaces?.contracts?.[interfaceName]?.output?.shape && result && !result.error) {
  const shape = manifest.interfaces.contracts[interfaceName].output.shape;
  const declaredFields = Object.keys(shape);
  const actualFields = Object.keys(result);
  for (const field of declaredFields) {
    if (!actualFields.includes(field) && result[field] === undefined) {
      this._contractViolation(
        `${bundleName}.${interfaceName}`,
        `output missing declared field '${field}'\n  Fix: include '${field}' in return value, or remove from interfaces.contracts.${interfaceName}.output.shape in manifest.yml`
      );
    }
  }
}
```

**Registry._contractViolation** (`torque-core/kernel/registry.js:309-314`): `(tag, message)` -- warns or throws based on `_validationMode`.

**EventBus constructor** (`torque-service-eventbus/index.js:9`):
```js
constructor({ db = null, maxLogEntries = 200, hookBus = null, silent = false } = {})
```

**EventBus._contractViolation** (`torque-service-eventbus/index.js:63-68`): `(message)` -- warns or throws based on `_validationMode`. Note: different signature than Registry (no `tag` param).

**EventBus publish() payload validation** (`torque-service-eventbus/index.js:102-121`) -- the block we extend:
```js
if (this._eventSchemas.has(eventName) && payload) {
  const { schema, bundle } = this._eventSchemas.get(eventName);
  const declaredFields = Object.keys(schema);
  const actualFields = Object.keys(payload);
  for (const field of declaredFields) {
    if (!actualFields.includes(field)) {
      this._contractViolation(`Event '${eventName}' payload missing declared field '${field}'...`);
    }
  }
  for (const field of actualFields) {
    if (!declaredFields.includes(field)) {
      this._contractViolation(`Event '${eventName}' payload has undeclared field '${field}'...`);
    }
  }
}
```

The same block is duplicated verbatim in `publishAsync()` at lines 202-221.

**Test patterns** -- both repos use identical conventions:
```js
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
```

**Existing test mocks** -- `test/registry.test.js` defines `createMockDataLayer()` and `createMockEventBus()`. We'll define our own copies in our new test file (each test file is self-contained).

**`@torquedev/schema` contract** (from Phase 1 design):
- `createTypeValidator()` returns a function: `(declaredType, actualValue, fieldName) => string | null`
- Returns `null` when valid, returns a violation string when invalid
- `validateRequired(args, inputContract)` returns first violation string or `null`

---

### Task 1: Link @torquedev/schema into dev environment

**Files:**
- Modify: `~/dev/t/dev-link.sh`

This adds `@torquedev/schema` to the workspace symlink script so the kernel packages can resolve it during development.

**Step 1: Add schema to dev-link.sh PACKAGES array**

Open `~/dev/t/dev-link.sh`. Find the `PACKAGES=(` array. Add this line after the `"test-helpers:torque-test-helpers"` entry (in the "Core framework" section):

```bash
  "schema:torque-schema"
```

The section should now read:

```bash
  # Core framework
  "core:torque-core"
  "datalayer:torque-service-datalayer"
  "eventbus:torque-service-eventbus"
  "server:torque-service-server"
  "ui-kit:torque-ui-kit"
  "cli:torque-cli"
  "test-helpers:torque-test-helpers"
  "schema:torque-schema"
  "shell-react:torque-shell-react"
```

**Step 2: Run dev-link.sh and verify**

```bash
cd ~/dev/t && bash dev-link.sh
```

Expected: you should see `LINKED   @torquedev/schema  ->  .../torque-schema` in the output. If Phase 1 isn't complete yet, you'll see `MISSING  @torquedev/schema` -- that's OK, come back and re-run after Phase 1.

**Step 3: Commit**

```bash
cd ~/dev/t && git add dev-link.sh && git commit -m "chore: add @torquedev/schema to dev-link.sh"
```

---

### Task 2: Registry accepts typeValidator in constructor

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Create: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Create the test file with helpers and first tests**

Create `~/dev/t/torque-core/test/registry-type-validation.test.js` with this content:

```js
/**
 * Tests for typeValidator injection and call-time type validation.
 * Covers: constructor injection, input validation, output validation.
 */
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { Registry } from '../kernel/registry.js';
import { ContractViolationError } from '../kernel/errors.js';

// ── Test helpers ────────────────────────────────────────────────────

function createMockDataLayer() {
  return {
    schemas: {},
    registerSchema(bundleName, tables) { this.schemas[bundleName] = tables; },
    tablesFor(bundle) { return Object.keys(this.schemas[bundle] || {}); },
  };
}

function createMockEventBus() {
  return {
    _validationMode: 'warn',
    _declaredEvents: new Map(),
    setValidationMode(mode) { this._validationMode = mode; },
    registerDeclaredEvents(name, events) { this._declaredEvents.set(name, events); },
    registerEventSchemas() {},
    subscribers: new Map(),
    subscribe() {},
    subscriptions() { return {}; },
  };
}

/**
 * Mock typeValidator that does basic type checking.
 * Tracks all calls in fn.calls for assertions.
 */
function createMockTypeValidator() {
  const calls = [];
  const fn = (declaredType, actualValue, fieldName) => {
    calls.push({ declaredType, actualValue, fieldName });
    const checks = {
      string: (v) => typeof v === 'string',
      text: (v) => typeof v === 'string',
      uuid: (v) => typeof v === 'string' && /^[0-9a-f]{8}-/.test(v),
      integer: (v) => Number.isInteger(v),
      boolean: (v) => typeof v === 'boolean',
    };
    const check = checks[declaredType];
    if (check && !check(actualValue)) {
      return `field '${fieldName}': expected ${declaredType}, got ${typeof actualValue}`;
    }
    return null;
  };
  fn.calls = calls;
  return fn;
}

/**
 * Create a Registry with optional typeValidator, defaulting to strict mode
 * so violations throw (easier to assert in tests).
 */
function createTestRegistry(typeValidator = null, mode = 'strict') {
  const registry = new Registry({
    dataLayer: createMockDataLayer(),
    eventBus: createMockEventBus(),
    createScopedData: (dl, name) => ({ _bundle: name }),
    typeValidator,
  });
  registry._validationMode = mode;
  return registry;
}

/**
 * Register a test bundle + interface on a registry.
 * Lets you set input/output contracts and the handler in one call.
 */
function registerTestInterface(registry, bundleName, interfaceName, { input, output, handler }) {
  if (!registry.bundles[bundleName]) {
    registry.bundles[bundleName] = { manifest: { interfaces: { contracts: {} } } };
  }
  const contract = {};
  if (input) contract.input = input;
  if (output) contract.output = output;
  registry.bundles[bundleName].manifest.interfaces.contracts[interfaceName] = contract;
  registry.interfaces[`${bundleName}.${interfaceName}`] = handler;
}

// ── Task 2: Constructor injection ───────────────────────────────────

describe('Registry typeValidator injection', () => {
  it('stores typeValidator when provided', () => {
    const tv = createMockTypeValidator();
    const registry = createTestRegistry(tv);
    assert.equal(registry._typeValidator, tv);
  });

  it('defaults _typeValidator to null when not provided', () => {
    const registry = new Registry({
      dataLayer: createMockDataLayer(),
      eventBus: createMockEventBus(),
      createScopedData: (dl, name) => ({ _bundle: name }),
    });
    assert.equal(registry._typeValidator, null);
  });

  it('call() still works without typeValidator (backward compat)', async () => {
    const registry = createTestRegistry(); // no typeValidator
    registry.interfaces['test.greet'] = async ({ name }) => ({ greeting: `Hi ${name}` });
    const result = await registry.call('test', 'greet', { name: 'World' });
    assert.deepEqual(result, { greeting: 'Hi World' });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- `Registry` constructor doesn't accept `typeValidator` yet, so `registry._typeValidator` is `undefined` not the function/null.

**Step 3: Implement -- modify Registry constructor**

In `~/dev/t/torque-core/kernel/registry.js`, change the constructor signature and body.

Find this (line 48-55):
```js
  /**
   * @param {object} opts
   * @param {object} opts.dataLayer - DataLayer instance (from @torquedev/datalayer)
   * @param {object} opts.eventBus - EventBus instance (from @torquedev/eventbus)
   * @param {function} opts.createScopedData - (dataLayer, bundleName) => BundleScopedData
   * @param {object} [opts.hookBus] - HookBus instance for lifecycle hooks
   */
  constructor({ dataLayer, eventBus, createScopedData, hookBus = null, silent = false }) {
```

Replace with:
```js
  /**
   * @param {object} opts
   * @param {object} opts.dataLayer - DataLayer instance (from @torquedev/datalayer)
   * @param {object} opts.eventBus - EventBus instance (from @torquedev/eventbus)
   * @param {function} opts.createScopedData - (dataLayer, bundleName) => BundleScopedData
   * @param {object} [opts.hookBus] - HookBus instance for lifecycle hooks
   * @param {function} [opts.typeValidator] - (declaredType, value, fieldName) => string|null
   */
  constructor({ dataLayer, eventBus, createScopedData, hookBus = null, typeValidator = null, silent = false }) {
```

Then, right after `this.silent = silent;` (line 60), add:
```js
    this._typeValidator = typeValidator;
```

So the constructor body now includes (around line 60-61):
```js
    this.silent = silent;
    this._typeValidator = typeValidator;
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass (new ones and existing ones).

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): accept typeValidator in constructor"
```

---

### Task 3: Registry input validation (required fields + types)

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Modify: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-core/test/registry-type-validation.test.js`:

```js
// ── Task 3: Input validation ────────────────────────────────────────

describe('Registry input validation', () => {
  describe('required field checking', () => {
    it('throws when a required field is missing', async () => {
      const registry = createTestRegistry(createMockTypeValidator());
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
          userId: { type: 'uuid', required: true },
          description: { type: 'string' },
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      await assert.rejects(
        () => registry.call('tasks', 'CreateTask', { taskName: 'Test' }),
        (err) => {
          assert.equal(err.name, 'ContractViolationError');
          assert.ok(err.message.includes('userId'), `should mention missing field 'userId', got: ${err.message}`);
          assert.ok(err.message.includes('required'), `should mention 'required', got: ${err.message}`);
          return true;
        }
      );
    });

    it('throws when a required field is null', async () => {
      const registry = createTestRegistry(createMockTypeValidator());
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      await assert.rejects(
        () => registry.call('tasks', 'CreateTask', { taskName: null }),
        (err) => {
          assert.equal(err.name, 'ContractViolationError');
          assert.ok(err.message.includes('taskName'));
          return true;
        }
      );
    });

    it('passes when all required fields are present', async () => {
      const registry = createTestRegistry(createMockTypeValidator());
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
          userId: { type: 'uuid', required: true },
        },
        output: {},
        handler: async (args) => ({ id: '550e8400-e29b-41d4-a716-446655440000', ...args }),
      });

      const result = await registry.call('tasks', 'CreateTask', {
        taskName: 'Test',
        userId: '550e8400-e29b-41d4-a716-446655440000',
      });
      assert.ok(result.id);
    });

    it('skips validation when no input contract is declared', async () => {
      const registry = createTestRegistry(createMockTypeValidator());
      registerTestInterface(registry, 'tasks', 'ListTasks', {
        output: {},
        handler: async () => ([]),
      });

      const result = await registry.call('tasks', 'ListTasks', { anything: 'goes' });
      assert.deepEqual(result, []);
    });
  });

  describe('input type checking', () => {
    it('throws when input field has wrong type', async () => {
      const registry = createTestRegistry(createMockTypeValidator());
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
          priority: { type: 'integer' },
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      await assert.rejects(
        () => registry.call('tasks', 'CreateTask', { taskName: 'Test', priority: 'high' }),
        (err) => {
          assert.equal(err.name, 'ContractViolationError');
          assert.ok(err.message.includes('priority'), `should mention field 'priority', got: ${err.message}`);
          assert.ok(err.message.includes('integer'), `should mention expected type, got: ${err.message}`);
          return true;
        }
      );
    });

    it('passes when input field types are correct', async () => {
      const tv = createMockTypeValidator();
      const registry = createTestRegistry(tv);
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
          priority: { type: 'integer' },
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      await registry.call('tasks', 'CreateTask', { taskName: 'Test', priority: 3 });
      // typeValidator should have been called for both fields
      assert.ok(tv.calls.length >= 2, `typeValidator should be called for present fields, got ${tv.calls.length} calls`);
    });

    it('skips type check for undefined (optional) fields', async () => {
      const tv = createMockTypeValidator();
      const registry = createTestRegistry(tv);
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
          description: { type: 'string' },  // optional, not passed
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      await registry.call('tasks', 'CreateTask', { taskName: 'Test' });
      // typeValidator should NOT be called for 'description' (absent)
      const descCalls = tv.calls.filter(c => c.fieldName === 'description');
      assert.equal(descCalls.length, 0, 'should not type-check absent optional fields');
    });

    it('skips all input validation when no typeValidator is provided', async () => {
      const registry = createTestRegistry(null); // no typeValidator
      registerTestInterface(registry, 'tasks', 'CreateTask', {
        input: {
          taskName: { type: 'string', required: true },
        },
        output: {},
        handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }),
      });

      // Missing required field, but no typeValidator = no validation = no error
      const result = await registry.call('tasks', 'CreateTask', {});
      assert.ok(result.id);
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- input validation doesn't exist yet.

**Step 3: Implement input validation in Registry.call()**

In `~/dev/t/torque-core/kernel/registry.js`, find this block inside `call()` (around lines 260-262):

```js
    const start = Date.now();
    try {
      const result = await handler(args);
```

Insert the following input validation block **BEFORE** `const start = Date.now();`:

```js
    // ── Input validation ──────────────────────────────────────────────
    if (this._typeValidator) {
      const manifest = this.bundles[bundleName]?.manifest;
      const inputContract = manifest?.interfaces?.contracts?.[interfaceName]?.input;
      if (inputContract) {
        const tag = `${bundleName}.${interfaceName}`;
        // 1. Required field check
        for (const [fieldName, fieldDef] of Object.entries(inputContract)) {
          if (fieldDef.required && (args[fieldName] === undefined || args[fieldName] === null)) {
            this._contractViolation(
              tag,
              `input missing required field '${fieldName}'\n  Fix: include '${fieldName}' in args, or remove 'required: true' from interfaces.contracts.${interfaceName}.input.${fieldName} in manifest.yml`
            );
          }
        }
        // 2. Type check for present fields
        for (const [fieldName, fieldDef] of Object.entries(inputContract)) {
          if (args[fieldName] !== undefined && args[fieldName] !== null && fieldDef.type) {
            const violation = this._typeValidator(fieldDef.type, args[fieldName], fieldName);
            if (violation) {
              this._contractViolation(tag, violation);
            }
          }
        }
      }
    }

```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): input validation - required fields + type checking"
```

---

### Task 4: Registry output type validation

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Modify: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-core/test/registry-type-validation.test.js`:

```js
// ── Task 4: Output type validation ──────────────────────────────────

describe('Registry output type validation', () => {
  it('throws when output field has wrong type', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ id: 42, title: 'Test' }),  // id should be uuid string, not number
    });

    await assert.rejects(
      () => registry.call('tasks', 'GetTask', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('id'), `should mention field 'id', got: ${err.message}`);
        return true;
      }
    );
  });

  it('passes when output field types are correct', async () => {
    const tv = createMockTypeValidator();
    const registry = createTestRegistry(tv);
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', title: 'Test' }),
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result.title, 'Test');
    // typeValidator should have been called for both output fields
    assert.ok(tv.calls.length >= 2, `typeValidator should check output fields, got ${tv.calls.length} calls`);
  });

  it('skips output type checking when typeValidator is null', async () => {
    const registry = createTestRegistry(null); // no typeValidator
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ id: 42, title: 'Test' }), // wrong type but no validator
    });

    // Should NOT throw -- existing field presence check passes (id is present), type check skipped
    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result.id, 42);
  });

  it('still checks field presence (existing behavior) alongside type checking', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string', status: 'string' },
      },
      handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000', title: 'Test' }), // missing 'status'
    });

    await assert.rejects(
      () => registry.call('tasks', 'GetTask', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('status'), `should mention missing field 'status', got: ${err.message}`);
        return true;
      }
    );
  });

  it('does not type-check fields that are undefined in result', async () => {
    const tv = createMockTypeValidator();
    const registry = createTestRegistry(tv, 'warn'); // warn mode so missing field doesn't throw
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }), // title missing
    });

    await registry.call('tasks', 'GetTask', {});
    // typeValidator should NOT be called for 'title' (undefined in result)
    const titleCalls = tv.calls.filter(c => c.fieldName === 'title');
    assert.equal(titleCalls.length, 0, 'should not type-check undefined output fields');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- `id: 42` doesn't trigger a type violation because the existing code only checks field presence, not types.

**Step 3: Implement output type validation**

In `~/dev/t/torque-core/kernel/registry.js`, find the output validation block inside `call()` (around line 265-279). The current loop body is:

```js
        for (const field of declaredFields) {
          if (!actualFields.includes(field) && result[field] === undefined) {
            this._contractViolation(
              `${bundleName}.${interfaceName}`,
              `output missing declared field '${field}'\n  Fix: include '${field}' in return value, or remove from interfaces.contracts.${interfaceName}.output.shape in manifest.yml`
            );
          }
        }
```

Replace that loop with:

```js
        for (const field of declaredFields) {
          if (!actualFields.includes(field) && result[field] === undefined) {
            this._contractViolation(
              `${bundleName}.${interfaceName}`,
              `output missing declared field '${field}'\n  Fix: include '${field}' in return value, or remove from interfaces.contracts.${interfaceName}.output.shape in manifest.yml`
            );
          } else if (this._typeValidator && result[field] !== undefined) {
            const violation = this._typeValidator(shape[field], result[field], field);
            if (violation) {
              this._contractViolation(`${bundleName}.${interfaceName}`, violation);
            }
          }
        }
```

The change: added an `else if` branch that calls `this._typeValidator` for fields that ARE present.

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): output type validation via typeValidator"
```

---

### Task 5: Registry output array validation

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Modify: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-core/test/registry-type-validation.test.js`:

```js
// ── Task 5: Output array validation ─────────────────────────────────

describe('Registry output array validation', () => {
  it('throws when output.type is array but handler returns non-array', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'ListTasks', {
      output: {
        type: 'array',
        items: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ id: '550e8400-e29b-41d4-a716-446655440000' }), // object, not array
    });

    await assert.rejects(
      () => registry.call('tasks', 'ListTasks', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('array'), `should mention 'array', got: ${err.message}`);
        return true;
      }
    );
  });

  it('validates each item in the array against items shape', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'ListTasks', {
      output: {
        type: 'array',
        items: { id: 'uuid', title: 'string' },
      },
      handler: async () => ([
        { id: '550e8400-e29b-41d4-a716-446655440000', title: 'Task 1' },
        { id: 42, title: 'Task 2' }, // id is wrong type
      ]),
    });

    await assert.rejects(
      () => registry.call('tasks', 'ListTasks', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('[1]'), `should include item index, got: ${err.message}`);
        assert.ok(err.message.includes('id'), `should mention field 'id', got: ${err.message}`);
        return true;
      }
    );
  });

  it('passes when all array items match the schema', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'ListTasks', {
      output: {
        type: 'array',
        items: { id: 'uuid', title: 'string' },
      },
      handler: async () => ([
        { id: '550e8400-e29b-41d4-a716-446655440000', title: 'Task 1' },
        { id: '660e8400-e29b-41d4-a716-446655440000', title: 'Task 2' },
      ]),
    });

    const result = await registry.call('tasks', 'ListTasks', {});
    assert.equal(result.length, 2);
  });

  it('passes empty array without error', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'ListTasks', {
      output: {
        type: 'array',
        items: { id: 'uuid', title: 'string' },
      },
      handler: async () => ([]),
    });

    const result = await registry.call('tasks', 'ListTasks', {});
    assert.deepEqual(result, []);
  });

  it('skips array validation when no typeValidator', async () => {
    const registry = createTestRegistry(null);
    registerTestInterface(registry, 'tasks', 'ListTasks', {
      output: {
        type: 'array',
        items: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({ notAnArray: true }), // wrong but no validator
    });

    const result = await registry.call('tasks', 'ListTasks', {});
    assert.equal(result.notAnArray, true);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- no array output validation exists yet.

**Step 3: Implement output array validation**

In `~/dev/t/torque-core/kernel/registry.js`, find the existing output validation block. It currently starts with:

```js
      // Contract validation: check return value against manifest interface schema
      const manifest = this.bundles[bundleName]?.manifest;
      if (manifest?.interfaces?.contracts?.[interfaceName]?.output?.shape && result && !result.error) {
```

We need to add array validation AFTER the existing `shape` block's closing `}`. Find the closing brace of the existing output validation block (after the `for` loop over `declaredFields`), and insert this new block immediately after it:

```js

      // Array output validation: check output.type === 'array' with items shape
      if (this._typeValidator) {
        const outputContract = manifest?.interfaces?.contracts?.[interfaceName]?.output;
        if (outputContract?.type === 'array' && result !== null && result !== undefined && !result.error) {
          const tag = `${bundleName}.${interfaceName}`;
          if (!Array.isArray(result)) {
            this._contractViolation(
              tag,
              `expected array output, got ${typeof result}\n  Fix: return an array from ${interfaceName}, or change output.type in manifest.yml`
            );
          } else if (outputContract.items) {
            for (let i = 0; i < result.length; i++) {
              const item = result[i];
              if (item && typeof item === 'object') {
                for (const [field, type] of Object.entries(outputContract.items)) {
                  if (item[field] !== undefined) {
                    const violation = this._typeValidator(type, item[field], `[${i}].${field}`);
                    if (violation) {
                      this._contractViolation(tag, violation);
                    }
                  }
                }
              }
            }
          }
        }
      }
```

Note: the `const manifest` variable was already declared in the shape validation block above. If it's scoped inside that `if`, you'll need to hoist it. Check: the existing code declares `const manifest = this.bundles[bundleName]?.manifest;` right before the `if`. It's at the same scope level as the new block, so it's accessible. If you see a `manifest is not defined` error, move the `const manifest` line above the existing `if` block.

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): output array validation with items shape checking"
```

---

### Task 6: Registry output extra field detection

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Modify: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-core/test/registry-type-validation.test.js`:

```js
// ── Task 6: Output extra field detection ────────────────────────────

describe('Registry output extra field detection', () => {
  it('throws when result has fields not declared in output.shape', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Test',
        secret: 'should-not-be-here',  // undeclared field
      }),
    });

    await assert.rejects(
      () => registry.call('tasks', 'GetTask', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('secret'), `should mention undeclared field 'secret', got: ${err.message}`);
        assert.ok(err.message.includes('undeclared'), `should mention 'undeclared', got: ${err.message}`);
        return true;
      }
    );
  });

  it('passes when result has only declared fields', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid', title: 'string' },
      },
      handler: async () => ({
        id: '550e8400-e29b-41d4-a716-446655440000',
        title: 'Test',
      }),
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result.title, 'Test');
  });

  it('skips extra field check when no typeValidator', async () => {
    const registry = createTestRegistry(null);
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid' },
      },
      handler: async () => ({
        id: '550e8400-e29b-41d4-a716-446655440000',
        extra: 'not-declared',
      }),
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result.extra, 'not-declared');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- no extra field detection exists yet.

**Step 3: Implement extra field detection**

In `~/dev/t/torque-core/kernel/registry.js`, find the output validation block that loops over `declaredFields`. Right after that `for` loop ends (and before the closing `}` of the outer `if`), add:

```js
        // Extra field detection: flag fields in result not declared in shape
        if (this._typeValidator) {
          for (const field of actualFields) {
            if (!declaredFields.includes(field)) {
              this._contractViolation(
                `${bundleName}.${interfaceName}`,
                `output has undeclared field '${field}'\n  Fix: add '${field}' to interfaces.contracts.${interfaceName}.output.shape in manifest.yml, or remove from return value`
              );
            }
          }
        }
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): detect undeclared extra fields in output"
```

---

### Task 7: Registry output nullable enforcement

**Files:**
- Modify: `~/dev/t/torque-core/kernel/registry.js`
- Modify: `~/dev/t/torque-core/test/registry-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-core/test/registry-type-validation.test.js`:

```js
// ── Task 7: Output nullable enforcement ─────────────────────────────

describe('Registry output nullable enforcement', () => {
  it('throws when handler returns null and output.nullable is false', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        nullable: false,
        shape: { id: 'uuid' },
      },
      handler: async () => null,
    });

    await assert.rejects(
      () => registry.call('tasks', 'GetTask', {}),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('null'), `should mention 'null', got: ${err.message}`);
        return true;
      }
    );
  });

  it('passes when handler returns null and nullable is not declared (default)', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        shape: { id: 'uuid' },
      },
      handler: async () => null,
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result, null);
  });

  it('passes when handler returns null and output.nullable is true', async () => {
    const registry = createTestRegistry(createMockTypeValidator());
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        nullable: true,
        shape: { id: 'uuid' },
      },
      handler: async () => null,
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result, null);
  });

  it('skips nullable check when no typeValidator', async () => {
    const registry = createTestRegistry(null);
    registerTestInterface(registry, 'tasks', 'GetTask', {
      output: {
        nullable: false,
        shape: { id: 'uuid' },
      },
      handler: async () => null,
    });

    const result = await registry.call('tasks', 'GetTask', {});
    assert.equal(result, null);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: FAIL -- no nullable enforcement exists yet.

**Step 3: Implement nullable enforcement**

In `~/dev/t/torque-core/kernel/registry.js`, find the line just BEFORE the existing output validation block. Currently it looks like:

```js
      const result = await handler(args);

      // Contract validation: check return value against manifest interface schema
      const manifest = this.bundles[bundleName]?.manifest;
```

Insert the nullable check between `const result = await handler(args);` and the comment `// Contract validation:`:

```js
      const result = await handler(args);

      // Nullable enforcement: flag null returns when output.nullable is false
      if (this._typeValidator) {
        const outputContract = this.bundles[bundleName]?.manifest?.interfaces?.contracts?.[interfaceName]?.output;
        if (outputContract?.nullable === false && (result === null || result === undefined)) {
          this._contractViolation(
            `${bundleName}.${interfaceName}`,
            `returned null but output.nullable is false\n  Fix: return a valid object from ${interfaceName}, or set output.nullable to true in manifest.yml`
          );
        }
      }

      // Contract validation: check return value against manifest interface schema
      const manifest = this.bundles[bundleName]?.manifest;
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(registry): output nullable enforcement"
```

---

### Task 8: EventBus accepts typeValidator in constructor

**Files:**
- Modify: `~/dev/t/torque-service-eventbus/index.js`
- Create: `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js`

**Step 1: Create the test file with helpers and first tests**

Create `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js` with this content:

```js
/**
 * Tests for typeValidator injection and payload type validation in EventBus.
 */
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { EventBus } from '../index.js';

// ── Test helpers ────────────────────────────────────────────────────

/**
 * Mock typeValidator: basic type checking, tracks calls.
 */
function createMockTypeValidator() {
  const calls = [];
  const fn = (declaredType, actualValue, fieldName) => {
    calls.push({ declaredType, actualValue, fieldName });
    const checks = {
      string: (v) => typeof v === 'string',
      text: (v) => typeof v === 'string',
      uuid: (v) => typeof v === 'string' && /^[0-9a-f]{8}-/.test(v),
      integer: (v) => Number.isInteger(v),
      boolean: (v) => typeof v === 'boolean',
    };
    const check = checks[declaredType];
    if (check && !check(actualValue)) {
      return `field '${fieldName}': expected ${declaredType}, got ${typeof actualValue}`;
    }
    return null;
  };
  fn.calls = calls;
  return fn;
}

/**
 * Capture console.warn calls during a callback.
 */
function captureWarnings(callback) {
  const warnings = [];
  const origWarn = console.warn;
  console.warn = (...args) => warnings.push(args.join(' '));
  try {
    const result = callback();
    return { result, warnings };
  } finally {
    console.warn = origWarn;
  }
}

/**
 * Async version of captureWarnings.
 */
async function captureWarningsAsync(callback) {
  const warnings = [];
  const origWarn = console.warn;
  console.warn = (...args) => warnings.push(args.join(' '));
  try {
    const result = await callback();
    return { result, warnings };
  } finally {
    console.warn = origWarn;
  }
}

// ── Task 8: Constructor injection ───────────────────────────────────

describe('EventBus typeValidator injection', () => {
  it('stores typeValidator when provided', () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    assert.equal(bus._typeValidator, tv);
  });

  it('defaults _typeValidator to null when not provided', () => {
    const bus = new EventBus();
    assert.equal(bus._typeValidator, null);
  });

  it('publish() still works without typeValidator (backward compat)', () => {
    const bus = new EventBus();
    const result = bus.publish('test.event', { key: 'value' });
    assert.equal(result.event, 'test.event');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: FAIL -- `bus._typeValidator` is `undefined`, not the function/null.

**Step 3: Implement -- modify EventBus constructor**

In `~/dev/t/torque-service-eventbus/index.js`, find the constructor (line 9):

```js
  constructor({ db = null, maxLogEntries = 200, hookBus = null, silent = false } = {}) {
```

Replace with:

```js
  constructor({ db = null, maxLogEntries = 200, hookBus = null, typeValidator = null, silent = false } = {}) {
```

Then, right after `this.hookBus = hookBus;` (line 18), add:

```js
    this._typeValidator = typeValidator;
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: ALL tests pass (new ones and existing ones).

**Step 5: Commit**

```bash
cd ~/dev/t/torque-service-eventbus && git add -A && git commit -m "feat(eventbus): accept typeValidator in constructor"
```

---

### Task 9: EventBus publish() payload type validation

**Files:**
- Modify: `~/dev/t/torque-service-eventbus/index.js`
- Modify: `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js`

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js`:

```js
// ── Task 9: publish() payload type validation ───────────────────────

describe('EventBus publish() payload type validation', () => {
  it('warns when payload field has wrong type (warn mode)', () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    const { result, warnings } = captureWarnings(() =>
      bus.publish('task.created', { taskId: 42, title: 'Test' })
    );

    assert.equal(result.event, 'task.created');
    assert.ok(warnings.some(w => w.includes('taskId')), `should warn about 'taskId', got: ${JSON.stringify(warnings)}`);
  });

  it('throws when payload field has wrong type (strict mode)', () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    assert.throws(
      () => bus.publish('task.created', { taskId: 42, title: 'Test' }),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('taskId'), `should mention 'taskId', got: ${err.message}`);
        return true;
      }
    );
  });

  it('passes when all payload fields have correct types', () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    const result = bus.publish('task.created', {
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      title: 'Test',
    });
    assert.equal(result.event, 'task.created');
    assert.ok(tv.calls.length >= 2, `typeValidator should check payload fields, got ${tv.calls.length} calls`);
  });

  it('skips type validation when no typeValidator', () => {
    const bus = new EventBus(); // no typeValidator
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    // Wrong type but no validator -- should NOT throw
    // (existing field presence check still runs, so both fields must be present)
    const result = bus.publish('task.created', { taskId: 42, title: 'Test' });
    assert.equal(result.event, 'task.created');
  });

  it('does not type-check fields missing from payload (presence check handles that)', () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    captureWarnings(() => bus.publish('task.created', { taskId: '550e8400-e29b-41d4-a716-446655440000' }));
    // title is missing -- presence check catches it, but typeValidator should NOT be called for 'title'
    const titleCalls = tv.calls.filter(c => c.fieldName === 'title');
    assert.equal(titleCalls.length, 0, 'should not type-check missing payload fields');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: FAIL -- no type validation in publish() yet.

**Step 3: Implement payload type validation in publish()**

In `~/dev/t/torque-service-eventbus/index.js`, find the payload validation section in `publish()` (around line 102-121). Inside the first `for` loop (declared fields check), add a type validation call. The current loop is:

```js
      for (const field of declaredFields) {
        if (!actualFields.includes(field)) {
          this._contractViolation(
            `Event '${eventName}' payload missing declared field '${field}'\n  Fix: add '${field}' to payload in ${bundle}/logic.js, or remove from events.publishes schema in manifest.yml`
          );
        }
      }
```

Replace it with:

```js
      for (const field of declaredFields) {
        if (!actualFields.includes(field)) {
          this._contractViolation(
            `Event '${eventName}' payload missing declared field '${field}'\n  Fix: add '${field}' to payload in ${bundle}/logic.js, or remove from events.publishes schema in manifest.yml`
          );
        } else if (this._typeValidator && payload[field] !== undefined) {
          const violation = this._typeValidator(schema[field], payload[field], field);
          if (violation) {
            this._contractViolation(
              `Event '${eventName}' payload type error: ${violation}`
            );
          }
        }
      }
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: ALL tests pass.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-service-eventbus && git add -A && git commit -m "feat(eventbus): publish() payload type validation via typeValidator"
```

---

### Task 10: EventBus extract shared helper + publishAsync() type validation

**Files:**
- Modify: `~/dev/t/torque-service-eventbus/index.js`
- Modify: `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js`

This task does two things: (1) extracts the duplicated validation logic from `publish()` and `publishAsync()` into a shared `_validatePublish()` method, and (2) ensures `publishAsync()` gets the same type validation that `publish()` now has.

**Step 1: Write the failing tests**

Append to `~/dev/t/torque-service-eventbus/test/eventbus-type-validation.test.js`:

```js
// ── Task 10: publishAsync() type validation + shared helper ─────────

describe('EventBus publishAsync() payload type validation', () => {
  it('warns when payload field has wrong type (warn mode)', async () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    const { result, warnings } = await captureWarningsAsync(() =>
      bus.publishAsync('task.created', { taskId: 42, title: 'Test' })
    );

    assert.equal(result.event, 'task.created');
    assert.ok(warnings.some(w => w.includes('taskId')), `should warn about 'taskId', got: ${JSON.stringify(warnings)}`);
  });

  it('throws when payload field has wrong type (strict mode)', async () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    await assert.rejects(
      () => bus.publishAsync('task.created', { taskId: 42, title: 'Test' }),
      (err) => {
        assert.equal(err.name, 'ContractViolationError');
        assert.ok(err.message.includes('taskId'));
        return true;
      }
    );
  });

  it('passes when all payload fields have correct types', async () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    const result = await bus.publishAsync('task.created', {
      taskId: '550e8400-e29b-41d4-a716-446655440000',
      title: 'Test',
    });
    assert.equal(result.event, 'task.created');
  });

  it('skips type validation when no typeValidator', async () => {
    const bus = new EventBus(); // no typeValidator
    bus.setValidationMode('strict');
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid', title: 'string' } },
    ]);

    const result = await bus.publishAsync('task.created', { taskId: 42, title: 'Test' });
    assert.equal(result.event, 'task.created');
  });
});

describe('EventBus _validatePublish shared helper', () => {
  it('is a method on EventBus instances', () => {
    const bus = new EventBus();
    assert.equal(typeof bus._validatePublish, 'function');
  });

  it('is used by both publish() and publishAsync() (same behavior)', async () => {
    const tv = createMockTypeValidator();
    const bus = new EventBus({ typeValidator: tv });
    bus.setValidationMode('strict');
    bus.registerDeclaredEvents('tasks', ['task.created']);
    bus.registerEventSchemas('tasks', [
      { name: 'task.created', schema: { taskId: 'uuid' } },
    ]);

    // Both should throw the same ContractViolationError for undeclared events
    assert.throws(
      () => bus.publish('task.unknown', {}, { publisher: 'tasks' }),
      (err) => err.name === 'ContractViolationError'
    );

    await assert.rejects(
      () => bus.publishAsync('task.unknown', {}, { publisher: 'tasks' }),
      (err) => err.name === 'ContractViolationError'
    );
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: FAIL -- `publishAsync()` doesn't have type validation, and `_validatePublish` doesn't exist.

**Step 3: Implement the shared helper and refactor both methods**

In `~/dev/t/torque-service-eventbus/index.js`, add a new `_validatePublish()` method. Place it right after the `_contractViolation()` method (after line 68):

```js

  /**
   * Shared validation for publish() and publishAsync().
   * Checks: undeclared event, payload field presence, extra fields, field types.
   */
  _validatePublish(eventName, payload, publisher) {
    // Check if publisher publishes an event not declared in its manifest
    if (publisher && this._declaredEvents.has(publisher)) {
      const declared = this._declaredEvents.get(publisher);
      if (!declared.has(eventName)) {
        this._contractViolation(
          `Bundle '${publisher}' published undeclared event '${eventName}'. ` +
          `Declared events: [${[...declared].join(', ')}]`
        );
      }
    }

    // Validate payload against declared schema
    if (this._eventSchemas.has(eventName) && payload) {
      const { schema, bundle } = this._eventSchemas.get(eventName);
      const declaredFields = Object.keys(schema);
      const actualFields = Object.keys(payload);
      for (const field of declaredFields) {
        if (!actualFields.includes(field)) {
          this._contractViolation(
            `Event '${eventName}' payload missing declared field '${field}'\n  Fix: add '${field}' to payload in ${bundle}/logic.js, or remove from events.publishes schema in manifest.yml`
          );
        } else if (this._typeValidator && payload[field] !== undefined) {
          const violation = this._typeValidator(schema[field], payload[field], field);
          if (violation) {
            this._contractViolation(
              `Event '${eventName}' payload type error: ${violation}`
            );
          }
        }
      }
      for (const field of actualFields) {
        if (!declaredFields.includes(field)) {
          this._contractViolation(
            `Event '${eventName}' payload has undeclared field '${field}'\n  Fix: add '${field}: ${typeof payload[field]}' to event schema in ${bundle}/manifest.yml`
          );
        }
      }
    }
  }
```

Now replace the validation sections in both `publish()` and `publishAsync()`.

**In `publish()` (around lines 90-121):** Replace everything from `// Check if publisher publishes an event not declared` through the end of the schema validation block (the closing `}` before `// Hook: before publish`) with:

```js
    this._validatePublish(eventName, payload, publisher);
```

**In `publishAsync()` (around lines 190-221):** Same replacement -- remove the duplicated validation block and replace with:

```js
    this._validatePublish(eventName, payload, publisher);
```

After this refactor, `publish()` should look like:

```js
  publish(eventName, payload, { publisher = null } = {}) {
    this._validatePublish(eventName, payload, publisher);

    // Hook: before publish
    if (this.hookBus) {
```

And `publishAsync()` should look like:

```js
  async publishAsync(eventName, payload, { publisher = null } = {}) {
    this._validatePublish(eventName, payload, publisher);

    // Hook: before publish
    if (this.hookBus) {
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-service-eventbus && npm test
```

Expected: ALL tests pass -- both old tests (existing behavior preserved) and new tests (publishAsync type validation + helper exists).

**Step 5: Commit**

```bash
cd ~/dev/t/torque-service-eventbus && git add -A && git commit -m "refactor(eventbus): extract _validatePublish helper, add publishAsync type validation"
```

---

### Task 11: Boot wiring -- connect @torquedev/schema to Registry and EventBus

**Files:**
- Modify: `~/dev/t/torque-core/boot.js`

**Step 1: Read the current boot.js to confirm context**

Verify that `~/dev/t/torque-core/boot.js` still has the Registry and EventBus construction at lines ~46-56:

```js
  const eventBus = new EventBus({ db: dataLayer.db, hookBus, silent: true });

  const registry = new Registry({
    dataLayer,
    eventBus,
    hookBus,
    createScopedData: (dl, name) => new BundleScopedData(dl, name),
    silent: true,
  });
```

**Step 2: Add typeValidator wiring**

In `~/dev/t/torque-core/boot.js`, find this line (around line 48):

```js
  const eventBus = new EventBus({ db: dataLayer.db, hookBus, silent: true });
```

Insert the following block BEFORE that line (after `const hookBus = new HookBus();`):

```js

  // Wire @torquedev/schema type validation (optional -- gracefully degrades if not installed)
  let typeValidator = null;
  try {
    const { createTypeValidator } = await import('@torquedev/schema');
    typeValidator = createTypeValidator();
  } catch {
    // @torquedev/schema not installed -- type validation disabled
  }

```

Then modify the EventBus construction to pass `typeValidator`:

```js
  const eventBus = new EventBus({ db: dataLayer.db, hookBus, typeValidator, silent: true });
```

And modify the Registry construction to pass `typeValidator`:

```js
  const registry = new Registry({
    dataLayer,
    eventBus,
    hookBus,
    typeValidator,
    createScopedData: (dl, name) => new BundleScopedData(dl, name),
    silent: true,
  });
```

The complete section should now read:

```js
  // 2. Create shared infrastructure
  const dataLayer = new DataLayer(db);
  const hookBus = new HookBus();

  // Wire @torquedev/schema type validation (optional -- gracefully degrades if not installed)
  let typeValidator = null;
  try {
    const { createTypeValidator } = await import('@torquedev/schema');
    typeValidator = createTypeValidator();
  } catch {
    // @torquedev/schema not installed -- type validation disabled
  }

  const eventBus = new EventBus({ db: dataLayer.db, hookBus, typeValidator, silent: true });

  const registry = new Registry({
    dataLayer,
    eventBus,
    hookBus,
    typeValidator,
    createScopedData: (dl, name) => new BundleScopedData(dl, name),
    silent: true,
  });
```

**Step 3: Run existing tests to confirm backward compatibility**

```bash
cd ~/dev/t/torque-core && npm test
```

Expected: ALL tests pass. The `try/catch` around the import means boot.js works fine whether `@torquedev/schema` is installed or not.

**Step 4: If Phase 1 is complete, verify end-to-end**

If `@torquedev/schema` is available (Phase 1 done and linked), you can verify the wiring works:

```bash
cd ~/dev/t/torque-core && node -e "
  import('./boot.js').then(m => console.log('boot.js imported OK'));
"
```

If @torquedev/schema is not yet available, the try/catch silently sets `typeValidator = null` -- that's correct behavior.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-core && git add -A && git commit -m "feat(boot): wire @torquedev/schema typeValidator into Registry and EventBus"
```

---

## Summary

| Task | Repo | What |
|------|------|------|
| 1 | torque (dev-link.sh) | Add `@torquedev/schema` symlink |
| 2 | torque-core | Registry accepts `typeValidator` in constructor |
| 3 | torque-core | Input validation: required fields + type checking |
| 4 | torque-core | Output type validation (extend existing shape check) |
| 5 | torque-core | Output array validation (`output.type === 'array'`) |
| 6 | torque-core | Output extra field detection |
| 7 | torque-core | Output nullable enforcement |
| 8 | torque-service-eventbus | EventBus accepts `typeValidator` in constructor |
| 9 | torque-service-eventbus | `publish()` payload type validation |
| 10 | torque-service-eventbus | Extract `_validatePublish()` helper + `publishAsync()` type validation |
| 11 | torque-core | Boot wiring: import `@torquedev/schema`, pass to Registry + EventBus |

**New test files created:**
- `torque-core/test/registry-type-validation.test.js` (Tasks 2-7)
- `torque-service-eventbus/test/eventbus-type-validation.test.js` (Tasks 8-10)

**Files modified:**
- `dev-link.sh` (Task 1)
- `torque-core/kernel/registry.js` (Tasks 2-7)
- `torque-core/boot.js` (Task 11)
- `torque-service-eventbus/index.js` (Tasks 8-10)

**Key backward compatibility guarantee:** When `typeValidator` is `null` (the default), every new validation path is skipped. All existing tests continue to pass without modification.
