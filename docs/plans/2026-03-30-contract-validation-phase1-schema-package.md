# Phase 1: `@torquedev/schema` Package Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Create the standalone `@torquedev/schema` package that provides type validators, a factory for kernel injection, and required-field checking — with zero dependencies.
**Architecture:** A new repo `torque-schema` at `~/dev/t/torque-schema/` containing three source modules (`types.js` for built-in type checkers, `validator.js` for the `createTypeValidator` factory, `required.js` for required-field validation) plus a barrel `index.js`. Tests use Node's built-in test runner. The factory returns a function matching the kernel injection contract: `(declaredType, actualValue, fieldName) => string | null`.
**Tech Stack:** Node.js (ESM-only), `node:test` + `node:assert/strict`, zero dependencies.

**Design doc:** `~/dev/t/torque/docs/specs/2026-03-30-contract-validation-design.md` (Section 1 & Section 4)

---

### Task 1: Initialize the repo and package.json

**Files:**
- Create: `~/dev/t/torque-schema/` (directory)
- Create: `~/dev/t/torque-schema/package.json`
- Create: `~/dev/t/torque-schema/.gitignore`

**Step 1: Create directory and initialize git**
```bash
mkdir -p ~/dev/t/torque-schema
cd ~/dev/t/torque-schema
git init
```
Expected: `Initialized empty Git repository in ~/dev/t/torque-schema/.git/`

**Step 2: Create package.json**

Create `~/dev/t/torque-schema/package.json` with exactly this content:

```json
{
  "name": "@torquedev/schema",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "description": "Type validators and contract checking for Torque. Zero dependencies.",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

**Step 3: Create .gitignore**

Create `~/dev/t/torque-schema/.gitignore` with exactly this content:

```
node_modules/
.DS_Store
```

**Step 4: Commit**
```bash
cd ~/dev/t/torque-schema
git add -A && git commit -m "chore: initialize @torquedev/schema package"
```

---

### Task 2: Implement and test the `string` and `text` type validators

**Files:**
- Create: `~/dev/t/torque-schema/types.js`
- Create: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the failing test**

Create `~/dev/t/torque-schema/test/types.test.js` with exactly this content:

```js
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { validators } from '../types.js';

describe('validators.string', () => {
  it('accepts a string', () => {
    assert.strictEqual(validators.string('hello'), true);
  });

  it('accepts an empty string', () => {
    assert.strictEqual(validators.string(''), true);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.string(42), false);
  });

  it('rejects null', () => {
    assert.strictEqual(validators.string(null), false);
  });

  it('rejects undefined', () => {
    assert.strictEqual(validators.string(undefined), false);
  });
});

