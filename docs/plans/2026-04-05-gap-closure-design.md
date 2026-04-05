# Torque Framework Gap Closure Design

## Goal

Close 15 identified gaps between Torque and mature frameworks (.NET, Rails), transforming Torque from a well-architected but incomplete framework into a production-ready developer platform.

## Background

A comparative analysis of Torque against .NET (25+ years, enterprise platform) and Ruby on Rails 8 (20+ years, omakase framework) revealed 10 gaps in developer experience and framework completeness. An independent deep research audit confirmed those and identified 6 additional gaps in AI runtime, embeddings, observability, security, hot reload, and documentation alignment. The documentation alignment gap was dissolved into a cross-cutting concern — every gap's definition of done includes updating the relevant docs.

The gaps span the full developer journey: first 30 minutes (templates, validation, deployment), first week (migrations, types, OpenAPI, queries, middleware), framework differentiators (real-time, AI runtime, embeddings, observability, security), and production confidence (hot reload, test harness, npm publishing).

## Approach

The 15 gaps are organized into 4 phases ordered by developer journey — what they hit first, what they need once building seriously, what makes them choose Torque, and what makes them stay. Each phase's gaps are largely independent and can be parallelized within the phase.

Five architectural decisions constrain all implementation:

1. **Anthropic-first, pluggable later.** The agent runtime uses `ClaudeRuntime` as the default LLM backend. The abstraction (`this.runtime.execute(intent, context, tools)`) emerges from concrete usage, not speculation. The interface will be extracted after the first implementation is stable. Building a provider-agnostic abstraction before having a working runtime would be premature — .NET's `IChatClient` took years to stabilize and they had the benefit of seeing what Semantic Kernel needed first.

2. **Keep systems separate.** No Model class. The event system IS the callback layer. Query builder extends `data.query()`. Embeddings are an extension listening to events. Real-time is manifest-driven. Each works independently. Bundle isolation is Torque's defining constraint — implicit behaviors like `afterCreate()` callbacks would undermine manifest-declared contracts.

3. **Behaviors for config, extensions for implementation.** Heavy logic (OTel spans, rate limiting, RBAC) lives in `@torquedev/ext-*` packages. Behavior YAMLs wire those extensions to hook positions. Mount plans opt in with one line: `behaviors: [observability]`. A behavior YAML says _what_ to wire _where_; the extension package has the _how_.

4. **Single VPS with Docker, no registry by default.** `torque deploy` uses `docker save | ssh docker load` for zero-infrastructure deployment. Registry push/pull is opt-in when `registry:` is present in `config/deploy.yml`. Three commands, no registry credentials, no extra infrastructure.

5. **Documentation is not a standalone gap.** Every gap's definition of done includes updating READMEs, REGISTRY.md, Bundle Authoring Guide, and removing "planned" claims that are now implemented.

## Architecture

The 15 gaps map onto the existing Torque architecture without introducing new architectural layers:

```
┌─────────────────────────────────────────────────────────┐
│                      Mount Plan                         │
│  behaviors: [development, observability, security]      │
│  middleware: { compression, rate_limit, request_id }    │
│  embeddings: { provider: local, store: sqlite }         │
│  realtime: (delegated to bundle manifests)              │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│                       Kernel                            │
│  Registry · HookBus · Coordinator · AgentRouter         │
│  WebSocketHub (declarative real-time)                   │
│  Hot Reload Watcher (dev only)                          │
└──┬───────────┬───────────┬──────────────────────────────┘
   │           │           │
┌──▼──┐   ┌───▼───┐   ┌───▼────────────────────┐
│ CLI │   │Server │   │    Extensions           │
│     │   │       │   │ ext-otel                │
│ new │   │OpenAPI│   │ ext-security            │
│ dev │   │ /docs │   │ ext-embeddings          │
│deploy│  │       │   │ ext-authorization       │
│migrate│ │middle-│   │ ext-soft-delete         │
│     │   │ ware  │   │ ext-async-events        │
└─────┘   └───────┘   │ ext-search             │
                       │ ext-storage            │
                       └────────────────────────┘
```

Extensions plug into the HookBus at declared positions. Behaviors wire extensions to positions. The mount plan declares which behaviors are active. No new architectural concepts are introduced.

## Components

