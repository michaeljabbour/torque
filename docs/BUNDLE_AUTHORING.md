# Bundle Authoring Guide

## Overview

A **bundle** is a self-contained feature module in Torque. It owns its schema, business logic, API routes, events, and UI -- all in one directory. Bundles never import each other's code. They communicate through events (pub/sub) and the coordinator (cross-bundle RPC), both enforced by the kernel at runtime.

Every bundle has three required files:

```
my-bundle/
  manifest.yml    # Declarative contract: schema, events, interfaces, routes
  logic.js        # Implementation: a single class with all behavior
  package.json    # ESM package metadata
```

Optional files:

```
  ui/             # Frontend views (ui-kit descriptors)
  intents/        # AI intent definitions (Context + Behavior + Intent)
  agent.md        # AI agent description for the bundle's domain
  test/           # Tests (node:test)
  seeds/          # Seed data scripts
  migrations/     # Database migrations
```

The manifest declares what the bundle needs and provides. The kernel reads it at boot to create tables, register events, wire interfaces, and mount routes. The logic class implements everything the manifest promises.

---

## Quick Start with the CLI

One command generates a complete working bundle:

```bash
torque generate scaffold notes title:text body:text status:text
```

This creates `bundles/notes/` with:

| File | Contents |
|------|----------|
| `manifest.yml` | Schema, CRUD events with payloads, interface contracts, REST routes, UI routes |
| `logic.js` | Full CRUD class with validation, event publishing, routes, interfaces |
| `agent.md` | AI agent definition with domain docs |
| `test/notes.test.js` | Complete test suite for routes, interfaces, and events |
| `ui/` | ListView, DetailView, ui-kit descriptors |
| `seeds/notes.js` | Seed data script |

It also patches your `development.yml` mount plan to include the new bundle.

For an empty skeleton instead:

```bash
torque generate bundle notes
```

This gives you stub files to fill in yourself.

Add fields with types: `title:text`, `amount:integer`, `due_date:timestamp`, `owner_id:uuid`. Use `--belongs-to workspace` for nested routes under a parent bundle.

---

## manifest.yml Reference

The manifest is the single source of truth for your bundle's contract. Here's the complete tasks bundle manifest as a reference:

```yaml
name: tasks
version: "1.0.0"
description: "Task management — create, assign, and track tasks linked to deals or other entities"

schema:
  tables:
    tasks:
      columns:
        id: { type: uuid, primary: true }
        title: { type: string, null: false }
        description: { type: text }
        status: { type: string, default: "open" }
        priority: { type: string, default: "normal" }
        due_date: { type: timestamp }
        entity_type: { type: string }
        entity_id: { type: uuid }
        assigned_to: { type: uuid }
        created_by: { type: uuid }
        completed_at: { type: timestamp }
        created_at: { type: timestamp }
        updated_at: { type: timestamp }
      indexes:
        - { columns: [entity_type, entity_id] }
        - { columns: [assigned_to] }
        - { columns: [status] }
        - { columns: [due_date] }

events:
  publishes:
    - name: tasks.task.created
      schema: { task_id: uuid, title: string, entity_type: string, entity_id: uuid, assigned_to: uuid, created_by: uuid }
    - name: tasks.task.completed
      schema: { task_id: uuid, completed_by: uuid }
  subscribes:
    - pipeline.deal.stage_changed

interfaces:
  queries:
    - getTask
    - listTasksForEntity
  contracts:
    getTask:
      description: "Retrieve a task by ID"
      input: { taskId: { type: uuid, required: true } }
      output:
        type: object
        nullable: true
        shape: { id: uuid, title: string, description: text, status: string, priority: string, due_date: timestamp, entity_type: string, entity_id: uuid, assigned_to: uuid, created_by: uuid, completed_at: timestamp, created_at: timestamp }
    listTasksForEntity:
      description: "List tasks linked to a specific entity"
      input:
        entityType: { type: string, required: true }
        entityId: { type: uuid, required: true }
      output:
        type: array
        items: { id: uuid, title: string, status: string, priority: string, due_date: timestamp, assigned_to: uuid, created_at: timestamp }

api:
  routes:
    - method: GET
      path: /api/tasks
      handler: listTasks
      auth: true
    - method: GET
      path: /api/tasks/entity/:entityType/:entityId
      handler: listTasksForEntity
      auth: true
    - method: POST
      path: /api/tasks
      handler: createTask
      auth: true
    - method: PATCH
      path: /api/tasks/:id
      handler: updateTask
      auth: true
    - method: PATCH
      path: /api/tasks/:id/complete
      handler: completeTask
      auth: true
    - method: DELETE
      path: /api/tasks/:id
      handler: deleteTask
      auth: true

ui:
  script: ui/index.js
  routes:
    - { path: /tasks, component: task-list }
  navigation:
    - { label: "Tasks", icon: "check-square", path: /tasks }

depends_on: []
optional_deps:
  - identity
  - pipeline
```

