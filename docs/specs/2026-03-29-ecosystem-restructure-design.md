# Ecosystem Restructure Design

## Goal

Split the Torque monorepo at `~/dev/torque` into 23 independent private repos at `~/dev/t/`, each with proper dependency posture, test isolation, and GitHub hosting under `torque-framework/*`.

## Background

Torque currently lives in a single monorepo. As the framework matures, each package needs its own repo with isolated tests, clear dependency boundaries, and independent versioning. The restructure establishes a clean multi-repo architecture where dependency direction is enforced by the filesystem — not by convention.

## Approach

Fresh `git init` for each repo (no history preservation). Each repo gets its source extracted from the monorepo, a proper `package.json` with the correct dependency posture, and is pushed to a private GitHub repo. A lightweight `dev-link.sh` script handles local cross-repo development — no npm workspaces, no package manager orchestration.

## Architecture — 23 Repos

| Tier | Repo | npm package | Runtime deps |
|------|------|-------------|-------------|
| Entry | `torque` | `@torquedev/torque` | depends on core + cli (the installer) |
| Kernel | `torque-core` | `@torquedev/core` | zero |
| Service | `torque-service-datalayer` | `@torquedev/datalayer` | peer: `@torquedev/core`, peer: `better-sqlite3` |
| Service | `torque-service-eventbus` | `@torquedev/eventbus` | peer: `@torquedev/core` |
| Service | `torque-service-server` | `@torquedev/server` | peer: `@torquedev/core`, peer: `express` |
| UI | `torque-ui-kit` | `@torquedev/ui-kit` | zero |
| Tooling | `torque-cli` | `@torquedev/cli` | peer: `@torquedev/core` |
| Tooling | `torque-foundation` | none (git-only) | zero |
| Tooling | `torque-test-helpers` | `@torquedev/test-helpers` | zero |
| Extension | `torque-ext-authorization` | `@torquedev/authorization` | peer: `@torquedev/core` |
| Extension | `torque-ext-soft-delete` | `@torquedev/datalayer-soft-delete` | peer: `@torquedev/datalayer` |
| Extension | `torque-ext-async-events` | `@torquedev/eventbus-async` | peer: `@torquedev/eventbus` |
| Extension | `torque-ext-search` | `@torquedev/search` | peer: `@torquedev/core` |
| Extension | `torque-ext-storage` | `@torquedev/storage` | peer: `@torquedev/core` |
| Bundle | `torque-bundle-graphql` | none (git-only) | zero |
| Bundle | `torque-bundle-identity` | none (git-only) | zero |
| Bundle | `torque-bundle-pipeline` | none (git-only) | zero |
| Bundle | `torque-bundle-pulse` | none (git-only) | zero |
| Bundle | `torque-bundle-tasks` | none (git-only) | zero |
| Shell | `torque-shell-react` | `@torquedev/shell-react` | peer: `react`, `react-dom`, `@mui/material` |
| App | `torque-app-todo` | none | app owns all runtime deps |

## Dependency Architecture — Four Postures

### 1. Zero deps (kernel, ui-kit, test-helpers, bundles, foundation)

```json
{ "dependencies": {} }
```

Bundles receive everything via constructor injection `{ data, events, config, coordinator }`. They never import framework packages directly. This is what makes them truly portable.

### 2. Peer deps only (services, extensions, cli, shell)

```json
{ "peerDependencies": { "@torquedev/core": ">=1.0.0" } }
```

Import from core in source code but don't own that dependency. The app provides it. Same pattern as Amplifier modules — zero declared deps, free-ride on the host environment.

### 3. App owns everything (torque-app-todo)

The only place that declares actual runtime deps:

```json
{
  "dependencies": {
    "express": "^4.21.0",
    "better-sqlite3": "^11.0.0",
    "js-yaml": "^4.1.0",
    "uuid": "^10.0.0"
  }
}
```

This is where `npm install` happens. The framework itself never pulls from npm.

### 4. Entry point (torque)

Contains install script that clones framework repos + runs `dev-link.sh`. Later becomes thin npm installer package.