### Phase 1 — "First 30 Minutes"

#### Gap 10: CLI Templates

**Problem.** Only 1 template exists (kanban, 8 bundles). No stepping stones for new developers.

**Solution.** Three new templates in `torque-cli/templates/`:

| Template | Bundles | Use case |
|----------|---------|----------|
| `minimal` | Identity only | Learn one bundle at a time |
| `standard` | Identity + pipeline + pulse + tasks | Real deal-tracking app with business logic |
| `api-only` | Identity + pipeline + tasks, no shell-react | Headless API server for custom frontend/mobile |

Each template includes: `template.json` (bundle list + config), `config/mount_plans/development.yml`, `seeds/`, generated `Dockerfile`, `.env.example`.

`torque new my-app` without `--template` prompts: "Which template? minimal / standard / kanban / api-only". Default: `standard`.

**Definition of done.** All templates work end-to-end (`torque new` → `npm install` → `torque seed` → `torque start`). README updated. REGISTRY.md updated.

---

#### Gap 2: Model Validation Adoption

**Problem.** The server infrastructure supports manifest `validate:` blocks, but bundles don't use them. 241 inline `if (!x) return {error}` patterns scattered across `logic.js` files.

**Solution.** Three changes:

1. **Audit all 17 bundle manifests** and add `validate:` blocks to every POST/PATCH route with required fields, types, and enum constraints matching what `logic.js` currently validates manually.

2. **Remove redundant inline validation** from route handlers where the manifest now covers it. Keep genuinely business-logic validation (e.g., "end date must be after start date").

3. **Add `validate` option to `data.insert()`** — `this.data.insert('tasks', record, { validate: true })` checks the manifest schema before writing. This catches bugs in seeds, migrations, and coordinator calls that bypass the HTTP route layer.

**Definition of done.** All bundle routes have `validate:` blocks, inline validation reduced by ~60%, `data.insert()` supports validate option, Bundle Authoring Guide updated with validation examples.

---

#### Gap 9: Deployment

**Problem.** Zero deployment support anywhere in the framework. The pitch is "SQLite, one process, no infrastructure" but the story breaks at the finish line.

**Solution.** Three artifacts:

**Generated Dockerfile** (via `torque new`):

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
# SQLite data lives here — this MUST be a mounted volume in production
# docker run -v torque-data:/app/data ...
VOLUME /app/data
EXPOSE 9292
CMD ["node", "boot.js"]
```

**Generated `config/deploy.yml`** (via `torque new`):

```yaml
server: 0.0.0.0      # replace with your VPS IP
user: deploy
port: 9292
# Uncomment to use registry push/pull instead of save/load:
# registry: ghcr.io/your-org
env:
  AUTH_SECRET: ${AUTH_SECRET}
  NODE_ENV: production