### Section-by-section breakdown

#### `name`, `version`, `description`

```yaml
name: tasks
version: "1.0.0"
description: "Task management — create, assign, and track tasks"
```

The `name` must match the bundle's directory name and its key in the mount plan. Version follows semver. Quote the version string to prevent YAML from parsing `1.0` as a float.

#### `schema.tables`

```yaml
schema:
  tables:
    tasks:
      columns:
        id: { type: uuid, primary: true }
        title: { type: string, null: false }
        status: { type: string, default: "open" }
        entity_id: { type: uuid }
        created_at: { type: timestamp }
      indexes:
        - { columns: [entity_type, entity_id] }
        - { columns: [status] }
```

Column types: `uuid`, `string`, `text`, `integer`, `real`, `boolean`, `timestamp`, `json`.

Column options:
- `primary: true` -- marks the primary key (typically `id: uuid`)
- `null: false` -- NOT NULL constraint
- `default: "value"` -- default value

The kernel creates these tables at boot. Each bundle can only access its own tables through the scoped `data` object.

#### `events.publishes`

```yaml
events:
  publishes:
    - name: tasks.task.created
      schema: { task_id: uuid, title: string, assigned_to: uuid, created_by: uuid }
    - name: tasks.task.completed
      schema: { task_id: uuid, completed_by: uuid }
```

Naming convention: `<bundle>.<entity>.<past_tense_verb>`

- Bundle prefix is **mandatory** -- prevents namespace collisions
- Entity is **singular** -- `task`, not `tasks`
- Verb is **past tense** -- events are facts about what happened, not commands
- Payload keys use **snake_case**

The `schema` field declares the payload shape. The kernel validates published events against this schema when running in strict mode.

Good: `tasks.task.created`, `pipeline.deal.stage_changed`, `identity.user.authenticated`
Bad: `tasks.task.create` (command), `tasks.tasks.created` (plural), `notify_pulse` (names subscriber)

#### `events.subscribes`

```yaml
events:
  subscribes:
    - pipeline.deal.stage_changed
```

Lists events from other bundles that this bundle reacts to. The kernel cross-checks that every subscription references an event published by some registered bundle.

#### `interfaces.queries` and `interfaces.contracts`

```yaml
interfaces:
  queries:
    - getTask
    - listTasksForEntity
  contracts:
    getTask:
      description: "Retrieve a task by ID"
      input: { taskId: { type: uuid, required: true } }
      output:
        type: object
        nullable: true
        shape: { id: uuid, title: string, status: string }
```

Interfaces are the bundle's public API for cross-bundle RPC. Other bundles call them via the coordinator:

```js
const task = await this.coordinator.call('tasks', 'getTask', { taskId: '...' });
```

**Bidirectional enforcement:** every query listed here must be implemented in `logic.js`, and every method returned by `interfaces()` must be declared here. The kernel checks both directions at boot.

Contracts declare input/output types. The kernel validates these at runtime when `typeValidator` is enabled. Output `type` can be `object` or `array`. Use `nullable: true` if the interface can return null (e.g., entity not found).

#### `api.routes`

```yaml
api:
  routes:
    - method: POST
      path: /api/tasks
      handler: createTask
      auth: true
```

Each route maps an HTTP method + path to a handler function name. The handler must be returned by the `routes()` method in `logic.js`.

Auth policy convention:
- `auth: true` for all mutations (POST, PATCH, PUT, DELETE)
- `auth: true` for GET routes that return user-specific data
- `auth: false` only for public endpoints (sign-in, sign-up, health checks)

Every route declared here must have a matching handler in `routes()`. The kernel checks this at boot.

#### `ui`

```yaml
ui:
  script: ui/index.js
  routes:
    - { path: /tasks, component: task-list }
  navigation:
    - { label: "Tasks", icon: "check-square", path: /tasks }
```

