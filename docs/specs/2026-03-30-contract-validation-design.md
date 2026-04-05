# Contract Validation Overhaul Design

## Goal

Upgrade Torque's contract validation from "field name presence only" to comprehensive type-checked, bidirectional contract enforcement across interfaces, events, and schema -- following Amplifier's kernel philosophy where the kernel provides the mechanism (injection point) and a new standalone package provides the policy (type validators).

## Background

Today Torque validates contracts at a surface level: it checks that declared field names are present in outputs and event payloads, but never checks that values match their declared types. Input contracts aren't validated at all. Several manifest declarations (indexes, `required: true` on schema fields, intents, route handlers, event subscriptions) are either silently ignored or not cross-checked at boot time, leading to runtime surprises instead of early failures.

This design closes every gap in the validation matrix while preserving full backward compatibility for apps that don't opt in.

## Architecture Decision

Based on Amplifier kernel philosophy:

- **Type validation is POLICY** -- the type vocabulary, strictness, and semantics can vary per deployment
- **The call site where validation happens is MECHANISM** -- belongs in the kernel as an injection point
- **Solution: Three-layer pattern**
  - `@torquedev/schema` (new standalone package) -- contains type validators, zero dependencies
  - `torque-core` (kernel) -- accepts optional `typeValidator` function, calls it at the right moments
  - `boot.js` (application layer) -- wires schema into kernel at construction time

This follows the Amplifier pattern where `amplifier-foundation` provides shared utilities outside the kernel, and the kernel provides mechanisms via injection, never policies.

## Section 1: @torquedev/schema Package -- Type Vocabulary

New standalone package (`torque-schema` repo). Zero dependencies. ESM-only, `node --test`.

### Built-in Type Vocabulary

| Type | Validates | Example Pass | Example Fail |
|------|-----------|-------------|-------------|
| `uuid` | RFC 4122 v1-v5 format | `"550e8400-e29b-41d4-a716-446655440000"` | `42`, `"not-a-uuid"` |
| `string` / `text` | typeof === 'string' | `"hello"` | `42`, `null` |
| `integer` | Number.isInteger | `42` | `3.14`, `"42"` |
| `float` / `decimal` | typeof === 'number' && isFinite | `3.14` | `"3.14"`, `NaN` |
| `boolean` | typeof === 'boolean' | `true` | `1`, `"true"` |
| `timestamp` / `datetime` | ISO 8601 string | `"2026-03-30T17:00:00Z"` | `"last tuesday"` |
| `email` | basic format validation (has @, has domain) | `"user@example.com"` | `"not-an-email"` |
| `url` | parseable by new URL() | `"https://example.com"` | `"not-a-url"` |
| `object` | typeof === 'object' && !Array.isArray | `{ foo: 1 }` | `[1,2]`, `"string"` |
| `array` | Array.isArray | `[1, 2, 3]` | `"string"`, `{}` |
| `string[]`, `uuid[]`, etc. | Array where every item matches inner type | `["a", "b"]` | `["a", 42]` |

### Custom Type Registration

```js
const validator = createTypeValidator();
validator.registerType('phone', (v) => typeof v === 'string' && /^\+?[1-9]\d{1,14}$/.test(v));
validator.registerType('currency_cents', (v) => Number.isInteger(v) && v >= 0);
```

### Factory Contract

The factory returns a single function matching the kernel injection contract:

```js
const validate = createTypeValidator();
validate('uuid', someValue, 'fieldName');
// returns null (valid) or "field 'fieldName': expected uuid, got number" (violation string)
```

### Required Field Checking

The package also exports `validateRequired(args, inputContract)` for checking required fields before type checking:

```js
// inputContract from manifest: { userId: { type: 'uuid', required: true }, name: { type: 'string' } }
validateRequired({ name: 'Alice' }, inputContract);
// => "required field 'userId' is missing"
```

Required checking is separate from type checking because `required` is about presence, not type. The registry calls `validateRequired` first, then `typeValidator` on each present field.

### Exports

- `createTypeValidator` -- factory returning validator function
- `validators` -- map of individual type checker functions
- `defineType` -- custom type registration helper
- `validateRequired` -- required field presence checker

### File Structure