```

**`torque deploy` CLI command** (~50-80 lines):

1. Reads `config/deploy.yml`
2. Builds: `docker build -t <app-name> .`
3. When no `registry:` configured (default): `docker save <app-name> | ssh <user>@<server> docker load`
4. When `registry:` configured: `docker push` then `ssh ... docker pull`
5. Deploys: `ssh <user>@<server> "docker stop <app-name>; docker run -d --name <app-name> --restart unless-stopped -v torque-data:/app/data -p <port>:9292 --env-file .env <app-name>"`

Also generates `.env.example` with all config vars.

The default path (save/load) requires zero infrastructure beyond the VPS itself — no registry, no credentials, no extra services. The registry path is opt-in for teams that already have one.

**Definition of done.** `torque new` → `torque deploy` works end-to-end to a VPS with Docker installed. README documents the deploy flow.

---

### Phase 2 — "First Week"

#### Gap 1: Migration System

**Problem.** `torque migrate` exists (~70% done) with `generate`, `run`, and `status` subcommands. But rollback is a stub, column type changes aren't detected, and there's no dry-run mode.

**Solution — finish what's started:**

- **Finish `rollback`** — apply the migration's `down()` export, update `_torque_migrations` table. Single migration rollback only (no rollback-to-version).

- **Column type changes** — add detection for type mismatches between manifest and snapshot. Since SQLite doesn't support `ALTER COLUMN`, generate the standard pattern: create temp table → copy data → drop original → rename. Emit as a helper: `migrateColumnType('tasks', 'priority', 'integer')`.

- **Data migration helpers** — `seed(table, records)` helper available inside migration `up()` functions for backfilling data during schema changes.

- **`torque migrate preview`** — dry-run mode that prints the SQL without executing. Critical before running against production.

**Definition of done.** `torque migrate generate` detects type changes, `torque migrate rollback` works, `torque migrate preview` prints SQL, tests pass.

---

#### Gap 7: TypeScript Declarations

**Problem.** Zero `.d.ts` files exist anywhere. TypeScript users (the majority of the JS ecosystem) get no autocomplete, no type checking.

**Solution.** Hand-written `.d.ts` files for the 5 packages bundle authors interact with:

| Package | Key types to declare |
|---------|---------------------|
| `@torquedev/core` | `boot()` options and return type, `Registry`, `HookBus`, `ScopedCoordinator` |
| `@torquedev/datalayer` | `BundleScopedData` — all methods: `insert`, `find`, `query`, `update`, `delete`, `count`, `transaction`, `findWithRelations`, `queryWithRelations` |
| `@torquedev/eventbus` | `EventBus` — `publish`, `subscribe`, `onAny` |
| `@torquedev/schema` | `createTypeValidator`, `validateRequired`, type names |
| `@torquedev/server` | `createServer` options, route handler context (`ctx.params`, `ctx.body`, `ctx.query`, `ctx.currentUser`) |

Each package gets `index.d.ts` + `"types": "index.d.ts"` in `package.json`. Public API surface only — no internal types.

**Definition of done.** TypeScript users get full autocomplete for the bundle authoring API. Types validated against actual implementation.

---

#### Gap 6: OpenAPI Generation

**Problem.** `/api/introspect` already has all the metadata. `/openapi.json` is claimed in docs but doesn't exist.

**Solution.**

- New file: `torque-service-server/openapi.js` — `generateOpenAPISpec(manifests)` maps: routes → paths, `validate.body` → request body JSON Schema, `interfaces.contracts.output` → response schemas, `auth: true` → Bearer security scheme.

- Mount `GET /openapi.json` — returns the generated spec.

- Mount `GET /api/docs` — serves `swagger-ui-dist` (the standard Swagger UI static bundle).

**Definition of done.** `/openapi.json` returns valid OpenAPI 3.1 spec, `/api/docs` renders Swagger UI, all routes are documented.

---

#### Gap 4: Query Builder

**Problem.** `data.query()` only supports equality filters. No operators, no aggregation, no raw SQL escape hatch.

**Solution.** Extend `BundleScopedData.query()` with operator-based filters:

```js
this.data.query('tasks', {
  status: { $in: ['open', 'in_progress'] },
  priority: { $ne: 'low' },
  due_date: { $lt: '2026-04-01' },
  title: { $like: '%urgent%' }
})
```

Supported operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$like`, `$isNull`, `$notNull`. All generate parameterized SQL.

New methods:

- `aggregate(table, { groupBy, count, sum, avg, min, max })` — returns computed results.

- `raw(sql, params)` — escape hatch for complex queries. Runs against the bundle's scoped database connection. SQLite enforces table access at the schema level since each bundle's tables are prefixed — no SQL parser needed. If someone writes `raw('SELECT * FROM other_bundle_tasks')`, it fails because that table doesn't exist in the bundle's scope.

Column validation remains enforced on structured queries. `raw()` relies on SQLite's inherent scoping.

**Definition of done.** Operators work with parameterized SQL, `aggregate()` works, `raw()` works, TypeScript declarations updated.

---

#### Gap 3: Middleware Pipeline

**Problem.** Express pipeline exists but isn't configurable from mount plans.

**Solution.** New `middleware:` section in mount plan:

```yaml
middleware:
  compression: true
  request_logging: true
  request_id: true        # defaults to ON — zero-cost, critical for debugging
  rate_limit:
    window_ms: 60000
    max_requests: 100
```

Server reads this at boot and inserts middleware in order. Uses standard Express packages (`compression`, `express-rate-limit`).

`request_id` defaults to ON — every production request should be traceable. Developers opt _out_, not in.

`behaviors/development.yaml` updated to include `request_logging: true` by default (structured logging in dev mode).