- `script` -- path to the UI entry point (relative to bundle root)
- `routes` -- SPA routes the shell should register; `component` matches a key in the UI exports
- `navigation` -- entries for the shell's navigation menu

#### `depends_on` and `optional_deps`

```yaml
depends_on: []
optional_deps:
  - identity
  - pipeline
```

`depends_on` -- hard dependencies. The kernel boots these first and the coordinator allows calls to them.

`optional_deps` -- soft dependencies. The coordinator allows calls, but the target bundle may not be active. Your code must handle the missing case gracefully (try/catch).

If you call a bundle not listed in either, the coordinator throws `DependencyViolationError` at runtime.

---

## logic.js Reference

The logic file exports a single default class. The kernel instantiates it with four injected services:

```js
export default class Tasks {
  constructor({ data, events, config, coordinator }) {
    this.data = data;             // Scoped DB access (own tables only)
    this.events = events;         // Pub/sub
    this.config = config;         // Config from the mount plan
    this.coordinator = coordinator; // Cross-bundle RPC (restricted to declared deps)
  }
}
```

### `routes()` -- HTTP handlers

Returns an object mapping handler names to functions. Each handler receives a `ctx` object with `params`, `query`, `body`, and `currentUser`:

```js
routes() {
  return {
    listTasks: (ctx) => {
      const filters = {};
      if (ctx.query.status && ctx.query.status !== 'all') {
        filters.status = ctx.query.status;
      }
      if (ctx.query.assigned_to) filters.assigned_to = ctx.query.assigned_to;
      const tasks = this.data.query('tasks', filters, { order: 'due_date ASC' });
      return { status: 200, data: tasks };
    },

    createTask: (ctx) => {
      const result = this.createTask({
        title: ctx.body.title,
        description: ctx.body.description,
        priority: ctx.body.priority,
        due_date: ctx.body.due_date,
        entity_type: ctx.body.entity_type,
        entity_id: ctx.body.entity_id,
        assigned_to: ctx.body.assigned_to,
        created_by: ctx.currentUser.id,
      });
      return result.error
        ? { status: 422, data: result }
        : { status: 201, data: result };
    },

    deleteTask: (ctx) => {
      this.deleteTask(ctx.params.id);
      return { status: 200, data: { deleted: true } };
    },
  };
}
```

Handlers return `{ status, data }`. The server translates this to an HTTP response. Route handlers are thin -- they extract parameters from `ctx` and delegate to private methods.

### `interfaces()` -- cross-bundle contracts

Returns an object mapping interface names to functions. These are callable by other bundles through the coordinator:

```js
interfaces() {
  return {
    getTask: ({ taskId }) => this.getTask(taskId),
    listTasksForEntity: ({ entityType, entityId }) =>
      this.listTasksForEntity(entityType, entityId),
  };
}
```

Interface methods always receive a single object argument (named parameters). Keep them thin -- delegate to private methods.

### `setupSubscriptions(eventBus)` -- event listeners

Called by the kernel during the subscription phase. Wire all event handlers here -- never in the constructor:

```js
setupSubscriptions(eventBus) {
  eventBus.subscribe('pipeline.deal.stage_changed', 'tasks', async (payload) => {
    const dealTitle = await this._resolveDeal(payload.deal_id);
    const toStage = await this._resolveStage(payload.to_stage_id);
    this.createTask({
      title: `Follow up: ${dealTitle} moved to ${toStage}`,
      description: `Auto-created when deal moved to ${toStage}`,
      priority: 'normal',
      entity_type: 'deal',
      entity_id: payload.deal_id,
      assigned_to: payload.changed_by,
      created_by: payload.changed_by,
    });
  });
}
```

The second argument to `subscribe` is the subscriber name (your bundle name). Always handle errors internally -- a thrown exception stops other handlers from running.

### Private methods -- business logic

Keep business logic in private methods. Routes and interfaces are thin wrappers that call these:

```js
createTask({ title, description, priority, due_date, entity_type, entity_id, assigned_to, created_by }) {
  const normalizedTitle = title?.trim();
  if (!normalizedTitle) return { error: 'Title is required' };

  const task = this.data.insert('tasks', {
    title: normalizedTitle,
    description: description || null,
    status: 'open',
    priority: priority || 'normal',
    due_date: due_date || null,
    entity_type: entity_type || null,
    entity_id: entity_id || null,
    assigned_to: assigned_to || null,
    created_by,
  });

  this.events.publish('tasks.task.created', {
    task_id: task.id,
    title: normalizedTitle,
    entity_type: entity_type || null,
    entity_id: entity_id || null,
    assigned_to: assigned_to || null,
    created_by,
  });

  return task;
}
```