```
torque-schema/
  index.js          Barrel exports
  validator.js      createTypeValidator factory
  types.js          Built-in type definitions + defineType + validators map
  test/
    types.test.js       Each built-in type with pass/fail cases
    validator.test.js   Factory, custom types, array types, edge cases
  package.json
```

## Section 2: Kernel Injection Points

The kernel accepts a `typeValidator` function at construction, calls it at the right moments, and routes violations through the existing `warn`/`strict` system. Zero validators live in the kernel itself.

### Registry Changes (`torque-core/kernel/registry.js`)

Constructor accepts `typeValidator`:

```js
constructor({ dataLayer, eventBus, createScopedData, hookBus, typeValidator, ... })
```

Called in three places inside `call()`:

1. **Input validation** (NEW -- biggest gap today). Before calling the handler, validate `args` against `manifest.interfaces.contracts[name].input`. Check `required` fields are present, check each field's type matches its declaration.

2. **Output validation** (EXTENDED). After the handler returns, extend the existing field-presence check to also validate types against `output.shape`, plus handle `output.type: array` with `output.items`.

3. **Output extra field detection** (NEW). Flag fields in the result that aren't declared in the shape (matching how events already work bidirectionally).

### EventBus Changes (`torque-service-eventbus`)

Constructor accepts `typeValidator`. Called during `publish()` / `publishAsync()` -- extend the existing payload field check to also validate types against registered event schemas.

### boot.js Changes

```js
import { createTypeValidator } from '@torquedev/schema';

const typeValidator = createTypeValidator();
const registry = new Registry({ ..., typeValidator });
const eventBus = new EventBus({ ..., typeValidator });
```

### Backward Compatibility

If `typeValidator` is `null`/`undefined` (the default), all new validation is skipped. Existing apps that don't import `@torquedev/schema` work exactly as before.

## Section 3: Full Validation Matrix

Everything that will be checked after this work, organized by when it fires.

### At Boot Time (during `registry.boot()`)

| Check | Today | After |
|-------|-------|-------|
| Interface name declared <-> implemented | Bidirectional | No change |
| `intents:` manifest vs `intents()` return keys | Not checked | Cross-check (warn/strict) |
| `events.subscribes` vs actual `eventBus.subscribe()` calls | Not checked | Cross-check (warn/strict) |
| `api.routes[].handler` exists in `instance.routes()` | Not checked | Cross-check (warn/strict) |
| Schema `indexes:` provisioned in DataLayer | Not checked | `CREATE INDEX IF NOT EXISTS` |
| Schema `required: true` mapped to `NOT NULL` | Ignored | Mapped during `_provisionTable` |

### At Call Time (during `registry.call()`)

| Check | Today | After |
|-------|-------|-------|
| Dependency scope (ScopedCoordinator) | Hard throw | No change |
| Input `required` fields present | Not checked | Validated, warn/strict |
| Input field types match declaration | Not checked | Validated via `typeValidator`, warn/strict |
| Output field presence (declared fields exist) | Names only | No change |
| Output field types match declaration | Not checked | Validated via `typeValidator`, warn/strict |
| Output extra undeclared fields | Not flagged | Warned in strict mode |
| Output `type: array` + `items` validation | Not checked | Each item validated against `items` shape |
| Output `nullable: false` enforcement | Not checked | Null return flagged, warn/strict |

### At Publish Time (during `eventBus.publish()`)

| Check | Today | After |
|-------|-------|-------|
| Publisher declared the event | Only if `publisher:` passed | `publisher:` required for bundles with declared events |
| Payload missing declared fields | Checked | No change |
| Payload extra undeclared fields | Checked | No change |
| Payload field types match schema | Not checked | Validated via `typeValidator`, warn/strict |

### Violation Routing

All new checks flow through existing `_contractViolation()` / `_eventContractViolation()` methods, respecting mount plan `validation.contracts` and `validation.events` settings (`warn` logs, `strict` throws).

## Section 4: @torquedev/schema Package Design

| | |
|---|---|
| **Package name** | `@torquedev/schema` |
| **Repo** | `torque-schema` (new, standalone) |
| **Dependencies** | Zero. Pure JS, ESM-only, `node --test` |

### The `createTypeValidator()` Factory