Also adds `route:beforeResponse` hook position to HookBus for extensions that need to modify responses.

**Definition of done.** Mount plan middleware works, request IDs default on, structured logging in development, rate limiting configurable.

---

### Phase 3 — "Framework Differentiators"

#### Gap 5: Declarative Real-time

**Problem.** Hardcoded realtime bundle and duplicate WebSocket systems (kernel hub + bundle hub).

**Solution.** Replace the realtime bundle with a manifest-driven system. New `realtime:` section in bundle manifests:

```yaml
realtime:
  channels:
    - name: "board:{board_id}"
      events: ["kanban.card.*", "kanban.list.*"]
      auth: isMember    # interface name — called to verify access
    - name: "workspace:{workspace_id}"
      events: ["workspace.member.*"]
```

At boot, the kernel reads `realtime:` declarations from all bundles, subscribes the existing `WebSocketHub` to matching events, and enforces channel auth by calling the named interface via the coordinator when a client subscribes.

When a client subscribes to `board:abc`, the hub calls `coordinator.call('kanban', 'isMember', { board_id: 'abc', user_id })` and rejects if it returns false.

The current realtime bundle is deleted — its behavior is now configuration. The `WebSocketHub` becomes the sole WebSocket system (removing the duplicate).

For bundle authors: zero real-time code. Declare channels in the manifest, emit events as usual, the kernel handles broadcast. This is Torque's equivalent to Rails' `broadcasts_to` — but manifest-driven, not model-driven.

**Definition of done.** Manifest `realtime:` works end-to-end, channel auth enforced, old realtime bundle deleted, kanban-app template uses the new system, WebSocket docs updated.

---

#### Gap 11: Agent Runtime

**Problem.** `AgentRouter` is a placeholder — emits lifecycle events but has no LLM execution loop, no tool calling, no success criteria evaluation.

**Solution.** Implement a real execution loop in `torque-core/idd/AgentRouter.js`. Anthropic-first, pluggable later.

**Components:**

**1. `ClaudeRuntime`** (new: `torque-core/idd/claude-runtime.js`)

Wraps `@anthropic-ai/claude-agent-sdk`. Implements:

```
execute(intent, context, tools) → { result, trace }
```

- Builds system prompt from Intent + Context + Behavior declarations
- Generates tool schemas from declared interfaces
- Executes tool calls via the coordinator
- Evaluates success criteria from Intent metadata
- Returns structured result with execution trace

**2. `AgentRouter.execute(intent, input)`** (replace the placeholder)

Orchestration loop:
1. Resolve intent metadata from registry
2. Build bounded context from Context declaration — query relevant data via `data.query()` + vector search when embeddings extension is available
3. Call `this.runtime.execute()` with intent + context + tool schemas
4. Handle human confirmation gates via HookBus → WebSocketHub → wait for approval
5. Emit lifecycle events: `idd:intent_received`, `idd:executing`, `idd:tool_invoked`, `idd:resolved` / `idd:failed`
6. Return result

**3. Human confirmation flow**

When a Behavior declares `confirm: true` on a tool, the AgentRouter pauses execution. It emits `idd:confirmation_required` via HookBus. The WebSocketHub pushes the confirmation request to the client. The client approves or denies. The Promise resolves and execution continues or aborts. Single-process, no external queue.

**4. Intent endpoints**

`POST /api/intents/{bundle}/{intent}` auto-mounted for every registered intent. Example: `POST /api/intents/tasks/TriageTasks`.

`@anthropic-ai/claude-agent-sdk` remains an optional peer dependency. If not installed, clear error message. Kernel boots fine without it — the agent runtime is not required for framework operation.

**Definition of done.** `POST /api/intents/tasks/TriageTasks` triggers real LLM inference, tool calling via coordinator, success criteria evaluation. Human confirmation gates work via WebSocket.

---

#### Gap 12: Embeddings / VORM

**Problem.** `vectorize` fields in Context declarations are metadata-only. No actual embedding generation or vector search.

**Solution.** New extension `@torquedev/ext-embeddings` with configurable provider and store from day one:

```yaml
# mount plan
embeddings:
  provider: local      # default: Anthropic embeddings via claude-agent-sdk
  # provider: openai   # future: OpenAI embeddings API
  store: sqlite        # default: cosine similarity in _torque_embeddings table
  # store: sqlite-vss  # future: native vector extension
```