### Input validation pattern

Validate early, return `{ error: 'message' }` on failure. Route handlers check for this and return the appropriate HTTP status:

```js
// In the private method:
const normalizedTitle = title?.trim();
if (!normalizedTitle) return { error: 'Title is required' };

// In the route handler:
const result = this.createTask({ ... });
return result.error
  ? { status: 422, data: result }
  : { status: 201, data: result };
```

### Event publishing pattern

Publish after the data operation succeeds. Include the entity ID and enough context for subscribers to act without round-trips:

```js
this.events.publish('tasks.task.created', {
  task_id: task.id,
  title: normalizedTitle,
  entity_type: entity_type || null,
  entity_id: entity_id || null,
  assigned_to: assigned_to || null,
  created_by,
});
```

### Graceful degradation for optional dependencies

When calling an optional dependency, catch errors and provide fallbacks:

```js
async _resolveDeal(dealId) {
  if (!dealId) return 'unknown deal';
  try {
    const deal = await this.coordinator.call('pipeline', 'getDeal', { dealId });
    return deal?.title || 'unknown deal';
  } catch { return 'unknown deal'; }
}
```

---

## package.json

Every bundle needs a minimal `package.json`:

```json
{
  "name": "@torquedev/bundle-tasks",
  "version": "0.1.0",
  "description": "Task management — create, assign, and track tasks",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/torque-framework/torque-bundle-tasks.git"
  },
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

Key points:
- `"type": "module"` is required -- Torque is ESM-only
- `"main": "logic.js"` -- the kernel imports this
- No build step. No bundler. No transpiler.
- Bundles should have zero runtime dependencies (the kernel provides everything)

---

## Adding UI

### ui/index.js exports

The UI entry point exports a `views` object mapping component names to view functions:

```js
import TaskList from './TaskList.js';

export default {
  views: {
    'task-list': TaskList,
  },
};
```

The component key (`task-list`) must match the `component` value in the manifest's `ui.routes`:

```yaml
ui:
  routes:
    - { path: /tasks, component: task-list }
```

### Using @torquedev/ui-kit

Bundle views return **ui-kit descriptors** -- pure JavaScript objects, not React components. The shell renders them:

```js
import { page, dataTable, button, stack } from '@torquedev/ui-kit';

export default function TaskList({ data, actions }) {
  return page({ title: 'Tasks' }, [
    stack({ direction: 'row', justify: 'space-between' }, [
      button({ label: 'New Task', onClick: () => actions.navigate('/tasks/new') }),
    ]),
    dataTable({
      columns: [
        { field: 'title', header: 'Title' },
        { field: 'status', header: 'Status' },
        { field: 'priority', header: 'Priority' },
        { field: 'due_date', header: 'Due Date' },
      ],
      rows: data.tasks,
      onRowClick: (row) => actions.navigate(`/tasks/${row.id}`),
    }),
  ]);
}
```

This is framework-agnostic. The shell (React + MUI today, anything tomorrow) maps these descriptors to real components. Bundles never import React.

---

## Testing Your Bundle

### Test helpers -- mock pattern

Create `test/helpers.js` with mock factories for the four injected services. No external test dependencies needed:

```js
// test/helpers.js
// Vendored mock factories — no @torquedev/test-helpers dependency