## Local Dev Infrastructure

### Directory Structure

```
~/dev/t/
├── torque-core/
├── torque-service-datalayer/
├── torque-service-eventbus/
├── torque-service-server/
├── torque-ui-kit/
├── torque-cli/
├── torque-foundation/
├── torque-test-helpers/
├── torque-ext-authorization/
├── torque-ext-soft-delete/
├── torque-ext-async-events/
├── torque-ext-search/
├── torque-ext-storage/
├── torque-bundle-graphql/
├── torque-bundle-identity/
├── torque-bundle-pipeline/
├── torque-bundle-pulse/
├── torque-bundle-tasks/
├── torque-shell-react/
├── torque-app-todo/
├── torque/
└── dev-link.sh
```

### `dev-link.sh`

A ~20-line script that creates a shared `node_modules/@torquedev/` directory with symlinks to each repo. Run once after cloning. Delete to reset. No npm, no package manager — just filesystem links.

Each repo passes its own tests in complete isolation — no symlinks needed. Mocks for any cross-repo dependencies.

## Split Mechanics

For each repo:

1. `mkdir ~/dev/t/<repo> && cd ~/dev/t/<repo> && git init`
2. Copy source from monorepo
3. Add `package.json` with correct name, peerDeps, test script
4. Add `.gitignore`
5. Ensure `node --test` passes in isolation
6. `git add -A && git commit -m "initial commit"`
7. `gh repo create torque-framework/<repo> --private --source=. --push`

All repos are **private** on GitHub under `torque-framework/`.

## Push Order

Strict dependency sequence — within each phase, repos are independent and can push in parallel.

```
Phase 1: torque-core
Phase 2: torque-service-datalayer
         torque-service-eventbus
         torque-service-server
         torque-ui-kit
         torque-test-helpers
Phase 3: torque-cli
         torque-foundation
Phase 4: torque-ext-authorization
         torque-ext-soft-delete
         torque-ext-async-events
         torque-ext-search
         torque-ext-storage
Phase 5: torque-bundle-identity
         torque-bundle-pipeline
         torque-bundle-pulse
         torque-bundle-tasks
         torque-bundle-graphql
Phase 6: torque-shell-react
Phase 7: torque-app-todo
Phase 8: torque (entry point)
```

## Source Mapping

| Current (monorepo) | Target repo |
|---------------------|-------------|
| `packages/core/` | `torque-core/` |
| `packages/datalayer/` | `torque-service-datalayer/` |
| `packages/eventbus/` | `torque-service-eventbus/` |
| `packages/server/` | `torque-service-server/` |
| `packages/cli/` + `packages/create-app/` | `torque-cli/` |
| `packages/ui-kit/` | `torque-ui-kit/` |
| `packages/test-helpers/` | `torque-test-helpers/` |
| `packages/authorization/` | `torque-ext-authorization/` |
| `packages/datalayer-soft-delete/` | `torque-ext-soft-delete/` |
| `packages/eventbus-async/` | `torque-ext-async-events/` |
| `packages/search/` | `torque-ext-search/` |
| `packages/storage/` | `torque-ext-storage/` |
| `packages/graphql/` | `torque-bundle-graphql/` |
| `examples/bundles/identity/` | `torque-bundle-identity/` |
| `examples/bundles/pipeline/` | `torque-bundle-pipeline/` |
| `examples/bundles/pulse/` | `torque-bundle-pulse/` |
| `examples/bundles/tasks/` | `torque-bundle-tasks/` |
| `examples/dealtracker/` | Absorbed into `torque-app-todo/` |
| `examples/todo-app/` | `torque-app-todo/` |
| `foundation/` | `torque-foundation/` |
| `docs/spec/` + governance | `torque/` (entry point) |
| (new) | `torque-shell-react/` |

## Testing Strategy

Each repo passes `node --test` in complete isolation. Cross-repo dependencies are mocked. No symlinks required to run a single repo's tests.

Integration testing happens at the app level (`torque-app-todo`) where all packages are assembled together.

## Open Questions

None — all sections validated.