The `embeddingService.search()` interface stays the same regardless of backend. Making provider and store configurable from day one avoids painting into a corner when pure-JS cosine similarity hits its performance ceiling (a few thousand records).

**How it works:**

1. **Context declarations drive indexing.** When a Context declares `vectorize: ['title', 'description']`, the extension subscribes to that bundle's `*.created` and `*.updated` events and generates embeddings for those fields.

2. **Storage.** `_torque_embeddings` table with columns: `bundle`, `table_name`, `entity_id`, `field`, `vector` (BLOB), `updated_at`. Default implementation: pure-JS cosine similarity.

3. **Search API.** `embeddingService.search(bundle, query, { limit, threshold })`. Exposed as `GET /api/embeddings/search?q=...&bundle=tasks&limit=10` and as a coordinator interface for AgentRouter context retrieval.

4. **Behavior wiring.** `behaviors/ai-assisted.yaml` updated to wire the extension.

**Definition of done.** Events trigger embedding generation, vector search works via API and coordinator, AgentRouter uses embeddings for context retrieval.

---

#### Gap 13: Observability

**Problem.** HookBus emits events but there are no OTel spans, metrics, or structured logs.

**Solution.** New extension `@torquedev/ext-otel` + behavior `behaviors/observability.yaml`.

Extension exports hook handlers:

| Handler | Hook position | What it does |
|---------|--------------|--------------|
| `spanOnInterfaceCall` | `interface:before-call` / `after-call` | OTel spans with bundle name, interface, duration, success/failure |
| `spanOnEventPublish` | `event:publish` | Traces event publishing with publisher, event name, subscriber count |
| `structuredAccessLog` | `route:after` | JSON request logs with method, path, status, duration, request ID, user ID |
| `requestTracing` | `route:before` | `X-Request-Id` and `X-Trace-Id` headers, trace context propagation |

`@opentelemetry/sdk-node` and `@opentelemetry/api` as peer dependencies.

Behavior YAML wires handlers to hook positions. Mount plan: `behaviors: [observability]` — one line opt-in.

**Definition of done.** OTel spans emitted for interface calls, structured access logs in JSON, traces correlated by request ID.

---

#### Gap 14: Security Hardening

**Problem.** RBAC/authz patterns exist across bundles but aren't standardized as reusable behavior packs.

**Solution.** New extension `@torquedev/ext-security` + behavior `behaviors/security-hardened.yaml`.

Extension exports:

| Handler | What it does |
|---------|--------------|
| `rbacGate` | `route:before` gate checking user role against manifest-declared `auth.roles`. Uses IAM bundle's `hasRole` interface via coordinator. |
| `rateLimiter` | Per-route rate limiting with in-memory counters (no Redis dependency). |
| `csrfEnforcement` | CSRF token validation for mutating routes (extracted from existing server.js production code). |
| `auditLog` | Security events logged to `_torque_audit_log` table. |

Mount plan: `behaviors: [security-hardened]` — one line opt-in.

**Definition of done.** RBAC gates enforce manifest role requirements, rate limiting works, audit log captures security events.

---

### Phase 4 — "Production Confidence"

#### Gap 15: Hot Reload

**Problem.** No dev-time bundle reload without full process restart. Changing one line in a bundle's `logic.js` requires restarting the entire application.

**Solution.** Extend `torque dev` with bundle-level hot reload:

- **File watcher** (`node:fs.watch`) monitors bundle directories for changes to `logic.js`, `manifest.yml`, and `ui/` files.

- **On change:** the registry unloads the affected bundle (tears down its routes, interfaces, subscriptions), re-imports the module using ESM cache-busting (`import('./logic.js?t=' + Date.now())`), and re-registers it through the normal boot path.

- **Other bundles are untouched** — their routes, subscriptions, and in-memory state remain live.

- **WebSocket notification** — clients receive a `__torque_reload` message so the shell can refresh the affected UI routes.

- **Documented limitations:** in-memory state in the reloaded bundle is lost. Database state persists. Event subscriptions are re-wired. If the manifest schema changes (new columns), a full restart is needed to run provisioning.

- **Dev-only** — the watcher is not started when `NODE_ENV=production`. This is purely a developer experience feature.