describe('validators.text (alias for string)', () => {
  it('accepts a string', () => {
    assert.strictEqual(validators.text('hello'), true);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.text(42), false);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: FAIL — cannot find module `../types.js`

**Step 3: Write minimal implementation**

Create `~/dev/t/torque-schema/types.js` with exactly this content:

```js
/**
 * Built-in type validators for @torquedev/schema.
 *
 * Each validator is a function: (value) => boolean
 * true = value matches the type, false = it doesn't.
 */

/** @type {Map<string, (v: any) => boolean>} */
const validators = new Map();

// ── String ──────────────────────────────────────────────
validators.set('string', (v) => typeof v === 'string');
validators.set('text', validators.get('string'));

/**
 * Register a custom type validator.
 * @param {string} name - Type name (e.g., 'phone', 'currency_cents')
 * @param {(v: any) => boolean} checkFn - Returns true if value matches
 */
function defineType(name, checkFn) {
  if (typeof name !== 'string' || !name) {
    throw new Error('defineType: name must be a non-empty string');
  }
  if (typeof checkFn !== 'function') {
    throw new Error('defineType: checkFn must be a function');
  }
  validators.set(name, checkFn);
}

export { validators, defineType };
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 7 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add string/text type validators"
```

---

### Task 3: Add `uuid` type validator with tests

**Files:**
- Modify: `~/dev/t/torque-schema/types.js`
- Modify: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the failing test**

Append to the end of `~/dev/t/torque-schema/test/types.test.js`:

```js

describe('validators.uuid', () => {
  it('accepts a valid v4 UUID', () => {
    assert.strictEqual(validators.uuid('550e8400-e29b-41d4-a716-446655440000'), true);
  });

  it('accepts a valid v1 UUID', () => {
    assert.strictEqual(validators.uuid('6ba7b810-9dad-11d1-80b4-00c04fd430c8'), true);
  });

  it('accepts uppercase UUID', () => {
    assert.strictEqual(validators.uuid('550E8400-E29B-41D4-A716-446655440000'), true);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.uuid(42), false);
  });

  it('rejects a random string', () => {
    assert.strictEqual(validators.uuid('not-a-uuid'), false);
  });

  it('rejects null', () => {
    assert.strictEqual(validators.uuid(null), false);
  });

  it('rejects a UUID missing a section', () => {
    assert.strictEqual(validators.uuid('550e8400-e29b-41d4-a716'), false);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: FAIL — `validators.uuid` is undefined

**Step 3: Write minimal implementation**

Add the following to `~/dev/t/torque-schema/types.js`, right after the `text` alias line (`validators.set('text', validators.get('string'));`):

```js

// ── UUID ────────────────────────────────────────────────
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
validators.set('uuid', (v) => typeof v === 'string' && UUID_RE.test(v));
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 14 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add uuid type validator"
```

---

### Task 4: Add `integer`, `float`/`decimal`, and `boolean` type validators with tests

**Files:**
- Modify: `~/dev/t/torque-schema/types.js`
- Modify: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the failing tests**

Append to the end of `~/dev/t/torque-schema/test/types.test.js`:

```js

describe('validators.integer', () => {
  it('accepts an integer', () => {
    assert.strictEqual(validators.integer(42), true);
  });

  it('accepts zero', () => {
    assert.strictEqual(validators.integer(0), true);
  });

  it('accepts negative integer', () => {
    assert.strictEqual(validators.integer(-7), true);
  });

  it('rejects a float', () => {
    assert.strictEqual(validators.integer(3.14), false);
  });

  it('rejects a string', () => {
    assert.strictEqual(validators.integer('42'), false);
  });

  it('rejects NaN', () => {
    assert.strictEqual(validators.integer(NaN), false);
  });
});

describe('validators.float', () => {
  it('accepts a float', () => {
    assert.strictEqual(validators.float(3.14), true);
  });

  it('accepts an integer (integers are valid floats)', () => {
    assert.strictEqual(validators.float(42), true);
  });

  it('accepts zero', () => {
    assert.strictEqual(validators.float(0), true);
  });

  it('rejects NaN', () => {
    assert.strictEqual(validators.float(NaN), false);
  });

  it('rejects Infinity', () => {
    assert.strictEqual(validators.float(Infinity), false);
  });

  it('rejects a string', () => {
    assert.strictEqual(validators.float('3.14'), false);
  });
});

describe('validators.decimal (alias for float)', () => {
  it('accepts a float', () => {
    assert.strictEqual(validators.decimal(3.14), true);
  });

  it('rejects a string', () => {
    assert.strictEqual(validators.decimal('3.14'), false);
  });
});

describe('validators.boolean', () => {
  it('accepts true', () => {
    assert.strictEqual(validators.boolean(true), true);
  });

  it('accepts false', () => {
    assert.strictEqual(validators.boolean(false), true);
  });

  it('rejects 1', () => {
    assert.strictEqual(validators.boolean(1), false);
  });

  it('rejects "true"', () => {
    assert.strictEqual(validators.boolean('true'), false);
  });

  it('rejects null', () => {
    assert.strictEqual(validators.boolean(null), false);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: FAIL — `validators.integer` is undefined

**Step 3: Write minimal implementation**

Add the following to `~/dev/t/torque-schema/types.js`, right after the uuid block:

```js

// ── Integer ─────────────────────────────────────────────
validators.set('integer', (v) => Number.isInteger(v));

// ── Float / Decimal ─────────────────────────────────────
validators.set('float', (v) => typeof v === 'number' && Number.isFinite(v));
validators.set('decimal', validators.get('float'));

// ── Boolean ─────────────────────────────────────────────
validators.set('boolean', (v) => typeof v === 'boolean');
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 30 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add integer, float/decimal, boolean type validators"
```

---

### Task 5: Add `timestamp`/`datetime`, `email`, and `url` type validators with tests

**Files:**
- Modify: `~/dev/t/torque-schema/types.js`
- Modify: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the failing tests**

Append to the end of `~/dev/t/torque-schema/test/types.test.js`:

```js

describe('validators.timestamp', () => {
  it('accepts an ISO 8601 string', () => {
    assert.strictEqual(validators.timestamp('2026-03-30T17:00:00Z'), true);
  });

  it('accepts a date-only ISO string', () => {
    assert.strictEqual(validators.timestamp('2026-03-30'), true);
  });

  it('rejects "last tuesday"', () => {
    assert.strictEqual(validators.timestamp('last tuesday'), false);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.timestamp(1711814400000), false);
  });

  it('rejects an empty string', () => {
    assert.strictEqual(validators.timestamp(''), false);
  });
});

describe('validators.datetime (alias for timestamp)', () => {
  it('accepts an ISO 8601 string', () => {
    assert.strictEqual(validators.datetime('2026-03-30T17:00:00Z'), true);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.datetime(42), false);
  });
});

describe('validators.email', () => {
  it('accepts a valid email', () => {
    assert.strictEqual(validators.email('user@example.com'), true);
  });

  it('accepts email with subdomain', () => {
    assert.strictEqual(validators.email('user@mail.example.com'), true);
  });

  it('rejects a string without @', () => {
    assert.strictEqual(validators.email('not-an-email'), false);
  });

  it('rejects a string with spaces', () => {
    assert.strictEqual(validators.email('user @example.com'), false);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.email(42), false);
  });
});

describe('validators.url', () => {
  it('accepts an https URL', () => {
    assert.strictEqual(validators.url('https://example.com'), true);
  });

  it('accepts an http URL with path', () => {
    assert.strictEqual(validators.url('http://example.com/path?q=1'), true);
  });

  it('rejects a random string', () => {
    assert.strictEqual(validators.url('not-a-url'), false);
  });

  it('rejects a number', () => {
    assert.strictEqual(validators.url(42), false);
  });

  it('rejects an empty string', () => {
    assert.strictEqual(validators.url(''), false);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: FAIL — `validators.timestamp` is undefined

**Step 3: Write minimal implementation**

Add the following to `~/dev/t/torque-schema/types.js`, right after the boolean block:

```js

// ── Timestamp / Datetime ────────────────────────────────
const ISO_PREFIX_RE = /^\d{4}-\d{2}/;
validators.set('timestamp', (v) =>
  typeof v === 'string' && ISO_PREFIX_RE.test(v) && !isNaN(Date.parse(v))
);
validators.set('datetime', validators.get('timestamp'));

// ── Email ───────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
validators.set('email', (v) => typeof v === 'string' && EMAIL_RE.test(v));

// ── URL ─────────────────────────────────────────────────
validators.set('url', (v) => {
  if (typeof v !== 'string') return false;
  try { new URL(v); return true; } catch { return false; }
});
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 44 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add timestamp, email, url type validators"
```

---

### Task 6: Add `object` and `array` type validators with tests

**Files:**
- Modify: `~/dev/t/torque-schema/types.js`
- Modify: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the failing tests**

Append to the end of `~/dev/t/torque-schema/test/types.test.js`:

```js

describe('validators.object', () => {
  it('accepts a plain object', () => {
    assert.strictEqual(validators.object({ foo: 1 }), true);
  });

  it('accepts an empty object', () => {
    assert.strictEqual(validators.object({}), true);
  });

  it('rejects an array', () => {
    assert.strictEqual(validators.object([1, 2]), false);
  });

  it('rejects null', () => {
    assert.strictEqual(validators.object(null), false);
  });

  it('rejects a string', () => {
    assert.strictEqual(validators.object('{}'), false);
  });
});

describe('validators.array', () => {
  it('accepts an array', () => {
    assert.strictEqual(validators.array([1, 2, 3]), true);
  });

  it('accepts an empty array', () => {
    assert.strictEqual(validators.array([]), true);
  });

  it('rejects an object', () => {
    assert.strictEqual(validators.array({ length: 2 }), false);
  });

  it('rejects a string', () => {
    assert.strictEqual(validators.array('not an array'), false);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: FAIL — `validators.object` is undefined

**Step 3: Write minimal implementation**

Add the following to `~/dev/t/torque-schema/types.js`, right after the url block:

```js

// ── Object ──────────────────────────────────────────────
validators.set('object', (v) => typeof v === 'object' && v !== null && !Array.isArray(v));

// ── Array ───────────────────────────────────────────────
validators.set('array', (v) => Array.isArray(v));
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 53 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add object and array type validators"
```

---

### Task 7: Implement and test the `createTypeValidator` factory

**Files:**
- Create: `~/dev/t/torque-schema/validator.js`
- Create: `~/dev/t/torque-schema/test/validator.test.js`

**Step 1: Write the failing test**

Create `~/dev/t/torque-schema/test/validator.test.js` with exactly this content:

```js
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createTypeValidator } from '../validator.js';

describe('createTypeValidator', () => {
  it('returns a function', () => {
    const validate = createTypeValidator();
    assert.strictEqual(typeof validate, 'function');
  });
});

describe('validate() — basic types', () => {
  const validate = createTypeValidator();

  it('returns null for a valid string', () => {
    assert.strictEqual(validate('string', 'hello', 'name'), null);
  });

  it('returns a violation string for invalid string', () => {
    const result = validate('string', 42, 'name');
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /field 'name'/);
    assert.match(result, /expected string/);
    assert.match(result, /got number/);
  });

  it('returns null for a valid uuid', () => {
    assert.strictEqual(validate('uuid', '550e8400-e29b-41d4-a716-446655440000', 'id'), null);
  });

  it('returns a violation string for invalid uuid', () => {
    const result = validate('uuid', 'nope', 'id');
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /field 'id'/);
    assert.match(result, /expected uuid/);
  });

  it('returns null for a valid integer', () => {
    assert.strictEqual(validate('integer', 42, 'count'), null);
  });

  it('returns null for a valid boolean', () => {
    assert.strictEqual(validate('boolean', true, 'active'), null);
  });

  it('handles type aliases (text -> string)', () => {
    assert.strictEqual(validate('text', 'hello', 'desc'), null);
  });

  it('handles type aliases (decimal -> float)', () => {
    assert.strictEqual(validate('decimal', 3.14, 'price'), null);
  });

  it('handles type aliases (datetime -> timestamp)', () => {
    assert.strictEqual(validate('datetime', '2026-03-30T17:00:00Z', 'created'), null);
  });

  it('returns a violation for unknown type', () => {
    const result = validate('banana', 'hello', 'fruit');
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /unknown type 'banana'/);
  });
});

describe('validate() — violation message format', () => {
  const validate = createTypeValidator();

  it('includes the actual JS type in the message', () => {
    const result = validate('uuid', null, 'user_id');
    assert.match(result, /got null/);
  });

  it('says "got array" for arrays', () => {
    const result = validate('string', [1, 2], 'tags');
    assert.match(result, /got array/);
  });

  it('says "got undefined" for undefined', () => {
    const result = validate('string', undefined, 'name');
    assert.match(result, /got undefined/);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/validator.test.js'
```
Expected: FAIL — cannot find module `../validator.js`

**Step 3: Write minimal implementation**

Create `~/dev/t/torque-schema/validator.js` with exactly this content:

```js
/**
 * Factory for creating a type validator function.
 *
 * The returned function matches the kernel injection contract:
 *   validate(declaredType, actualValue, fieldName) => string | null
 *
 * null = valid. string = violation message.
 */

import { validators, defineType } from './types.js';

/**
 * Describe a JS value's type for error messages.
 * @param {any} v
 * @returns {string}
 */
function describeType(v) {
  if (v === null) return 'null';
  if (v === undefined) return 'undefined';
  if (Array.isArray(v)) return 'array';
  return typeof v;
}

/**
 * Create a type validator function.
 * @returns {Function & { registerType: (name: string, checkFn: (v: any) => boolean) => void }}
 */
export function createTypeValidator() {
  function validate(declaredType, actualValue, fieldName) {
    const checker = validators.get(declaredType);
    if (!checker) {
      return `field '${fieldName}': unknown type '${declaredType}'`;
    }
    if (checker(actualValue)) {
      return null;
    }
    return `field '${fieldName}': expected ${declaredType}, got ${describeType(actualValue)}`;
  }

  validate.registerType = function registerType(name, checkFn) {
    defineType(name, checkFn);
  };

  return validate;
}
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/validator.test.js'
```
Expected: All 14 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add createTypeValidator factory"
```

---

### Task 8: Add array-of-type validation (`string[]`, `uuid[]`, etc.)

**Files:**
- Modify: `~/dev/t/torque-schema/validator.js`
- Modify: `~/dev/t/torque-schema/test/validator.test.js`

**Step 1: Write the failing tests**

Append to the end of `~/dev/t/torque-schema/test/validator.test.js`:

```js

describe('validate() — array-of-type (Type[])', () => {
  const validate = createTypeValidator();

  it('returns null for a valid string[]', () => {
    assert.strictEqual(validate('string[]', ['a', 'b'], 'tags'), null);
  });

  it('returns null for an empty array (string[])', () => {
    assert.strictEqual(validate('string[]', [], 'tags'), null);
  });

  it('returns a violation when array contains wrong type', () => {
    const result = validate('string[]', ['a', 42], 'tags');
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /field 'tags\[1\]'/);
    assert.match(result, /expected string/);
    assert.match(result, /got number/);
  });

  it('returns a violation when value is not an array', () => {
    const result = validate('string[]', 'not an array', 'tags');
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /field 'tags'/);
    assert.match(result, /expected array/);
  });

  it('works with uuid[]', () => {
    assert.strictEqual(
      validate('uuid[]', ['550e8400-e29b-41d4-a716-446655440000'], 'ids'),
      null
    );
  });

  it('catches bad item in uuid[]', () => {
    const result = validate('uuid[]', ['550e8400-e29b-41d4-a716-446655440000', 'bad'], 'ids');
    assert.match(result, /field 'ids\[1\]'/);
    assert.match(result, /expected uuid/);
  });

  it('works with integer[]', () => {
    assert.strictEqual(validate('integer[]', [1, 2, 3], 'counts'), null);
  });

  it('works with object[]', () => {
    assert.strictEqual(validate('object[]', [{ a: 1 }, { b: 2 }], 'items'), null);
  });

  it('returns a violation for unknown inner type', () => {
    const result = validate('banana[]', ['hello'], 'fruit');
    assert.match(result, /unknown type 'banana'/);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/validator.test.js'
```
Expected: FAIL — `string[]` is an unknown type (no array-of-type parsing yet)

**Step 3: Write minimal implementation**

In `~/dev/t/torque-schema/validator.js`, replace the `validate` function body inside `createTypeValidator()` with this updated version. Find the existing `function validate(declaredType, actualValue, fieldName)` block and replace it:

Find this:
```js
  function validate(declaredType, actualValue, fieldName) {
    const checker = validators.get(declaredType);
    if (!checker) {
      return `field '${fieldName}': unknown type '${declaredType}'`;
    }
    if (checker(actualValue)) {
      return null;
    }
    return `field '${fieldName}': expected ${declaredType}, got ${describeType(actualValue)}`;
  }
```

Replace with:
```js
  function validate(declaredType, actualValue, fieldName) {
    // ── Array-of-type: "string[]", "uuid[]", etc. ──
    if (declaredType.endsWith('[]')) {
      const innerType = declaredType.slice(0, -2);
      const innerChecker = validators.get(innerType);
      if (!innerChecker) {
        return `field '${fieldName}': unknown type '${innerType}'`;
      }
      if (!Array.isArray(actualValue)) {
        return `field '${fieldName}': expected array, got ${describeType(actualValue)}`;
      }
      for (let i = 0; i < actualValue.length; i++) {
        if (!innerChecker(actualValue[i])) {
          return `field '${fieldName}[${i}]': expected ${innerType}, got ${describeType(actualValue[i])}`;
        }
      }
      return null;
    }

    // ── Scalar types ──
    const checker = validators.get(declaredType);
    if (!checker) {
      return `field '${fieldName}': unknown type '${declaredType}'`;
    }
    if (checker(actualValue)) {
      return null;
    }
    return `field '${fieldName}': expected ${declaredType}, got ${describeType(actualValue)}`;
  }
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/validator.test.js'
```
Expected: All 23 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add array-of-type validation (string[], uuid[], etc.)"
```

---

### Task 9: Add custom type registration via `registerType`

**Files:**
- Modify: `~/dev/t/torque-schema/test/validator.test.js`

This is test-only — the implementation already exists from Task 7. We just need to verify it works.

**Step 1: Write the tests**

Append to the end of `~/dev/t/torque-schema/test/validator.test.js`:

```js

describe('validate.registerType() — custom types', () => {
  it('registers and validates a custom phone type', () => {
    const validate = createTypeValidator();
    validate.registerType('phone', (v) => typeof v === 'string' && /^\+?[1-9]\d{1,14}$/.test(v));

    assert.strictEqual(validate('phone', '+15551234567', 'mobile'), null);
    const fail = validate('phone', 'not-a-phone', 'mobile');
    assert.match(fail, /field 'mobile'/);
    assert.match(fail, /expected phone/);
  });

  it('registers and validates a custom currency_cents type', () => {
    const validate = createTypeValidator();
    validate.registerType('currency_cents', (v) => Number.isInteger(v) && v >= 0);

    assert.strictEqual(validate('currency_cents', 1500, 'price'), null);
    const fail = validate('currency_cents', -1, 'price');
    assert.match(fail, /field 'price'/);
  });

  it('throws if name is not a string', () => {
    const validate = createTypeValidator();
    assert.throws(() => validate.registerType(42, () => true), /name must be a non-empty string/);
  });

  it('throws if checkFn is not a function', () => {
    const validate = createTypeValidator();
    assert.throws(() => validate.registerType('foo', 'not a function'), /checkFn must be a function/);
  });

  it('custom array-of-type works after registration', () => {
    const validate = createTypeValidator();
    validate.registerType('phone', (v) => typeof v === 'string' && /^\+?[1-9]\d{1,14}$/.test(v));

    assert.strictEqual(validate('phone[]', ['+15551234567', '+19998887777'], 'phones'), null);
    const fail = validate('phone[]', ['+15551234567', 'bad'], 'phones');
    assert.match(fail, /field 'phones\[1\]'/);
  });
});
```

**Step 2: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/validator.test.js'
```
Expected: All 28 tests pass. (These should pass immediately — the implementation is already in place.)

**Step 3: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "test: add custom type registration tests"
```

---

### Task 10: Add `defineType` tests in types.test.js

**Files:**
- Modify: `~/dev/t/torque-schema/test/types.test.js`

**Step 1: Write the tests**

Append to the end of `~/dev/t/torque-schema/test/types.test.js`:

```js

describe('defineType', () => {
  // Import defineType — add this import at the top of the file alongside validators
  // Actually, since we can't modify the top easily, we'll use dynamic import
  it('registers a new type on the validators map', async () => {
    const { defineType, validators: v } = await import('../types.js');
    defineType('test_custom', (val) => typeof val === 'string' && val.startsWith('test_'));
    assert.strictEqual(v.get('test_custom')('test_hello'), true);
    assert.strictEqual(v.get('test_custom')('nope'), false);
  });

  it('throws on empty name', async () => {
    const { defineType } = await import('../types.js');
    assert.throws(() => defineType('', () => true), /name must be a non-empty string/);
  });

  it('throws on non-function checkFn', async () => {
    const { defineType } = await import('../types.js');
    assert.throws(() => defineType('bad', 'not-a-fn'), /checkFn must be a function/);
  });
});
```

Wait — that dynamic import approach is fragile because of module caching. Let's do this cleanly instead. Add the `defineType` import at the top of the file alongside `validators`.

Modify the import line at the top of `~/dev/t/torque-schema/test/types.test.js`:

Find:
```js
import { validators } from '../types.js';
```

Replace with:
```js
import { validators, defineType } from '../types.js';
```

Then append to the end of the file:

```js

describe('defineType', () => {
  it('registers a new type on the validators map', () => {
    defineType('test_custom', (val) => typeof val === 'string' && val.startsWith('test_'));
    assert.strictEqual(validators.get('test_custom')('test_hello'), true);
    assert.strictEqual(validators.get('test_custom')('nope'), false);
  });

  it('throws on empty name', () => {
    assert.throws(() => defineType('', () => true), /name must be a non-empty string/);
  });

  it('throws on non-function checkFn', () => {
    assert.throws(() => defineType('bad', 'not-a-fn'), /checkFn must be a function/);
  });
});
```

**Step 2: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/types.test.js'
```
Expected: All 56 tests pass.

**Step 3: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "test: add defineType tests"
```

---

### Task 11: Implement and test `validateRequired`

**Files:**
- Create: `~/dev/t/torque-schema/required.js`
- Create: `~/dev/t/torque-schema/test/required.test.js`

**Step 1: Write the failing test**

Create `~/dev/t/torque-schema/test/required.test.js` with exactly this content:

```js
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { validateRequired } from '../required.js';

describe('validateRequired', () => {
  const contract = {
    userId: { type: 'uuid', required: true },
    name: { type: 'string', required: true },
    bio: { type: 'string' },
  };

  it('returns null when all required fields are present', () => {
    assert.strictEqual(
      validateRequired({ userId: '550e8400-e29b-41d4-a716-446655440000', name: 'Alice', bio: 'hi' }, contract),
      null
    );
  });

  it('returns null when optional field is missing', () => {
    assert.strictEqual(
      validateRequired({ userId: '550e8400-e29b-41d4-a716-446655440000', name: 'Alice' }, contract),
      null
    );
  });

  it('returns a violation when a required field is missing', () => {
    const result = validateRequired({ name: 'Alice' }, contract);
    assert.strictEqual(typeof result, 'string');
    assert.match(result, /required field 'userId' is missing/);
  });

  it('returns the first missing required field', () => {
    const result = validateRequired({}, contract);
    assert.strictEqual(typeof result, 'string');
    // Should find userId first (object key order)
    assert.match(result, /required field 'userId' is missing/);
  });

  it('treats null value as missing', () => {
    const result = validateRequired({ userId: null, name: 'Alice' }, contract);
    assert.match(result, /required field 'userId' is missing/);
  });

  it('treats undefined value as missing', () => {
    const result = validateRequired({ userId: undefined, name: 'Alice' }, contract);
    assert.match(result, /required field 'userId' is missing/);
  });

  it('returns null for empty contract', () => {
    assert.strictEqual(validateRequired({ anything: 'goes' }, {}), null);
  });

  it('returns null when no fields are required', () => {
    const optionalOnly = { bio: { type: 'string' }, age: { type: 'integer' } };
    assert.strictEqual(validateRequired({}, optionalOnly), null);
  });
});
```

**Step 2: Run test to verify it fails**
```bash
cd ~/dev/t/torque-schema && node --test 'test/required.test.js'
```
Expected: FAIL — cannot find module `../required.js`

**Step 3: Write minimal implementation**

Create `~/dev/t/torque-schema/required.js` with exactly this content:

```js
/**
 * Validate that all required fields declared in an input contract are present.
 *
 * @param {object} args - The actual arguments passed by the caller
 * @param {object} inputContract - The contract from the manifest, e.g.:
 *   { userId: { type: 'uuid', required: true }, name: { type: 'string' } }
 * @returns {string | null} null if valid, or a violation message string
 */
export function validateRequired(args, inputContract) {
  for (const [fieldName, spec] of Object.entries(inputContract)) {
    if (!spec.required) continue;
    if (args[fieldName] === undefined || args[fieldName] === null) {
      return `required field '${fieldName}' is missing`;
    }
  }
  return null;
}
```

**Step 4: Run test to verify it passes**
```bash
cd ~/dev/t/torque-schema && node --test 'test/required.test.js'
```
Expected: All 8 tests pass.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add validateRequired for input contract checking"
```

---

### Task 12: Create the barrel export `index.js`

**Files:**
- Create: `~/dev/t/torque-schema/index.js`

**Step 1: Write the barrel**

Create `~/dev/t/torque-schema/index.js` with exactly this content:

```js
/**
 * @torquedev/schema — Type validators and contract checking for Torque.
 *
 * Usage:
 *   import { createTypeValidator, validateRequired } from '@torquedev/schema';
 *
 *   const validate = createTypeValidator();
 *   validate('uuid', someValue, 'fieldName');  // => null or violation string
 *
 *   // Custom types
 *   validate.registerType('phone', (v) => typeof v === 'string' && /^\+?[1-9]\d{1,14}$/.test(v));
 *
 *   // Required field checking
 *   validateRequired(args, inputContract);  // => null or violation string
 */

export { createTypeValidator } from './validator.js';
export { validators, defineType } from './types.js';
export { validateRequired } from './required.js';
```

**Step 2: Verify the barrel works**
```bash
cd ~/dev/t/torque-schema && node -e "
  import { createTypeValidator, validators, defineType, validateRequired } from './index.js';
  console.log('createTypeValidator:', typeof createTypeValidator);
  console.log('validators:', validators instanceof Map);
  console.log('defineType:', typeof defineType);
  console.log('validateRequired:', typeof validateRequired);
" --input-type=module
```
Expected output:
```
createTypeValidator: function
validators: true
defineType: function
validateRequired: function
```

**Step 3: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "feat: add barrel export index.js"
```

---

### Task 13: Full integration test

**Files:**
- Modify: `~/dev/t/torque-schema/test/validator.test.js`

**Step 1: Write the integration tests**

Append to the end of `~/dev/t/torque-schema/test/validator.test.js`:

```js

describe('integration — full workflow via barrel import', () => {
  it('validates a realistic input contract', async () => {
    const { createTypeValidator, validateRequired } = await import('../index.js');
    const validate = createTypeValidator();

    const contract = {
      userId: { type: 'uuid', required: true },
      title: { type: 'string', required: true },
      tags: { type: 'string[]' },
      priority: { type: 'integer' },
    };

    const args = {
      userId: '550e8400-e29b-41d4-a716-446655440000',
      title: 'Fix the bug',
      tags: ['urgent', 'backend'],
      priority: 1,
    };

    // Required check passes
    assert.strictEqual(validateRequired(args, contract), null);

    // Type check each field
    for (const [field, spec] of Object.entries(contract)) {
      if (args[field] !== undefined) {
        assert.strictEqual(validate(spec.type, args[field], field), null, `${field} should be valid`);
      }
    }
  });

  it('catches missing required field then type error', async () => {
    const { createTypeValidator, validateRequired } = await import('../index.js');
    const validate = createTypeValidator();

    const contract = {
      userId: { type: 'uuid', required: true },
      title: { type: 'string', required: true },
    };

    // Missing userId
    const reqResult = validateRequired({ title: 'hi' }, contract);
    assert.match(reqResult, /required field 'userId' is missing/);

    // Wrong type for title
    const typeResult = validate('string', 42, 'title');
    assert.match(typeResult, /field 'title': expected string, got number/);
  });

  it('custom type survives full round-trip', async () => {
    const { createTypeValidator } = await import('../index.js');
    const validate = createTypeValidator();

    validate.registerType('hex_color', (v) => typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v));

    assert.strictEqual(validate('hex_color', '#ff00aa', 'bg_color'), null);
    assert.match(validate('hex_color', 'red', 'bg_color'), /expected hex_color/);
    assert.strictEqual(validate('hex_color[]', ['#ff00aa', '#00ff00'], 'palette'), null);
    assert.match(validate('hex_color[]', ['#ff00aa', 'bad'], 'palette'), /field 'palette\[1\]'/);
  });
});
```

**Step 2: Run the full test suite**
```bash
cd ~/dev/t/torque-schema && node --test 'test/*.test.js'
```
Expected: All tests pass across all three test files (`types.test.js`, `validator.test.js`, `required.test.js`).

**Step 3: Commit**
```bash
cd ~/dev/t/torque-schema && git add -A && git commit -m "test: add integration tests for full barrel workflow"
```

---

### Task 14: Push to GitHub

**Step 1: Create the GitHub repo**
```bash
cd ~/dev/t/torque-schema
gh repo create torque-schema --private --source=. --push
```
Expected: Repo created and all commits pushed.

**Step 2: Verify the push**
```bash
cd ~/dev/t/torque-schema && git log --oneline
```
Expected: 9 commits in order:
1. `chore: initialize @torquedev/schema package`
2. `feat: add string/text type validators`
3. `feat: add uuid type validator`
4. `feat: add integer, float/decimal, boolean type validators`
5. `feat: add timestamp, email, url type validators`
6. `feat: add object and array type validators`
7. `feat: add createTypeValidator factory`
8. `feat: add array-of-type validation (string[], uuid[], etc.)`
9. `test: add custom type registration tests`
10. `test: add defineType tests`
11. `feat: add validateRequired for input contract checking`
12. `feat: add barrel export index.js`
13. `test: add integration tests for full barrel workflow`

**Step 3: Run tests one final time to confirm everything is green**
```bash
cd ~/dev/t/torque-schema && npm test
```
Expected: All tests pass. Zero failures.

---

## Summary

| Task | What it does | Key files |
|------|-------------|-----------|
| 1 | Init repo + package.json | `package.json`, `.gitignore` |
| 2 | `string`/`text` validators | `types.js`, `test/types.test.js` |
| 3 | `uuid` validator | `types.js`, `test/types.test.js` |
| 4 | `integer`, `float`/`decimal`, `boolean` | `types.js`, `test/types.test.js` |
| 5 | `timestamp`/`datetime`, `email`, `url` | `types.js`, `test/types.test.js` |
| 6 | `object`, `array` | `types.js`, `test/types.test.js` |
| 7 | `createTypeValidator` factory | `validator.js`, `test/validator.test.js` |
| 8 | Array-of-type (`string[]`, etc.) | `validator.js`, `test/validator.test.js` |
| 9 | Custom type registration tests | `test/validator.test.js` |
| 10 | `defineType` tests | `test/types.test.js` |
| 11 | `validateRequired` | `required.js`, `test/required.test.js` |
| 12 | Barrel `index.js` | `index.js` |
| 13 | Integration tests | `test/validator.test.js` |
| 14 | Push to GitHub | — |