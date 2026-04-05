# Torque Package Registry

> Canonical source of truth for all Torque framework packages. Bundle authors: add your bundle here after publishing.

## Core

Packages that make up the Torque kernel and runtime. Installed via npm.

| Package | Version | Install | Source | Description |
|---------|---------|---------|--------|-------------|
| `@torquedev/core` | 0.1.0 | `npm install @torquedev/core` | [torque-core](https://github.com/torque-framework/torque-core) | Kernel: resolver, registry, HookBus, intents |
| `@torquedev/cli` | 0.1.1 | `npm install -g @torquedev/cli` | [torque-cli](https://github.com/torque-framework/torque-cli) | CLI: scaffolding, dev server, seeding, bundle management |
| `@torquedev/schema` | 0.1.0 | `npm install @torquedev/schema` | [torque-schema](https://github.com/torque-framework/torque-schema) | Type validators and contract checking (zero deps) |
| `@torquedev/foundation` | 0.1.0 | `npm install @torquedev/foundation` | [torque-foundation](https://github.com/torque-framework/torque-foundation) | Catalog, mount plans, agents, recipes, design context |

## Services

Runtime services injected into bundles. Installed via npm.

| Package | Version | Install | Source | Description |
|---------|---------|---------|--------|-------------|
| `@torquedev/datalayer` | 0.1.0 | `npm install @torquedev/datalayer` | [torque-service-datalayer](https://github.com/torque-framework/torque-service-datalayer) | Bundle-scoped SQLite storage with WAL + read pooling |
| `@torquedev/eventbus` | 0.1.0 | `npm install @torquedev/eventbus` | [torque-service-eventbus](https://github.com/torque-framework/torque-service-eventbus) | Pub/sub with contract validation |
| `@torquedev/server` | 0.1.0 | `npm install @torquedev/server` | [torque-service-server](https://github.com/torque-framework/torque-service-server) | Express + SPA serving + bundle route mounting |

## UI

| Package | Version | Install | Source | Description |
|---------|---------|---------|--------|-------------|
| `@torquedev/shell-react` | 0.1.0 | `npm install @torquedev/shell-react` | [torque-shell-react](https://github.com/torque-framework/torque-shell-react) | React + MUI shell with auto-wiring |
| `@torquedev/ui-kit` | 0.1.0 | `npm install @torquedev/ui-kit` | [torque-ui-kit](https://github.com/torque-framework/torque-ui-kit) | Declarative UI element descriptors |

## Extensions

Optional capabilities that enhance core services. Install alongside the service they extend.

| Package | Version | Install | Source | Description |
|---------|---------|---------|--------|-------------|
| `@torquedev/ext-authorization` | 0.1.0 | `npm install @torquedev/ext-authorization` | [torque-ext-authorization](https://github.com/torque-framework/torque-ext-authorization) | HookBus-based RBAC authorization middleware |
| `@torquedev/ext-soft-delete` | 0.1.0 | `npm install @torquedev/ext-soft-delete` | [torque-ext-soft-delete](https://github.com/torque-framework/torque-ext-soft-delete) | Soft-delete mixin for datalayer |
| `@torquedev/ext-async-events` | 0.1.0 | `npm install @torquedev/ext-async-events` | [torque-ext-async-events](https://github.com/torque-framework/torque-ext-async-events) | Async job queue with retry for eventbus |
| `@torquedev/ext-search` | 0.1.0 | `npm install @torquedev/ext-search` | [torque-ext-search](https://github.com/torque-framework/torque-ext-search) | SQLite FTS5 full-text search |
| `@torquedev/ext-storage` | 0.1.0 | `npm install @torquedev/ext-storage` | [torque-ext-storage](https://github.com/torque-framework/torque-ext-storage) | File storage with bundle-scoped namespaces |
| `@torquedev/ext-embeddings` | 0.1.0 | `npm install @torquedev/ext-embeddings` | [torque-ext-embeddings](https://github.com/torque-framework/torque-ext-embeddings) | Vector search — embedding generation, similarity queries, auto-indexing |
| `@torquedev/ext-otel` | 0.1.0 | `npm install @torquedev/ext-otel` | [torque-ext-otel](https://github.com/torque-framework/torque-ext-otel) | OpenTelemetry spans, structured JSON logs, trace correlation across bundles |
| `@torquedev/ext-security` | 0.1.0 | `npm install @torquedev/ext-security` | [torque-ext-security](https://github.com/torque-framework/torque-ext-security) | RBAC role checks, rate limiting, CSRF validation, audit logging |

### Behaviors

One-line opt-in via the `behaviors:` key in your mount plan bundle entry.

| Behavior | Extension | Mount Plan Usage |
|----------|-----------|-----------------|
| `observability` | `ext-otel` | `behaviors: [observability]` |
| `security-hardened` | `ext-security` | `behaviors: [security-hardened]` |

---

## Bundles

Self-contained feature modules loaded via mount plans. Install via git URL in your mount plan.

| Bundle | Package | Version | Source | Depends On | Description |
|--------|---------|---------|--------|------------|-------------|
| `identity` | `@torquedev/bundle-identity` | 0.1.0 | [torque-bundle-identity](https://github.com/torque-framework/torque-bundle-identity) | -- | Authentication, JWT sessions |
| `iam` | `@torquedev/bundle-iam` | 1.0.0 | [torque-bundle-iam](https://github.com/torque-framework/torque-bundle-iam) | -- | Consolidated auth, roles, profiles, teams |
| `pipeline` | `@torquedev/bundle-pipeline` | 0.1.0 | [torque-bundle-pipeline](https://github.com/torque-framework/torque-bundle-pipeline) | -- | Stage-based workflow engine |
| `pulse` | `@torquedev/bundle-pulse` | 0.1.0 | [torque-bundle-pulse](https://github.com/torque-framework/torque-bundle-pulse) | -- | Activity timeline |
| `tasks` | `@torquedev/bundle-tasks` | 0.1.0 | [torque-bundle-tasks](https://github.com/torque-framework/torque-bundle-tasks) | -- | Task management |
| `graphql` | `@torquedev/bundle-graphql` | 0.1.0 | [torque-bundle-graphql](https://github.com/torque-framework/torque-bundle-graphql) | -- | Auto-generated GraphQL API + GraphiQL |
| `workspace` | `@torquedev/bundle-workspace` | 0.1.0 | [torque-bundle-workspace](https://github.com/torque-framework/torque-bundle-workspace) | -- | Organizations, members, invites |
| `profile` | `@torquedev/bundle-profile` | 0.1.0 | [torque-bundle-profile](https://github.com/torque-framework/torque-bundle-profile) | -- | User profiles, preferences |
| `admin` | `@torquedev/bundle-admin` | 0.1.0 | [torque-bundle-admin](https://github.com/torque-framework/torque-bundle-admin) | -- | Roles, permissions, RBAC panel |
| `search` | `@torquedev/bundle-search` | 0.1.0 | [torque-bundle-search](https://github.com/torque-framework/torque-bundle-search) | -- | Full-text search, typeahead |
| `boards` | `@torquedev/bundle-boards` | 0.1.0 | [torque-bundle-boards](https://github.com/torque-framework/torque-bundle-boards) | workspace | Boards within workspaces |
| `kanban` | `@torquedev/bundle-kanban` | 0.1.0 | [torque-bundle-kanban](https://github.com/torque-framework/torque-bundle-kanban) | boards | Lists, cards, labels, checklists |
| `activity` | `@torquedev/bundle-activity` | 0.1.0 | [torque-bundle-activity](https://github.com/torque-framework/torque-bundle-activity) | kanban, boards | Activity feed, comments, notifications |
| `realtime` | `@torquedev/bundle-realtime` | 0.1.0 | [torque-bundle-realtime](https://github.com/torque-framework/torque-bundle-realtime) | kanban, boards | WebSocket broadcast |

### Composite Bundles

Full-stack application bundles that combine multiple features into a single installable unit.

| Bundle | Package | Version | Source | Description |
|--------|---------|---------|--------|-------------|
| `kanban-app` | `@torquedev/bundle-kanban-app` | 1.0.0 | [torque-bundle-kanban-app](https://github.com/torque-framework/torque-bundle-kanban-app) | Full kanban application (workspace + boards + kanban) |
| `search-app` | `@torquedev/bundle-search-app` | 0.1.0 | [torque-bundle-search-app](https://github.com/torque-framework/torque-bundle-search-app) | Full-text search with auto-indexing |
| `activity-app` | `@torquedev/bundle-activity-app` | 0.1.0 | [torque-bundle-activity-app](https://github.com/torque-framework/torque-bundle-activity-app) | Activity feed with real-time broadcast |

## Testing & Development

| Package | Version | Install | Source | Description |
|---------|---------|---------|--------|-------------|
| `@torquedev/test-helpers` | 0.1.0 | `npm install --save-dev @torquedev/test-helpers` | [torque-test-helpers](https://github.com/torque-framework/torque-test-helpers) | Shared mock factories for bundle tests |

## Example Applications

| App | Source | Description |
|-----|--------|-------------|
| `@torquedev/app-todo` | [torque-app-todo](https://github.com/torque-framework/torque-app-todo) | Reference todo-list app demonstrating the full framework lifecycle |

## CLI Templates

Available via `torque new --template <name>`:

| Template | Bundles | Description |
|----------|---------|-------------|
| `minimal` | identity | Simplest possible app — authentication only |
| `standard` | identity, pipeline, pulse, tasks | Deal-tracking app with full business logic |
| `kanban` | iam, kanban-app, activity-app, search-app | Full kanban board with real-time collaboration |
| `api-only` | identity, pipeline, tasks | Headless API server — no shell/UI |

Default: `standard`. All templates include a `Dockerfile`, `deploy.yml`, and `.env.example`.

## TypeScript Support

All `@torquedev/*` packages include `.d.ts` declaration files. No separate `@types/` packages are needed — TypeScript support is bundled with every package.

| Package | Key Types |
|---------|-----------|
| `@torquedev/core` | `Registry`, `ScopedCoordinator`, `HookBus`, `boot()` |
| `@torquedev/datalayer` | `DataLayer`, `BundleScopedData`, `ValidationError` |
| `@torquedev/eventbus` | `EventBus` |
| `@torquedev/schema` | `createTypeValidator`, `validators`, `validateRequired` |
| `@torquedev/server` | `createServer`, `RouteContext` |

---

## Using bundles in your mount plan

Bundles are loaded via git URL in your mount plan (`config/mount_plans/development.yml`):

```yaml
bundles:
  identity:
    source: "git+https://github.com/torque-framework/torque-bundle-identity.git@main"
    config:
      jwt_secret: "${AUTH_SECRET}"

  tasks:
    source: "git+https://github.com/torque-framework/torque-bundle-tasks.git@main"
```

For local development, use a path:

```yaml
  tasks:
    source: "../torque-bundle-tasks"
```

## Adding your bundle to the registry

After creating a bundle (see [Bundle Authoring Guide](./docs/BUNDLE_AUTHORING.md)):

1. Push your bundle repo to GitHub
2. Add an entry to the **Bundles** table above
3. Open a PR to this repo

Include: bundle name, package name, version, source URL, dependencies, and a one-line description.