**Definition of done.** Changing a bundle's `logic.js` during `torque dev` reflects immediately without restart. No memory leaks on repeated reloads. Limitations clearly documented.

---

#### Gap 8: Integration Test Harness

**Problem.** One app-specific integration test exists (`torque-app-todo/test/integration.test.js`) but the boot-in-memory pattern isn't reusable.

**Solution.** New export in `@torquedev/test-helpers`:

```js
import { createTestApp } from '@torquedev/test-helpers';

const app = await createTestApp({
  bundles: {
    identity: { source: '../torque-bundle-identity', config: { jwt_secret: 'test' } },
    tasks: { source: '../torque-bundle-tasks' }
  }
});

const res = await app.fetch('/api/tasks');
assert.equal(res.status, 200);

const events = app.eventBus.published;
await app.close();
```

Internally: boots the kernel with `db: ':memory:'`, `port: 0`, `silent: true`. Returns `fetch` pre-pointed at the server address. Exposes `coordinator` and `eventBus` for assertions. Tears down cleanly on `close()`.

**Definition of done.** `createTestApp` works, documented in Bundle Authoring Guide, example test added to `torque-app-todo`.

---

#### npm Publishing

Publish all remaining unpublished packages plus new Phase 3 extensions:

- `@torquedev/ui-kit`
- `@torquedev/ext-authorization`
- `@torquedev/ext-soft-delete`
- `@torquedev/ext-async-events`
- `@torquedev/ext-search`
- `@torquedev/ext-storage`
- `@torquedev/test-helpers`
- `@torquedev/ext-embeddings` (new in Phase 3)
- `@torquedev/ext-otel` (new in Phase 3)
- `@torquedev/ext-security` (new in Phase 3)

**Definition of done.** All `@torquedev/*` packages installable via `npm install`.

## Data Flow

### Standard Request Flow (after all gaps closed)

```
Client Request
    │
    ▼
Middleware Pipeline (Gap 3)
  request_id → compression → rate_limit → request_logging
    │
    ▼
Route Handler
  manifest validate: (Gap 2) → logic.js handler
    │
    ▼
BundleScopedData (Gap 4)
  query with operators / aggregate / raw
    │
    ▼
EventBus emit
    │
    ├──▶ ext-embeddings subscriber (Gap 12) → generate/update embeddings
    ├──▶ ext-otel subscriber (Gap 13) → emit OTel span
    ├──▶ ext-security subscriber (Gap 14) → write audit log
    └──▶ WebSocketHub (Gap 5) → broadcast to subscribed channels
```

### Agent Intent Flow (after Gap 11)

```
POST /api/intents/tasks/TriageTasks
    │
    ▼
AgentRouter.execute(intent, input)
    │
    ├── 1. Resolve intent metadata from registry
    ├── 2. Build bounded context (data.query + embeddingService.search)
    ├── 3. ClaudeRuntime.execute(intent, context, tools)
    │       │
    │       ├── LLM decides to call a tool
    │       ├── AgentRouter checks confirm: true on Behavior
    │       ├── If confirmation needed:
    │       │     emit idd:confirmation_required → WebSocketHub → client
    │       │     await approval/denial via EventBus
    │       ├── Execute tool via coordinator.call(bundle, interface, args)
    │       └── Loop until success criteria met or max iterations
    │
    ├── 4. Emit idd:resolved or idd:failed
    └── 5. Return result + execution trace
```

### Deployment Flow (after Gap 9)

```
Developer workstation                    VPS
─────────────────────                    ───
torque deploy
  │
  ├── docker build -t myapp .
  ├── docker save myapp ──────────────▶ docker load
  └── ssh deploy@server ──────────────▶ docker stop myapp
                                        docker run -d
                                          --name myapp
                                          --restart unless-stopped
                                          -v torque-data:/app/data
                                          -p 9292:9292
                                          --env-file .env
                                          myapp
```

## Error Handling

Each gap handles errors according to the system it extends:

- **Validation (Gap 2).** Manifest `validate:` blocks return structured `{ error, details }` with field-level messages. `data.insert({ validate: true })` throws on schema violation — caught by the route handler.

