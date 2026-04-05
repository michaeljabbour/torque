# Auto-Wiring Shell Design

## Goal

Create `torque-shell-react` — a framework package that provides a complete React+MUI shell which auto-discovers and renders bundle UIs from manifests. Zero hardcoding in the app. The shell is to the frontend what the kernel is to the backend.

## Background

Today the POC's `shell/App.jsx` hardcodes bundle imports and routes. Adding a bundle's UI requires editing `App.jsx` — violating the composability contract. The framework promises that bundles are self-describing and the app never references them by name, but the current frontend breaks that promise.

## Approach

Build a shell package that reads the server's existing introspection API and dynamically wires routes, navigation, and bundle UIs at runtime. No new protocol needed — the contracts already exist in the spec. The server already serves `/api/introspect` and `/bundles/{name}/`. The only missing piece is a shell that reads this data dynamically instead of hardcoding imports.

## Architecture

The shell reads the server's introspection API and dynamically wires everything:

```
Display Layer (torque-shell-react — framework package)
    ↓ fetches
Protocol Layer (GET /api/introspect, GET /bundles/{name}/{script})
    ↓ served by
Server Layer (torque-service-server — already serves both endpoints)
    ↓ reads from
Manifest Layer (bundle manifest.yml ui: section — already declared)
```

## Components

### Package Contents

| File | Purpose |
|------|---------|
| `createShell(config)` | Express middleware factory — serves the shell app, injects runtime config |
| `App.jsx` | Root React component — fetches `/api/introspect`, auto-generates routes and nav |
| `renderer.jsx` | Maps ui-kit descriptors → MUI components (the adapter layer) |
| `BundleViewPage.jsx` | Generic page — dynamically loads a bundle's UI script, calls the view function, renders the result through the renderer |
| `Layout.jsx` | Sidebar/topbar nav — built dynamically from `ui.navigation` entries across all mounted bundles |
| `LoginPage.jsx` | The only hardcoded page — delegates to whichever bundle handles auth |
| `AuthContext.jsx` | Auth state management — reads auth bundle from `app.config.js` |
| `ToastContext.jsx` | Notification state |
| `theme.js` | Default MUI theme — overridden by `app.config.js` |

### App Configuration (`app.config.js`)

The app provides runtime configuration — the shell reads it but never owns it:

```javascript
export default {
  theme: { primary: '#6ea8fe', mode: 'light' },
  branding: { name: 'My App', logo: '/assets/logo.svg' },
  auth: { bundle: 'identity', loginPath: '/login' },
  shell: { layout: 'sidebar', defaultRoute: '/dashboard' },
};
```

## Data Flow

### Auto-Wiring Flow at Runtime

1. Browser loads shell from `@torquedev/shell-react` (served as static assets by Express middleware)
2. `App.jsx` fetches `GET /api/introspect`
3. For each bundle with `ui.routes` — creates a React Router `<Route>`
4. For each bundle with `ui.navigation` — adds an entry to Layout's sidebar
5. When user navigates to a bundle route — `BundleViewPage` dynamically imports `/bundles/{name}/{script}`, calls the registered view function, gets back ui-kit descriptors, passes them through `renderer.jsx` → MUI components

The shell never knows bundle names, never imports bundle code at build time. Everything is runtime discovery.

### Bundle UI Contract

Each bundle that contributes UI declares it in `manifest.yml`:

```yaml
ui:
  script: ui/index.js
  routes:
    - { path: /deals, component: kanban-board }
    - { path: /deals/list, component: deal-list }
  navigation:
    - { label: "Pipeline", icon: "trending-up", path: /deals }
    - { label: "Deal List", icon: "list", path: /deals/list }
```

The bundle's `ui/index.js` exports a views map:

```javascript
export default {
  views: {
    'kanban-board': KanbanBoard,   // returns ui-kit descriptors
    'deal-list': DealList,         // returns ui-kit descriptors
  },
};
```

Bundles without a `ui:` section simply don't appear in the frontend — no routes, no nav. They're API-only. The shell handles this gracefully because it only generates routes for what introspection returns.

## The Linux Desktop Test

The shell's composability can be validated against the same contract that Linux desktops use:

| Test | Torque equivalent |
|------|-------------------|
| Install app → appears in menu automatically | Add bundle to mount plan → routes and nav appear |
| Remove app → desktop still works | Remove bundle from mount plan → app still works |
| Switch GNOME → KDE → same apps work | Switch shell-react → shell-vue → same bundles work |
| Apps declare their own `.desktop` entry points | Bundles declare `ui.routes` and `ui.navigation` in manifest |
| Desktop reads `/usr/share/applications/` | Shell reads `/api/introspect` |

## Error Handling

- **Introspection fails**: Shell shows error state, no routes generated
- **Bundle script fails to load**: `BundleViewPage` catches the error, shows fallback UI for that route only — other routes unaffected
- **Bundle view function throws**: Renderer catches and displays error boundary — other bundles continue working
- **Auth bundle missing**: `LoginPage` shows configuration error pointing to `app.config.js`
- **No bundles with UI**: Shell renders empty layout with "No bundles mounted" message

## Testing Strategy

- **Unit tests**: Each component (`App.jsx`, `renderer.jsx`, `BundleViewPage.jsx`, `Layout.jsx`) tested in isolation with mocked introspection data
- **Integration tests**: `createShell` middleware tested with a mock Express app serving known bundle manifests
- **Contract tests**: Verify shell correctly handles all valid `ui:` manifest shapes (routes only, nav only, both, neither)
- **The add/remove test**: Mount a bundle → verify route appears. Unmount → verify route disappears. Shell never touched.

## Open Questions

None — all sections validated.