export function createMockData() {
  const store = {};
  let idCounter = 0;
  return {
    insert(table, attrs) {
      if (!store[table]) store[table] = [];
      const record = {
        ...attrs,
        id: attrs.id || `id-${++idCounter}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      store[table].push(record);
      return { ...record };
    },
    find(table, id) {
      return (store[table] || []).find((r) => r.id === id) || null;
    },
    query(table, filters = {}, opts = {}) {
      let results = (store[table] || []).filter((r) =>
        Object.entries(filters).every(([k, v]) => r[k] === v),
      );
      if (opts.order) {
        const [col, dir] = opts.order.split(' ');
        results.sort((a, b) =>
          dir === 'DESC'
            ? b[col] > a[col] ? 1 : -1
            : a[col] > b[col] ? 1 : -1,
        );
      }
      if (opts.offset) results = results.slice(opts.offset);
      if (opts.limit) results = results.slice(0, opts.limit);
      return results;
    },
    update(table, id, attrs) {
      const arr = store[table] || [];
      const idx = arr.findIndex((r) => r.id === id);
      if (idx >= 0) {
        arr[idx] = { ...arr[idx], ...attrs, updated_at: new Date().toISOString() };
        return { ...arr[idx] };
      }
      return null;
    },
    delete(table, id) {
      if (store[table]) store[table] = store[table].filter((r) => r.id !== id);
      return true;
    },
    count(table, filters = {}) {
      return (store[table] || []).filter((r) =>
        Object.entries(filters).every(([k, v]) => r[k] === v),
      ).length;
    },
    transaction(fn) { fn(); },
    _store: store,
  };
}

export function createMockEvents() {
  const published = [];
  return {
    publish(name, payload) { published.push({ name, payload }); },
    _published: published,
  };
}

export function createMockCoordinator(responses = {}) {
  return {
    async call(bundle, iface, args) {
      const key = `${bundle}.${iface}`;
      if (responses[key]) return responses[key](args);
      return null;
    },
  };
}
```

### Test structure

Tests use Node.js built-in `node:test` -- no Jest, no Mocha, no dependencies:

```js
// test/tasks.test.js
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import Tasks from '../logic.js';
import { createMockData, createMockEvents, createMockCoordinator } from './helpers.js';

const tasksCoordinatorResponses = {
  'pipeline.getDeal': (args) => ({ id: args.dealId, title: 'Test Deal' }),
  'pipeline.getStage': (args) => ({ id: args.stageId, name: 'Submitted' }),
};

describe('Tasks bundle', () => {
  let tasks, data, events;

  beforeEach(() => {
    data = createMockData();
    events = createMockEvents();
    tasks = new Tasks({
      data,
      events,
      config: { config: {} },
      coordinator: createMockCoordinator(tasksCoordinatorResponses),
    });
  });

  describe('createTask', () => {
    it('creates a task and publishes event', () => {
      const task = tasks.createTask({
        title: 'Call client',
        entity_id: 'deal-1',
        entity_type: 'deal',
        created_by: 'user-1',
      });
      assert.equal(task.title, 'Call client');
      assert.equal(task.status, 'open');
      assert.equal(task.entity_id, 'deal-1');

      const event = events._published.find(e => e.name === 'tasks.task.created');
      assert.ok(event);
      assert.equal(event.payload.title, 'Call client');
    });

    it('rejects empty title', () => {
      const result = tasks.createTask({ title: '', created_by: 'user-1' });
      assert.ok(result.error);
    });

    it('rejects whitespace-only title', () => {
      const result = tasks.createTask({ title: '   ', created_by: 'user-1' });
      assert.ok(result.error);
    });
  });

  describe('completeTask', () => {
    it('marks as completed and publishes event', () => {
      const task = tasks.createTask({ title: 'Do thing', created_by: 'user-1' });
      const completed = tasks.completeTask(task.id, 'user-1');
      assert.equal(completed.status, 'completed');

      const event = events._published.find(e => e.name === 'tasks.task.completed');
      assert.ok(event);
      assert.equal(event.payload.task_id, task.id);
    });
  });

  describe('interfaces', () => {
    it('getTask returns a task by ID', () => {
      const task = tasks.createTask({ title: 'Test', created_by: 'user-1' });
      const ifaces = tasks.interfaces();
      const found = ifaces.getTask({ taskId: task.id });
      assert.equal(found.title, 'Test');
    });
  });
});
```

### Running tests

```bash
node --test 'test/*.test.js'
```

Or via npm:

```bash
npm test
```

The test pattern:
1. Instantiate your class with mocks in `beforeEach`
2. Test business logic methods directly (not through HTTP)
3. Assert on return values AND published events
4. Test validation edge cases (empty strings, missing fields)
5. Test interfaces return the right data

---

## Mounting Your Bundle

### Adding to a mount plan

Bundles are activated by adding them to a mount plan (`config/mount_plans/development.yml`):

```yaml
app:
  name: "my-app"

validation:
  contracts: strict
  events: warn

bundles:
  identity:
    source: "git+https://github.com/torque-framework/torque-bundle-identity.git@main"
    config:
      jwt_secret: "${AUTH_SECRET}"

  tasks:
    source: "git+https://github.com/torque-framework/torque-bundle-tasks.git@main"

  pipeline:
    source: "git+https://github.com/torque-framework/torque-bundle-pipeline.git@main"
```

### Bundle resolution: three source types

| Source | Syntax | Use When |
|--------|--------|----------|
| Local | (no prefix) | Bundle lives in `bundles/<name>/` or `.bundles/<name>/` |
| Path | `path:../relative/path` | Local development with a checkout outside the app |
| Git | `git+https://...@ref` | Production; cloned and locked in `bundle.lock` |

During development, use `path:` sources for instant feedback (no git fetch on every boot). For production, use `git+https://...@tag` with pinned versions.

### Config injection

Pass runtime configuration from the mount plan into the bundle:

```yaml
bundles:
  identity:
    source: "git+https://..."
    config:
      jwt_secret: "${AUTH_SECRET}"
      session_ttl: 3600
```

These values are available in `this.config` inside the bundle class. Environment variables are interpolated: `${VAR}` (required, throws if missing) and `${?VAR}` (optional, empty string if missing).

### Dependency ordering

The kernel reads all `manifest.yml` files, builds a dependency graph from `depends_on`, and runs Kahn's topological sort. Every dependency boots before the bundles that need it. Circular dependencies throw `CircularDependencyError` with the exact cycle path.

You don't control boot order manually -- declare your dependencies and the kernel handles the rest.

---

## Design Principles

These rules govern every bundle. When in doubt, return to these.

### The mount plan is the product

An application is defined by a YAML file, not a codebase. Adding a feature means adding a bundle to the mount plan. If a feature requires code changes in multiple repos to "turn on," the architecture has failed.

### Bundles are stateless compute with declared schemas

A bundle never:
- Holds a database connection (the kernel provides scoped data access)
- Imports another bundle's code (use the coordinator)
- Reads environment variables directly (use `this.config`)
- Knows what application it's part of

### Events are facts, not commands

`tasks.task.created` states what happened. It does not request action. Events fire whether or not anyone subscribes.

**Event naming convention:**

```
<bundle>.<entity>.<past_tense_verb>

tasks.task.created          ✓  fact
tasks.task.completed        ✓  fact
tasks.task.create           ✗  command
tasks.tasks.created         ✗  plural entity
notify_analytics            ✗  names the subscriber
```

Payload rules:
- Always include the entity ID
- Use IDs, not denormalized data (subscribers resolve names themselves)
- Include enough context to avoid round-trips
- snake_case keys, UUID strings for IDs, ISO 8601 for timestamps

### Interfaces are stable contracts

When `tasks` exposes `getTask({ taskId })`, it returns a DTO that won't change when the internal schema changes. Interfaces should be small, focused, and versioned.

### Composition over inheritance

Bundles don't extend each other. They compose through events and interfaces. No base bundle. No class hierarchy. Each bundle is flat and self-contained.

### Auth policy convention

- All mutations (POST, PATCH, DELETE): `auth: true`
- GETs returning user-specific data: `auth: true`
- Public endpoints (sign-in, sign-up, health): `auth: false`

### Convention over configuration, configuration over code

Follow the conventions in this guide. When conventions don't cover your case, use configuration (mount plan). When configuration isn't enough, write code in a bundle. Never write code when configuration would suffice.

---

## Registering Your Bundle

After your bundle is published and tested:

1. Add it to [REGISTRY.md](../REGISTRY.md) in the **Bundles** table
2. Include: bundle name, package name, version, source URL, dependencies, and one-line description
3. Open a PR to the [torque](https://github.com/torque-framework/torque) repo

This makes your bundle discoverable by other developers and by `torque list` / `torque info`.

---

## Complete Example

A minimal "notes" bundle showing the full flow.

### manifest.yml

```yaml
name: notes
version: "1.0.0"
description: "Simple note-taking — create, edit, and organize personal notes"

schema:
  tables:
    notes:
      columns:
        id: { type: uuid, primary: true }
        title: { type: string, null: false }
        body: { type: text }
        pinned: { type: boolean, default: false }
        created_by: { type: uuid }
        created_at: { type: timestamp }
        updated_at: { type: timestamp }
      indexes:
        - { columns: [created_by] }
        - { columns: [pinned] }

events:
  publishes:
    - name: notes.note.created
      schema: { note_id: uuid, title: string, created_by: uuid }
    - name: notes.note.deleted
      schema: { note_id: uuid, deleted_by: uuid }

interfaces:
  queries:
    - getNote
    - listNotesForUser
  contracts:
    getNote:
      description: "Retrieve a note by ID"
      input: { noteId: { type: uuid, required: true } }
      output:
        type: object
        nullable: true
        shape: { id: uuid, title: string, body: text, pinned: boolean, created_by: uuid, created_at: timestamp }
    listNotesForUser:
      description: "List notes created by a specific user"
      input: { userId: { type: uuid, required: true } }
      output:
        type: array
        items: { id: uuid, title: string, pinned: boolean, created_at: timestamp }

api:
  routes:
    - method: GET
      path: /api/notes
      handler: listNotes
      auth: true
    - method: GET
      path: /api/notes/:id
      handler: getNote
      auth: true
    - method: POST
      path: /api/notes
      handler: createNote
      auth: true
    - method: PATCH
      path: /api/notes/:id
      handler: updateNote
      auth: true
    - method: DELETE
      path: /api/notes/:id
      handler: deleteNote
      auth: true

ui:
  script: ui/index.js
  routes:
    - { path: /notes, component: note-list }
  navigation:
    - { label: "Notes", icon: "file-text", path: /notes }

depends_on: []
optional_deps:
  - identity
```

### logic.js

```js
export default class Notes {
  constructor({ data, events, config, coordinator }) {
    this.data = data;
    this.events = events;
    this.config = config;
    this.coordinator = coordinator;
  }

  interfaces() {
    return {
      getNote: ({ noteId }) => this.data.find('notes', noteId),
      listNotesForUser: ({ userId }) =>
        this.data.query('notes', { created_by: userId }, { order: 'created_at DESC' }),
    };
  }

  routes() {
    return {
      listNotes: (ctx) => {
        const notes = this.data.query(
          'notes',
          { created_by: ctx.currentUser.id },
          { order: 'pinned DESC, created_at DESC' },
        );
        return { status: 200, data: notes };
      },

      getNote: (ctx) => {
        const note = this.data.find('notes', ctx.params.id);
        if (!note) return { status: 404, data: { error: 'Note not found' } };
        return { status: 200, data: note };
      },

      createNote: (ctx) => {
        const result = this.createNote({
          title: ctx.body.title,
          body: ctx.body.body,
          created_by: ctx.currentUser.id,
        });
        return result.error
          ? { status: 422, data: result }
          : { status: 201, data: result };
      },

      updateNote: (ctx) => {
        const result = this.updateNote(ctx.params.id, ctx.body);
        return result?.error
          ? { status: 422, data: result }
          : { status: 200, data: result };
      },

      deleteNote: (ctx) => {
        this.data.delete('notes', ctx.params.id);
        this.events.publish('notes.note.deleted', {
          note_id: ctx.params.id,
          deleted_by: ctx.currentUser.id,
        });
        return { status: 200, data: { deleted: true } };
      },
    };
  }

  createNote({ title, body, created_by }) {
    const normalizedTitle = title?.trim();
    if (!normalizedTitle) return { error: 'Title is required' };

    const note = this.data.insert('notes', {
      title: normalizedTitle,
      body: body || null,
      pinned: false,
      created_by,
    });

    this.events.publish('notes.note.created', {
      note_id: note.id,
      title: normalizedTitle,
      created_by,
    });

    return note;
  }

  updateNote(noteId, attrs) {
    const safe = {};
    if (attrs.title !== undefined) {
      const t = attrs.title?.trim();
      if (!t) return { error: 'Title is required' };
      safe.title = t;
    }
    if (attrs.body !== undefined) safe.body = attrs.body;
    if (attrs.pinned !== undefined) safe.pinned = attrs.pinned;

    if (Object.keys(safe).length === 0) return this.data.find('notes', noteId);
    return this.data.update('notes', noteId, safe);
  }
}
```

### test/helpers.js

```js
export function createMockData() {
  const store = {};
  let idCounter = 0;
  return {
    insert(table, attrs) {
      if (!store[table]) store[table] = [];
      const record = {
        ...attrs,
        id: attrs.id || `id-${++idCounter}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      store[table].push(record);
      return { ...record };
    },
    find(table, id) {
      return (store[table] || []).find((r) => r.id === id) || null;
    },
    query(table, filters = {}, opts = {}) {
      return (store[table] || []).filter((r) =>
        Object.entries(filters).every(([k, v]) => r[k] === v),
      );
    },
    update(table, id, attrs) {
      const arr = store[table] || [];
      const idx = arr.findIndex((r) => r.id === id);
      if (idx >= 0) {
        arr[idx] = { ...arr[idx], ...attrs, updated_at: new Date().toISOString() };
        return { ...arr[idx] };
      }
      return null;
    },
    delete(table, id) {
      if (store[table]) store[table] = store[table].filter((r) => r.id !== id);
      return true;
    },
    _store: store,
  };
}

export function createMockEvents() {
  const published = [];
  return {
    publish(name, payload) { published.push({ name, payload }); },
    _published: published,
  };
}

export function createMockCoordinator(responses = {}) {
  return {
    async call(bundle, iface, args) {
      const key = `${bundle}.${iface}`;
      if (responses[key]) return responses[key](args);
      return null;
    },
  };
}
```

### test/notes.test.js

```js
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import Notes from '../logic.js';
import { createMockData, createMockEvents, createMockCoordinator } from './helpers.js';

describe('Notes bundle', () => {
  let notes, data, events;

  beforeEach(() => {
    data = createMockData();
    events = createMockEvents();
    notes = new Notes({
      data,
      events,
      config: {},
      coordinator: createMockCoordinator(),
    });
  });

  describe('createNote', () => {
    it('creates a note and publishes event', () => {
      const note = notes.createNote({
        title: 'Meeting notes',
        body: 'Discussed Q4 roadmap',
        created_by: 'user-1',
      });
      assert.equal(note.title, 'Meeting notes');
      assert.equal(note.pinned, false);

      const event = events._published.find(e => e.name === 'notes.note.created');
      assert.ok(event);
      assert.equal(event.payload.title, 'Meeting notes');
      assert.equal(event.payload.created_by, 'user-1');
    });

    it('rejects empty title', () => {
      const result = notes.createNote({ title: '', created_by: 'user-1' });
      assert.ok(result.error);
    });

    it('rejects whitespace-only title', () => {
      const result = notes.createNote({ title: '   ', created_by: 'user-1' });
      assert.ok(result.error);
    });
  });

  describe('updateNote', () => {
    it('updates title and body', () => {
      const note = notes.createNote({ title: 'Draft', created_by: 'user-1' });
      const updated = notes.updateNote(note.id, { title: 'Final', body: 'Done' });
      assert.equal(updated.title, 'Final');
      assert.equal(updated.body, 'Done');
    });

    it('rejects empty title on update', () => {
      const note = notes.createNote({ title: 'Draft', created_by: 'user-1' });
      const result = notes.updateNote(note.id, { title: '' });
      assert.ok(result.error);
    });
  });

  describe('interfaces', () => {
    it('getNote returns a note by ID', () => {
      const note = notes.createNote({ title: 'Test', created_by: 'user-1' });
      const ifaces = notes.interfaces();
      const found = ifaces.getNote({ noteId: note.id });
      assert.equal(found.title, 'Test');
    });

    it('listNotesForUser returns notes for a user', () => {
      notes.createNote({ title: 'Note 1', created_by: 'user-1' });
      notes.createNote({ title: 'Note 2', created_by: 'user-1' });
      notes.createNote({ title: 'Note 3', created_by: 'user-2' });
      const ifaces = notes.interfaces();
      const results = ifaces.listNotesForUser({ userId: 'user-1' });
      assert.equal(results.length, 2);
    });
  });
});
```

### ui/index.js

```js
import NoteList from './NoteList.js';

export default {
  views: {
    'note-list': NoteList,
  },
};
```

### package.json

```json
{
  "name": "@torquedev/bundle-notes",
  "version": "0.1.0",
  "description": "Simple note-taking — create, edit, and organize personal notes",
  "type": "module",
  "main": "logic.js",
  "license": "MIT",
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

### Mount it

Add to `config/mount_plans/development.yml`:

```yaml
bundles:
  notes:
    source: "path:../torque-bundle-notes"
```

Run `torque start` and the kernel creates tables, mounts routes, registers events, and wires the UI.

### Validate it

```bash
torque validate
```

This checks all 7 composability rules: no cross-imports, event schemas declared, subscriptions reference real events, dependencies exist, interfaces match between manifest and logic, and route handlers are implemented.