- **Migrations (Gap 1).** Failed migrations leave the database in its pre-migration state (SQLite transactions). `_torque_migrations` table only updated on success. `rollback` wraps `down()` in a transaction.

- **Query Builder (Gap 4).** Invalid operators return clear errors. Invalid column names rejected before SQL generation. `raw()` errors bubble as-is from SQLite.

- **Agent Runtime (Gap 11).** `ClaudeRuntime` catches LLM API errors and emits `idd:failed` with error details. Max iteration limit prevents runaway loops. Tool execution errors are returned to the LLM as error results (not thrown), allowing the agent to recover or try a different approach. Confirmation timeouts (configurable) result in denial.

- **Deployment (Gap 9).** Each step's exit code is checked. SSH failures surface immediately. Docker build errors shown verbatim. If the old container fails to stop, the new one is not started (fail-safe).

- **Hot Reload (Gap 15).** If the reloaded bundle fails to register (syntax error, missing export), the old version stays loaded and an error is logged to the console. The watcher continues monitoring for the next save.

## Testing Strategy

Every gap produces tests appropriate to its scope:

| Gap | Test type | Location |
|-----|-----------|----------|
| Gap 10: CLI Templates | `torque new` E2E (generate → install → seed → start) | `torque-cli/test/` |
| Gap 2: Validation | Unit tests for `validate:` middleware + `data.insert({ validate: true })` | Per-bundle `test/` |
| Gap 9: Deployment | Unit test for `deploy.yml` parsing + Dockerfile lint | `torque-cli/test/` |
| Gap 1: Migrations | Rollback, type change detection, preview output | `torque-cli/test/` |
| Gap 7: TypeScript | Compile-time checks with `tsc --noEmit` against declarations | Per-package CI step |
| Gap 6: OpenAPI | Spec validates against OpenAPI 3.1 JSON Schema | `torque-service-server/test/` |
| Gap 4: Query Builder | Operator SQL generation, aggregation, raw() scoping | `torque-service-datalayer/test/` |
| Gap 3: Middleware | Request ID presence, compression headers, rate limit 429s | `torque-service-server/test/` |
| Gap 5: Real-time | Channel subscription, auth rejection, event broadcast | `torque-core/test/` |
| Gap 11: Agent Runtime | Intent resolution, tool calling, confirmation flow (mocked LLM) | `torque-core/test/` |
| Gap 12: Embeddings | Event-driven indexing, vector search results | `torque-ext-embeddings/test/` |
| Gap 13: Observability | Span emission, structured log format, request ID correlation | `torque-ext-otel/test/` |
| Gap 14: Security | RBAC gate enforcement, rate limit counters, audit log entries | `torque-ext-security/test/` |
| Gap 15: Hot Reload | Bundle reload without restart, state preservation, memory leak check | `torque-core/test/` |
| Gap 8: Test Harness | `createTestApp` boots, serves requests, tears down cleanly | `torque-test-helpers/test/` |

Integration tests (using `createTestApp` from Gap 8) are added once Gap 8 lands. Earlier phases use the existing per-repo test patterns.

## Phase Dependencies

```
Phase 1 (independent — all can run in parallel)
├── Gap 10: CLI Templates
├── Gap 2: Validation Adoption
└── Gap 9: Deployment

Phase 2 (independent — all can run in parallel)
├── Gap 1: Migrations
├── Gap 7: TypeScript Declarations
├── Gap 6: OpenAPI Generation
├── Gap 4: Query Builder
└── Gap 3: Middleware Pipeline

Phase 3 (some dependencies)
├── Gap 5: Declarative Real-time     (independent)
├── Gap 11: Agent Runtime            (independent — uses current data API)
├── Gap 12: Embeddings/VORM          (depends on Gap 11 for AgentRouter integration)
├── Gap 13: Observability            (independent)
└── Gap 14: Security Hardening       (independent)

Phase 4 (depends on earlier phases being usable)
├── Gap 15: Hot Reload               (independent)
├── Gap 8: Integration Test Harness  (independent)
└── npm Publishing                   (after all extensions exist)
```

Gap 11 (Agent Runtime) does NOT depend on Gap 4 (Query Builder). It builds against the current `data.query()` API. When the query builder lands later, the agent's context retrieval improves automatically — but it is not gated.

## Open Questions

None. All architectural decisions were resolved during brainstorming.