```js
const validate = createTypeValidator();

// Kernel injection contract: (declaredType, actualValue, fieldName) => string | null
validate('uuid', '550e8400-...', 'user_id');    // => null (valid)
validate('uuid', 42, 'user_id');                 // => "field 'user_id': expected uuid, got number"
validate('string[]', ['a', 'b'], 'tags');        // => null
validate('string[]', ['a', 42], 'tags');         // => "field 'tags[1]': expected string, got number"

// Custom types
validate.registerType('phone', (v) => typeof v === 'string' && /^\+?[1-9]\d{1,14}$/.test(v));
validate('phone', '+15551234567', 'mobile');     // => null
```

### `validateRequired` for Input Contract Checking

```js
// inputContract from manifest: { userId: { type: 'uuid', required: true }, name: { type: 'string' } }
validateRequired({ name: 'Alice' }, inputContract);
// => "required field 'userId' is missing"
```

Required checking is separate from type checking because `required` is about presence, not type. The registry calls `validateRequired` first, then `typeValidator` on each present field.

## Section 5: Boot-Time Fixes

These are the remaining gaps that don't involve the `typeValidator` injection but should ship alongside it to close the full validation matrix.

### DataLayer `_provisionTable()` Fixes (`torque-service-datalayer`)

1. **Index provisioning** -- read `schema.tables[t].indexes` from manifest and run `CREATE INDEX IF NOT EXISTS` for each. Today 4 indexes are declared by `tasks` and zero are created.

2. **`required: true` -> `NOT NULL`** -- during column creation, treat `required: true` in the manifest the same as `null: false`. Currently `required: true` is silently ignored at the DDL level.

### Registry Boot-Time Cross-Checks (`torque-core/kernel/registry.js`)

3. **`intents:` manifest vs `intents()` return** -- at boot, compare the `intents:` list in manifest.yml against the keys returned by `instance.intents()`. Bidirectional, same as the existing interface name check. Catches "manifest says OrganizeWork but code doesn't return it."

4. **`api.routes[].handler` existence** -- at boot, for each declared route, verify that `instance.routes()[handlerName]` exists. Today a missing handler is a runtime crash on first request instead of a boot-time error.

5. **`events.subscribes` cross-check** -- at boot, after `setupSubscriptions()` runs, verify that each event declared in `events.subscribes` has a corresponding subscription registered on the EventBus. Warn if a bundle declares it subscribes to an event but never actually called `eventBus.subscribe()` for it.

### EventBus `publisher:` Enforcement (`torque-service-eventbus`)

6. **Make `publisher:` required for bundles with declared events** -- if a bundle registered declared events via `registerDeclaredEvents()` but then calls `publish()` without the `publisher:` option, warn (or throw in strict mode). This closes the hole where omitting `publisher:` silently skips the authorship check.

## Repos Touched

| Repo | Changes |
|------|---------|
| `torque-schema` (NEW) | New package: type validators, factory, required checking |
| `torque-core` | Registry: `typeValidator` injection, input validation, output type checking, boot cross-checks |
| `torque-service-eventbus` | `typeValidator` injection, payload type checking, publisher enforcement |
| `torque-service-datalayer` | Index provisioning, `required`->`NOT NULL` mapping |
| `torque` (boot.js in reference apps) | Wire `@torquedev/schema` into boot |

## Testing Strategy

- **`torque-schema`**: Unit tests for every built-in type (pass/fail cases), factory behavior, custom type registration, array type validation, and edge cases. Uses `node --test`.
- **`torque-core`**: Unit tests for each new validation point in `registry.call()` (input required, input types, output types, output extra fields). Tests for each boot-time cross-check. Tests confirm that omitting `typeValidator` skips all new validation.
- **`torque-service-eventbus`**: Tests for payload type validation during publish, and `publisher:` enforcement.
- **`torque-service-datalayer`**: Tests for index provisioning DDL and `required: true` -> `NOT NULL` mapping.
- **Integration**: End-to-end boot of reference app with `@torquedev/schema` wired in, verifying that contract violations in warn mode log and in strict mode throw.

## Open Questions

1. Should the CLI's `torque validate` command also run type validation against seed data or test fixtures?
2. Should custom type definitions be declarable in manifest.yml (e.g., `types: { phone: regex:...}`) or only in code?
3. Should there be a `torque check-contracts` CLI command that validates all manifests against the schema package without booting?