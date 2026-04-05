# Auto-Wiring Shell Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.

**Goal:** Create `torque-shell-react` — a framework package that provides a complete React+MUI shell which auto-discovers and renders bundle UIs from manifests at runtime. Zero hardcoded bundle imports. The shell is to the frontend what the kernel is to the backend.

**Architecture:** The shell fetches `/api/introspect` at runtime and dynamically generates routes, navigation, and bundle view pages. Bundle UI scripts are loaded via dynamic `import()` from `/bundles/{name}/{script}`. The existing `renderer.jsx` (MUI adapter) is ported from the dealtracker POC and made fully standalone. The package exports a `createShell(config)` Express middleware factory.

**Tech Stack:** React 19, React Router 7, MUI 7, Vite 6 (build tool), `node:test` for server-side tests, Vitest + Testing Library for React component tests.

**Design Spec:** `docs/specs/2026-03-29-auto-wiring-shell-design.md`

**Prerequisite:** Plan 1 complete (repos exist at `~/dev/t/`, `dev-link.sh` works).

---

### Task 1: Create repo structure and build config

**Files:**
- Create: `~/dev/t/torque-shell-react/package.json`
- Create: `~/dev/t/torque-shell-react/vite.config.js`
- Create: `~/dev/t/torque-shell-react/.gitignore`

**Step 1: Create repo**

```bash
mkdir -p ~/dev/t/torque-shell-react/src
mkdir -p ~/dev/t/torque-shell-react/test
cd ~/dev/t/torque-shell-react
git init
```

**Step 2: Create package.json**

```json
{
  "name": "@torquedev/shell-react",
  "version": "0.1.0",
  "description": "Auto-wiring React+MUI shell for Torque — reads /api/introspect and dynamically composes frontend from bundle manifests",
  "type": "module",
  "main": "src/createShell.js",
  "exports": {
    ".": "./src/createShell.js",
    "./App": "./src/App.jsx"
  },
  "license": "MIT",
  "peerDependencies": {
    "react": ">=19.0.0",
    "react-dom": ">=19.0.0",
    "@mui/material": ">=7.0.0",
    "@emotion/react": ">=11.0.0",
    "@emotion/styled": ">=11.0.0",
    "react-router-dom": ">=7.0.0"
  },
  "devDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@mui/material": "^7.3.9",
    "@mui/icons-material": "^7.3.9",
    "@emotion/react": "^11.0.0",
    "@emotion/styled": "^11.0.0",
    "react-router-dom": "^7.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^6.0.0",
    "vitest": "^3.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "jsdom": "^25.0.0",
    "express": "^4.21.0"
  },
  "scripts": {
    "build": "vite build",
    "test": "vitest run",
    "test:server": "node --test 'test/server/*.test.js'"
  }
}
```

**Step 3: Create vite.config.js**

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  build: {
    outDir: 'dist',
    lib: {
      entry: 'src/main.jsx',
      formats: ['es'],
      fileName: 'shell',
    },
    rollupOptions: {
      // Don't bundle React/MUI — they come from the app
      external: ['react', 'react-dom', 'react-router-dom',
        /^@mui\//, /^@emotion\//],
    },
  },

  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./test/setup.js'],
    include: ['test/**/*.test.{js,jsx}'],
  },
});
```

**Step 4: Create test setup**

Create `~/dev/t/torque-shell-react/test/setup.js`:

```javascript
import '@testing-library/jest-dom';
```

**Step 5: Create .gitignore**

```
node_modules/
dist/
.DS_Store
```

**Step 6: Install dependencies**

```bash
cd ~/dev/t/torque-shell-react
npm install
```

**Step 7: Commit**

```bash
git add -A && git commit -m "feat: initial repo structure with build config"
```

---

### Task 2: Port renderer.jsx — ui-kit descriptor to MUI adapter

**Files:**
- Create: `~/dev/t/torque-shell-react/src/renderer.jsx`
- Create: `~/dev/t/torque-shell-react/test/renderer.test.jsx`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/renderer.test.jsx`:

```jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { renderDescriptor } from '../src/renderer.jsx';

describe('renderDescriptor', () => {
  it('returns null for null descriptor', () => {
    const result = renderDescriptor(null);
    expect(result).toBeNull();
  });

  it('returns null for unknown descriptor type', () => {
    const result = renderDescriptor({ type: 'unknown-widget', props: {} });
    expect(result).toBeNull();
  });

  it('renders a text descriptor', () => {
    const descriptor = { type: 'text', props: { content: 'Hello World', variant: 'h6' } };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('renders a button descriptor', () => {
    const descriptor = { type: 'button', props: { label: 'Click me' } };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('renders a stack with children', () => {
    const descriptor = {
      type: 'stack',
      props: { spacing: 2 },
      children: [
        { type: 'text', props: { content: 'Item 1' } },
        { type: 'text', props: { content: 'Item 2' } },
      ],
    };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('renders an alert descriptor', () => {
    const descriptor = { type: 'alert', props: { severity: 'error', content: 'Something broke' } };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('renders a card descriptor with title', () => {
    const descriptor = { type: 'card', props: { title: 'My Card' } };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('My Card')).toBeInTheDocument();
  });

  it('renders a spinner descriptor', () => {
    const descriptor = { type: 'spinner', props: {} };
    const { container } = render(renderDescriptor(descriptor));
    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
  });

  it('renders nested children from props.children', () => {
    const descriptor = {
      type: 'stack',
      props: {
        children: [
          { type: 'text', props: { content: 'Nested' } },
        ],
      },
    };
    render(renderDescriptor(descriptor));
    expect(screen.getByText('Nested')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/renderer.test.jsx
```

Expected: FAIL — `Cannot find module '../src/renderer.jsx'`

**Step 3: Write the renderer**

Create `~/dev/t/torque-shell-react/src/renderer.jsx` — ported from `examples/dealtracker/shell/renderer.jsx` with the same adapter pattern:

```jsx
import React from 'react';
import MuiStack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import MuiDivider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import MuiTextField from '@mui/material/TextField';
import MuiButton from '@mui/material/Button';
import MuiAlert from '@mui/material/Alert';
import MuiCard from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';

function StackAdapter({ children, ...props }) {
  return <MuiStack {...props}>{children}</MuiStack>;
}

function GridAdapter({ columns, spacing, children, sx: sxProp, ...props }) {
  return (
    <Box
      sx={{ display: 'grid', gridTemplateColumns: columns, gap: spacing, ...sxProp }}
      {...props}
    >
      {children}
    </Box>
  );
}

function DividerAdapter(props) {
  return <MuiDivider {...props} />;
}

function TextAdapter({ content, variant, ...props }) {
  return (
    <Typography variant={variant} {...props}>
      {content}
    </Typography>
  );
}

function TextFieldAdapter({ onChange, name, ...props }) {
  const handleChange = (e) => {
    if (onChange) onChange(name || e.target.name, e.target.value);
  };
  return (
    <MuiTextField
      name={name}
      variant="outlined"
      fullWidth
      size="small"
      {...props}
      onChange={handleChange}
    />
  );
}

function ButtonAdapter({ label, fullWidth, ...props }) {
  return (
    <MuiButton fullWidth={fullWidth} {...props}>
      {label}
    </MuiButton>
  );
}

function AlertAdapter({ content, severity, ...props }) {
  return (
    <MuiAlert severity={severity} {...props}>
      {content}
    </MuiAlert>
  );
}

function FormAdapter({ onSubmit, children, ...props }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) onSubmit(e);
  };
  return (
    <Box component="form" onSubmit={handleSubmit} noValidate {...props}>
      {children}
    </Box>
  );
}

function CardAdapter({ title, children, ...props }) {
  return (
    <MuiCard {...props}>
      <CardContent>
        {title && <Typography variant="h6">{title}</Typography>}
        {children}
      </CardContent>
    </MuiCard>
  );
}

function BadgeAdapter({ text, color, ...props }) {
  return (
    <Chip
      label={text}
      sx={{ backgroundColor: color ? `${color}22` : undefined }}
      {...props}
    />
  );
}

function SpinnerAdapter({ size: sizeProp, ...props }) {
  const sizeMap = { small: 20, large: 48 };
  const size = sizeMap[sizeProp] ?? 32;
  return <CircularProgress size={size} {...props} />;
}

const componentMap = {
  stack: StackAdapter,
  grid: GridAdapter,
  divider: DividerAdapter,
  text: TextAdapter,
  'text-field': TextFieldAdapter,
  button: ButtonAdapter,
  alert: AlertAdapter,
  form: FormAdapter,
  card: CardAdapter,
  badge: BadgeAdapter,
  spinner: SpinnerAdapter,
};

export function renderDescriptor(descriptor, key) {
  if (!descriptor) return null;

  const Component = componentMap[descriptor.type];
  if (!Component) return null;

  const rawChildren = descriptor.children ?? descriptor.props?.children;
  const { children: _propsChildren, ...restProps } = descriptor.props || {};

  const renderedChildren = Array.isArray(rawChildren)
    ? rawChildren.filter(Boolean).map((child, index) => renderDescriptor(child, index))
    : null;

  return (
    <Component key={key} {...restProps}>
      {renderedChildren}
    </Component>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/renderer.test.jsx
```

Expected: PASS — all 9 tests.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: port renderer.jsx from dealtracker POC"
```

---

### Task 3: Build BundleViewPage.jsx — generic dynamic bundle view

**Files:**
- Create: `~/dev/t/torque-shell-react/src/BundleViewPage.jsx`
- Create: `~/dev/t/torque-shell-react/test/BundleViewPage.test.jsx`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/BundleViewPage.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BundleViewPage from '../src/BundleViewPage.jsx';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

function Wrapper({ children }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe('BundleViewPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('shows spinner while loading', () => {
    // Never resolve to keep loading state
    mockFetch.mockReturnValue(new Promise(() => {}));

    const { container } = render(
      <Wrapper>
        <BundleViewPage
          bundleName="pipeline"
          viewName="kanban-board"
          bundleScript="ui/index.js"
          fetchUrls={['/api/pipeline/stages']}
          token="test-token"
        />
      </Wrapper>
    );

    expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
  });

  it('shows error when fetch fails', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(
      <Wrapper>
        <BundleViewPage
          bundleName="pipeline"
          viewName="kanban-board"
          bundleScript="ui/index.js"
          fetchUrls={['/api/pipeline/stages']}
          token="test-token"
        />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('renders descriptor from view function when data loads', async () => {
    // Mock bundle script that returns a view map
    const mockViewFn = (ctx) => ({
      type: 'text',
      props: { content: `Loaded ${ctx.data.length} items` },
    });

    // Mock the dynamic import of the bundle script
    vi.stubGlobal('__TORQUE_BUNDLE_VIEWS__', {
      'pipeline': { 'kanban-board': mockViewFn },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ([{ id: 1 }, { id: 2 }]),
    });

    render(
      <Wrapper>
        <BundleViewPage
          bundleName="pipeline"
          viewName="kanban-board"
          bundleScript="ui/index.js"
          fetchUrls={['/api/pipeline/stages']}
          token="test-token"
          resolveView={() => mockViewFn}
        />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Loaded 1 items')).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/BundleViewPage.test.jsx
```

Expected: FAIL — `Cannot find module '../src/BundleViewPage.jsx'`

**Step 3: Write the BundleViewPage**

This is a rewrite of `examples/dealtracker/shell/pages/BundleViewPage.jsx` — made fully dynamic with no hardcoded bundle imports. The view function is resolved at runtime, either via a `resolveView` prop (for testing) or by dynamically importing the bundle's UI script.

Create `~/dev/t/torque-shell-react/src/BundleViewPage.jsx`:

```jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { renderDescriptor } from './renderer.jsx';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('[BundleViewPage] Render crash:', error, info); }
  render() {
    if (this.state.error) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Something went wrong rendering this view.</Typography>
            <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', fontSize: 12 }}>
              {this.state.error.message}
            </Typography>
          </Alert>
        </Box>
      );
    }
    return this.props.children;
  }
}

// Cache of loaded bundle modules: { bundleName: moduleExports }
const bundleModuleCache = {};

async function loadBundleView(bundleName, viewName, bundleScript, resolveView) {
  // Allow injected resolver (for testing)
  if (resolveView) return resolveView(bundleName, viewName);

  // Dynamic import of the bundle's UI script from the server
  if (!bundleModuleCache[bundleName]) {
    const scriptUrl = `/bundles/${bundleName}/${bundleScript}`;
    bundleModuleCache[bundleName] = await import(/* @vite-ignore */ scriptUrl);
  }

  const mod = bundleModuleCache[bundleName];
  const views = mod.default?.views || mod.views || {};
  return views[viewName] || null;
}

/**
 * Generic page that bridges bundle view functions to the shell renderer.
 *
 * 1. Dynamically loads the bundle's UI script
 * 2. Fetches data from API endpoints (using auth token)
 * 3. Calls the bundle view function with { data, actions }
 * 4. Renders the returned descriptor tree through renderDescriptor()
 *
 * Props:
 *   bundleName   — bundle name (e.g., 'pipeline')
 *   viewName     — view key from the bundle's views map (e.g., 'kanban-board')
 *   bundleScript — path to the bundle's UI script (from manifest ui.script)
 *   fetchUrls    — array of API endpoints to fetch data from
 *   token        — auth token for API requests
 *   showToast    — optional toast function
 *   resolveView  — optional function for testing: (bundleName, viewName) => viewFn
 */
export default function BundleViewPage({
  bundleName, viewName, bundleScript, fetchUrls = [],
  token, showToast, resolveView,
}) {
  const navigate = useNavigate();
  const [viewFn, setViewFn] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dialog, setDialog] = useState(null);

  const fetchWithAuth = useCallback((url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }, [token]);

  // Load the bundle view function
  useEffect(() => {
    loadBundleView(bundleName, viewName, bundleScript, resolveView)
      .then((fn) => {
        if (!fn) setError(`View '${viewName}' not found in bundle '${bundleName}'`);
        else setViewFn(() => fn);
      })
      .catch((err) => {
        console.error(`[BundleViewPage] Failed to load bundle UI: ${err.message}`);
        setError(`Failed to load bundle UI: ${err.message}`);
      });
  }, [bundleName, viewName, bundleScript, resolveView]);

  // Fetch data
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (fetchUrls.length > 0) {
        const results = await Promise.all(
          fetchUrls.map(url => fetchWithAuth(url).then(res => res.json()))
        );
        setData(fetchUrls.length === 1 ? results[0] : results);
      } else {
        setData(null);
      }
    } catch (err) {
      console.error('[BundleViewPage] Fetch error:', err);
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [fetchUrls, fetchWithAuth]);

  useEffect(() => { load(); }, [load]);

  if (loading || !viewFn) {
    return renderDescriptor({ type: 'spinner', props: {} });
  }

  if (error) {
    return renderDescriptor({
      type: 'alert',
      props: { severity: 'error', content: `Failed to load: ${error}` },
    });
  }

  const actions = {
    navigate,
    api: fetchWithAuth,
    refresh: load,
    showDialog: (name, props) => setDialog({ name, props }),
    closeDialog: () => setDialog(null),
    showToast: showToast || (() => {}),
  };

  const descriptor = viewFn({ data, actions });
  return (
    <ErrorBoundary>
      {renderDescriptor(descriptor)}
    </ErrorBoundary>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/BundleViewPage.test.jsx
```

Expected: PASS — all 3 tests.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: BundleViewPage with dynamic bundle view loading"
```

---

### Task 4: Build Layout.jsx — dynamic navigation from introspection

**Files:**
- Create: `~/dev/t/torque-shell-react/src/Layout.jsx`
- Create: `~/dev/t/torque-shell-react/test/Layout.test.jsx`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/Layout.test.jsx`:

```jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../src/Layout.jsx';

const navItems = [
  { label: 'Pipeline', icon: 'columns', path: '/deals' },
  { label: 'Tasks', icon: 'check-square', path: '/tasks' },
  { label: 'Pulse', icon: 'activity', path: '/pulse' },
];

function Wrapper({ children }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

describe('Layout', () => {
  it('renders navigation items from props', () => {
    render(
      <Wrapper>
        <Layout navItems={navItems} branding={{ name: 'TestApp' }}>
          <div>Page content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Pipeline')).toBeInTheDocument();
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Pulse')).toBeInTheDocument();
  });

  it('renders branding name', () => {
    render(
      <Wrapper>
        <Layout navItems={navItems} branding={{ name: 'My App' }}>
          <div>Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('My App')).toBeInTheDocument();
  });

  it('renders children in main content area', () => {
    render(
      <Wrapper>
        <Layout navItems={[]} branding={{ name: 'App' }}>
          <div>Main content here</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Main content here')).toBeInTheDocument();
  });

  it('renders with empty navItems', () => {
    render(
      <Wrapper>
        <Layout navItems={[]} branding={{ name: 'App' }}>
          <div>No nav</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('No nav')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/Layout.test.jsx
```

Expected: FAIL

**Step 3: Write Layout.jsx**

Ported from `examples/dealtracker/shell/components/Layout.jsx`, made fully dynamic — nav items come from props (derived from introspection data), not hardcoded.

Create `~/dev/t/torque-shell-react/src/Layout.jsx`:

```jsx
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Link as RouterLink, useLocation } from 'react-router-dom';

export default function Layout({ children, navItems = [], branding = {}, user, onLogout }) {
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="default" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar variant="dense" sx={{ gap: 1 }}>
          <Typography
            variant="subtitle2"
            sx={{ color: 'primary.main', cursor: 'pointer', letterSpacing: '-0.02em', fontWeight: 600 }}
          >
            {branding.name || 'Torque'}
          </Typography>

          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                component={RouterLink}
                to={item.path}
                size="small"
                sx={{
                  color: isActive ? 'primary.main' : 'text.secondary',
                  bgcolor: isActive ? 'rgba(94,230,184,0.08)' : 'transparent',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' },
                  fontSize: 13,
                  textTransform: 'none',
                }}
              >
                {item.label}
              </Button>
            );
          })}

          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
            {user && (
              <Typography variant="body2" sx={{ color: 'text.disabled', fontSize: 12 }}>
                {user.name} ({user.email})
              </Typography>
            )}
            {onLogout && (
              <Button
                size="small"
                onClick={onLogout}
                sx={{ fontSize: 11, color: 'text.secondary', border: 1, borderColor: 'divider', textTransform: 'none' }}
              >
                Sign out
              </Button>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{ flex: 1, p: 2.5, maxWidth: 1200, mx: 'auto', width: '100%' }}>
        {children}
      </Box>
    </Box>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/Layout.test.jsx
```

Expected: PASS — all 4 tests.

**Step 5: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: Layout with dynamic navigation from introspection data"
```

---

### Task 5: Build App.jsx — auto-generates routes from /api/introspect

**Files:**
- Create: `~/dev/t/torque-shell-react/src/App.jsx`
- Create: `~/dev/t/torque-shell-react/test/App.test.jsx`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/App.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../src/App.jsx';

const mockIntrospection = {
  bundles: {
    pipeline: {
      version: '1.0.0',
      description: 'Stage-based workflow',
      api: {
        routes: [
          { method: 'GET', path: '/api/pipeline/stages', handler: 'listStages', auth: true },
        ],
      },
      ui: {
        script: 'ui/index.js',
        routes: [
          { path: '/deals', component: 'kanban-board' },
          { path: '/deals/list', component: 'deal-list' },
        ],
        navigation: [
          { label: 'Pipeline', icon: 'columns', path: '/deals' },
          { label: 'Deal List', icon: 'list', path: '/deals/list' },
        ],
      },
    },
    tasks: {
      version: '1.0.0',
      description: 'Task management',
      api: { routes: [] },
      ui: {
        script: 'ui/index.js',
        routes: [
          { path: '/tasks', component: 'task-list' },
        ],
        navigation: [
          { label: 'Tasks', icon: 'check-square', path: '/tasks' },
        ],
      },
    },
    identity: {
      version: '1.0.0',
      description: 'Auth',
      api: { routes: [] },
      // No ui section — API-only bundle
    },
  },
};

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('App', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('fetches /api/introspect and generates navigation from bundles with UI', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockIntrospection,
    });

    render(<App config={{ auth: { loginPath: '/login' }, shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Deal List')).toBeInTheDocument();
      expect(screen.getByText('Tasks')).toBeInTheDocument();
    });
  });

  it('shows error state when introspection fails', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    render(<App config={{ auth: { loginPath: '/login' }, shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('API-only bundles (no ui section) do not generate nav items', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => mockIntrospection,
    });

    render(<App config={{ auth: { loginPath: '/login' }, shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      // identity bundle has no ui section — should not appear in nav
      expect(screen.queryByText('Auth')).not.toBeInTheDocument();
      // pipeline bundle has ui — should appear
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/App.test.jsx
```

Expected: FAIL

**Step 3: Write App.jsx**

Create `~/dev/t/torque-shell-react/src/App.jsx`:

```jsx
import { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Layout from './Layout.jsx';
import BundleViewPage from './BundleViewPage.jsx';
import { createDefaultTheme } from './theme.js';

export default function App({ config = {} }) {
  const [introspection, setIntrospection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const theme = createDefaultTheme(config.theme);
  const defaultRoute = config.shell?.defaultRoute || '/';

  useEffect(() => {
    fetch('/api/introspect')
      .then(res => res.json())
      .then(data => { setIntrospection(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
          <CircularProgress />
        </Box>
      </ThemeProvider>
    );
  }

  if (error) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ p: 4 }}>
          <Alert severity="error">Failed to load application: {error}</Alert>
        </Box>
      </ThemeProvider>
    );
  }

  // Extract routes and navigation from all bundles with ui sections
  const navItems = [];
  const routeConfigs = [];

  for (const [bundleName, bundleData] of Object.entries(introspection.bundles || {})) {
    const ui = bundleData.ui;
    if (!ui) continue; // API-only bundle — skip

    // Collect navigation items
    if (ui.navigation) {
      for (const nav of ui.navigation) {
        navItems.push({ ...nav, bundle: bundleName });
      }
    }

    // Collect route configs
    if (ui.routes) {
      for (const route of ui.routes) {
        routeConfigs.push({
          path: route.path,
          component: route.component,
          bundle: bundleName,
          script: ui.script,
          fetchUrls: route.fetchUrls || [],
        });
      }
    }
  }

  const branding = config.branding || { name: 'Torque' };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout navItems={navItems} branding={branding}>
          <Routes>
            {routeConfigs.map((rc) => (
              <Route
                key={rc.path}
                path={rc.path}
                element={
                  <BundleViewPage
                    key={rc.path}
                    bundleName={rc.bundle}
                    viewName={rc.component}
                    bundleScript={rc.script}
                    fetchUrls={rc.fetchUrls}
                  />
                }
              />
            ))}
            {routeConfigs.length > 0 && (
              <Route path="*" element={<Navigate to={defaultRoute} replace />} />
            )}
            {routeConfigs.length === 0 && (
              <Route path="*" element={
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography color="text.secondary">No bundles with UI mounted.</Typography>
                </Box>
              } />
            )}
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}
```

**Step 4: Create the theme helper**

Create `~/dev/t/torque-shell-react/src/theme.js`:

```javascript
import { createTheme } from '@mui/material/styles';

export function createDefaultTheme(themeConfig = {}) {
  const mode = themeConfig.mode || 'dark';
  const primary = themeConfig.primary || '#5ee6b8';

  return createTheme({
    palette: {
      mode,
      background: mode === 'dark'
        ? { default: '#0d1117', paper: '#151b23' }
        : undefined,
      primary: { main: primary },
      text: mode === 'dark'
        ? { primary: '#e6edf3', secondary: '#9da5b4', disabled: '#656d76' }
        : undefined,
      divider: mode === 'dark' ? 'rgba(255,255,255,0.08)' : undefined,
    },
    shape: { borderRadius: 8 },
    typography: {
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    },
  });
}
```

**Step 5: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/App.test.jsx
```

Expected: PASS — all 3 tests.

**Step 6: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: App.jsx auto-generates routes from /api/introspect"
```

---

### Task 6: Build AuthContext.jsx and LoginPage.jsx

**Files:**
- Create: `~/dev/t/torque-shell-react/src/AuthContext.jsx`
- Create: `~/dev/t/torque-shell-react/src/LoginPage.jsx`
- Create: `~/dev/t/torque-shell-react/test/AuthContext.test.jsx`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/AuthContext.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from '../src/AuthContext.jsx';

const mockFetch = vi.fn();
global.fetch = mockFetch;

function TestConsumer() {
  const { user, isAuthenticated, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? 'yes' : 'no'}</span>
      <span data-testid="user-name">{user?.name || 'none'}</span>
      <button onClick={() => login('test@test.com', 'pass')}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    sessionStorage.clear();
  });

  it('starts unauthenticated when no token in storage', async () => {
    render(
      <AuthProvider config={{ auth: { bundle: 'identity' } }}>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('no');
    });
  });

  it('login stores token and sets user', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: 'jwt-123',
        user: { id: 'u1', name: 'Test User', email: 'test@test.com' },
      }),
    });

    render(
      <AuthProvider config={{ auth: { bundle: 'identity' } }}>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('no');
    });

    await act(async () => {
      await userEvent.click(screen.getByText('Login'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('yes');
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/AuthContext.test.jsx
```

Expected: FAIL

**Step 3: Write AuthContext.jsx**

Ported from `examples/dealtracker/shell/contexts/AuthContext.jsx`, made configurable via `config.auth`.

Create `~/dev/t/torque-shell-react/src/AuthContext.jsx`:

```jsx
import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children, config = {} }) {
  const authConfig = config.auth || {};
  const authBundle = authConfig.bundle || 'identity';

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    (async () => {
      const clearAuth = () => {
        sessionStorage.removeItem('token');
        setToken(null);
        setUser(null);
      };

      try {
        const res = await fetch(`/api/${authBundle}/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
        } else {
          clearAuth();
        }
      } catch {
        clearAuth();
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email, password) => {
    const res = await fetch(`/api/${authBundle}/sign_in`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || 'Sign in failed');
    }
    const data = await res.json();
    sessionStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  }, [authBundle]);

  const logout = useCallback(() => {
    sessionStorage.removeItem('token');
    setToken(null);
    setUser(null);
  }, []);

  const value = {
    user, token, loading, login, logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
```

**Step 4: Write LoginPage.jsx**

Create `~/dev/t/torque-shell-react/src/LoginPage.jsx`:

```jsx
import { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import { renderDescriptor } from './renderer.jsx';
import { useAuth } from './AuthContext.jsx';

/**
 * Generic login page that delegates form rendering to the auth bundle's UI.
 * Falls back to a basic built-in form if no bundle UI is available.
 */
export default function LoginPage({ branding = {} }) {
  const [fields, setFields] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleFieldChange = (name, value) => {
    setFields((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    setError('');
    try {
      await login(fields.email, fields.password);
    } catch (err) {
      setError(err.message);
    }
  };

  // Built-in login form using ui-kit descriptors
  const descriptor = {
    type: 'stack',
    props: { spacing: 2 },
    children: [
      { type: 'text', props: { content: `Sign in to ${branding.name || 'Torque'}`, variant: 'h6' } },
      ...(error ? [{ type: 'alert', props: { severity: 'error', content: error } }] : []),
      { type: 'text-field', props: { label: 'Email', name: 'email', value: fields.email, onChange: handleFieldChange } },
      { type: 'text-field', props: { label: 'Password', name: 'password', type: 'password', value: fields.password, onChange: handleFieldChange } },
      { type: 'button', props: { label: 'Sign in', variant: 'contained', fullWidth: true, onClick: handleSubmit } },
    ],
  };

  return (
    <Box sx={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box sx={{ maxWidth: 320, width: '100%', bgcolor: 'background.paper', border: 1, borderColor: 'divider', borderRadius: 2, p: 4 }}>
        {renderDescriptor(descriptor)}
      </Box>
    </Box>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/AuthContext.test.jsx
```

Expected: PASS — all 2 tests.

**Step 6: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: AuthContext and LoginPage with configurable auth bundle"
```

---

### Task 7: Build ToastContext.jsx

**Files:**
- Create: `~/dev/t/torque-shell-react/src/ToastContext.jsx`

**Step 1: Write ToastContext.jsx**

Ported directly from `examples/dealtracker/shell/contexts/ToastContext.jsx` — unchanged.

Create `~/dev/t/torque-shell-react/src/ToastContext.jsx`:

```jsx
import { createContext, useContext, useState, useCallback } from 'react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, severity = 'success') => {
    setToast({ message, severity, key: Date.now() });
  }, []);

  const handleClose = (_, reason) => {
    if (reason === 'clickaway') return;
    setToast(null);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Snackbar
        key={toast?.key}
        open={!!toast}
        autoHideDuration={3000}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {toast ? (
          <Alert onClose={handleClose} severity={toast.severity} variant="filled" sx={{ width: '100%' }}>
            {toast.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </ToastContext.Provider>
  );
}

const NOOP_TOAST = { showToast: () => {} };

export function useToast() {
  const ctx = useContext(ToastContext);
  return ctx ?? NOOP_TOAST;
}
```

**Step 2: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: ToastContext for global notifications"
```

---

### Task 8: Build createShell(config) — Express middleware

**Files:**
- Create: `~/dev/t/torque-shell-react/src/createShell.js`
- Create: `~/dev/t/torque-shell-react/src/main.jsx`
- Create: `~/dev/t/torque-shell-react/test/server/createShell.test.js`

**Step 1: Write the failing test**

Create `~/dev/t/torque-shell-react/test/server/createShell.test.js`:

```javascript
import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { createShell } from '../../src/createShell.js';

describe('createShell', () => {
  it('returns an Express middleware function', () => {
    const middleware = createShell({ branding: { name: 'Test' } });
    assert.equal(typeof middleware, 'function');
  });

  it('accepts config with theme, branding, auth, shell options', () => {
    const config = {
      theme: { primary: '#ff0000', mode: 'light' },
      branding: { name: 'My App', logo: '/logo.svg' },
      auth: { bundle: 'identity', loginPath: '/login' },
      shell: { layout: 'sidebar', defaultRoute: '/dashboard' },
    };
    const middleware = createShell(config);
    assert.equal(typeof middleware, 'function');
  });

  it('middleware attaches to an Express app', () => {
    const middleware = createShell({});
    // The middleware should be a function that can be used with app.use()
    assert.equal(middleware.length >= 2, true, 'middleware should accept (req, res) or (req, res, next)');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd ~/dev/t/torque-shell-react && node --test 'test/server/*.test.js'
```

Expected: FAIL

**Step 3: Write createShell.js**

The shell middleware serves the built React app as static files and injects the app config as a `<script>` tag in the HTML so the React app can read it at runtime.

Create `~/dev/t/torque-shell-react/src/createShell.js`:

```javascript
import express from 'express';
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = join(__dirname, '..', 'dist');

/**
 * Creates Express middleware that serves the shell React app.
 *
 * @param {object} config - App configuration (theme, branding, auth, shell)
 * @returns {function} Express middleware
 */
export function createShell(config = {}) {
  const router = express.Router();

  // Serve built shell assets if they exist
  if (existsSync(distDir)) {
    router.use(express.static(distDir));
  }

  // Serve the shell's index.html with injected config
  router.get('*', (req, res, next) => {
    // Skip API routes and bundle routes
    if (req.path.startsWith('/api/') || req.path.startsWith('/bundles/') || req.path.startsWith('/health')) {
      return next();
    }

    const indexPath = join(distDir, 'index.html');
    if (!existsSync(indexPath)) {
      return res.status(200).send(generateDevHtml(config));
    }

    let html = readFileSync(indexPath, 'utf8');
    // Inject config as a global variable
    const configScript = `<script>window.__TORQUE_CONFIG__ = ${JSON.stringify(config)};</script>`;
    html = html.replace('</head>', `${configScript}\n</head>`);
    res.type('html').send(html);
  });

  return router;
}

/**
 * Generate a minimal HTML page for dev mode (when dist/ doesn't exist).
 */
function generateDevHtml(config) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${config.branding?.name || 'Torque'}</title>
  <script>window.__TORQUE_CONFIG__ = ${JSON.stringify(config)};</script>
</head>
<body>
  <div id="root"></div>
  <p style="text-align:center;color:#666;margin-top:40vh">
    Shell not built. Run <code>npm run build</code> in torque-shell-react, or use Vite dev server.
  </p>
</body>
</html>`;
}
```

**Step 4: Write main.jsx (Vite entry point)**

Create `~/dev/t/torque-shell-react/src/main.jsx`:

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

const config = window.__TORQUE_CONFIG__ || {};
const root = createRoot(document.getElementById('root'));
root.render(<App config={config} />);
```

**Step 5: Run test to verify it passes**

```bash
cd ~/dev/t/torque-shell-react && node --test 'test/server/*.test.js'
```

Expected: PASS — all 3 tests.

**Step 6: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "feat: createShell Express middleware and main.jsx entry point"
```

---

### Task 9: The Linux Desktop Test — integration test

**Files:**
- Create: `~/dev/t/torque-shell-react/test/integration.test.jsx`

**Step 1: Write the integration test**

This test verifies the core contract: bundles with `ui:` sections get routes and nav; bundles without `ui:` don't; adding/removing bundles from introspection dynamically changes what the shell renders.

Create `~/dev/t/torque-shell-react/test/integration.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import App from '../src/App.jsx';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Linux Desktop Test — auto-wiring contract', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('bundles with ui: section get routes and navigation', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        bundles: {
          pipeline: {
            version: '1.0.0',
            ui: {
              script: 'ui/index.js',
              routes: [{ path: '/deals', component: 'kanban-board' }],
              navigation: [{ label: 'Pipeline', icon: 'columns', path: '/deals' }],
            },
          },
        },
      }),
    });

    render(<App config={{ shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
    });
  });

  it('bundles without ui: section do NOT get routes or navigation', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        bundles: {
          identity: {
            version: '1.0.0',
            description: 'Auth only — no UI',
            // No ui section at all
          },
          pipeline: {
            version: '1.0.0',
            ui: {
              script: 'ui/index.js',
              routes: [{ path: '/deals', component: 'kanban-board' }],
              navigation: [{ label: 'Pipeline', icon: 'columns', path: '/deals' }],
            },
          },
        },
      }),
    });

    render(<App config={{ shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
      // identity has no UI — verify it doesn't appear
      expect(screen.queryByText('identity')).not.toBeInTheDocument();
      expect(screen.queryByText('Identity')).not.toBeInTheDocument();
    });
  });

  it('removing a bundle from introspection removes its routes and nav', async () => {
    // First render: pipeline + tasks
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        bundles: {
          pipeline: {
            version: '1.0.0',
            ui: {
              script: 'ui/index.js',
              routes: [{ path: '/deals', component: 'kanban-board' }],
              navigation: [{ label: 'Pipeline', icon: 'columns', path: '/deals' }],
            },
          },
          tasks: {
            version: '1.0.0',
            ui: {
              script: 'ui/index.js',
              routes: [{ path: '/tasks', component: 'task-list' }],
              navigation: [{ label: 'Tasks', icon: 'check-square', path: '/tasks' }],
            },
          },
        },
      }),
    });

    const { unmount } = render(<App config={{ shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Tasks')).toBeInTheDocument();
    });

    unmount();

    // Second render: only pipeline (tasks bundle removed from mount plan)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        bundles: {
          pipeline: {
            version: '1.0.0',
            ui: {
              script: 'ui/index.js',
              routes: [{ path: '/deals', component: 'kanban-board' }],
              navigation: [{ label: 'Pipeline', icon: 'columns', path: '/deals' }],
            },
          },
        },
      }),
    });

    render(<App config={{ shell: { defaultRoute: '/deals' } }} />);

    await waitFor(() => {
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
      expect(screen.queryByText('Tasks')).not.toBeInTheDocument();
    });
  });

  it('no bundles with UI shows empty state', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        bundles: {
          identity: { version: '1.0.0' },
        },
      }),
    });

    render(<App config={{ shell: { defaultRoute: '/' } }} />);

    await waitFor(() => {
      expect(screen.getByText(/no bundles with ui/i)).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run the integration test**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run test/integration.test.jsx
```

Expected: PASS — all 4 tests. This validates the core auto-wiring contract.

**Step 3: Run the full test suite**

```bash
cd ~/dev/t/torque-shell-react && npx vitest run
```

Expected: All tests pass across all test files.

**Step 4: Commit**

```bash
cd ~/dev/t/torque-shell-react && git add -A && git commit -m "test: Linux Desktop Test — validates auto-wiring contract"
```

---

### Task 10: Push to GitHub

**Step 1: Final commit with all files**

```bash
cd ~/dev/t/torque-shell-react
git add -A
git status  # Verify everything looks right
```

**Step 2: Push to GitHub**

```bash
gh repo create torque-framework/torque-shell-react --private --source=. --push
```

**Step 3: Run dev-link.sh to include the shell**

```bash
cd ~/dev/t && bash dev-link.sh
```

Expected: Now shows `@torquedev/shell-react -> torque-shell-react/` in the linked packages.

---

## Important Notes for Implementer

1. **The shell has NO hardcoded bundle names.** If you see `'pipeline'`, `'identity'`, `'tasks'` anywhere in the source code (outside of test mocks), that's a bug. The shell reads everything from `/api/introspect` at runtime.

2. **The renderer.jsx is ported from** `examples/dealtracker/shell/renderer.jsx` in the monorepo. Same adapter pattern, same component map. The only change is removing the `import.meta.env?.DEV` check (replaced with a simple null return for unknown types).

3. **BundleViewPage dynamically imports** bundle UI scripts via `import('/bundles/{name}/{script}')`. The server already serves these at that path (see `packages/server/index.js` lines 179-187). No server changes needed.

4. **The `/api/introspect` endpoint already returns** `ui.routes` and `ui.navigation` from bundle manifests. Verified in `packages/server/index.js` line 72 — it returns the full manifest `ui` field. The App.jsx reads `bundleData.ui.routes` and `bundleData.ui.navigation` which map directly to what the server provides.

5. **Tests use Vitest + Testing Library** for React components and `node:test` for the server-side `createShell` middleware. This matches the dealtracker's existing test setup pattern.

6. **The shell reads `window.__TORQUE_CONFIG__`** for runtime configuration. This is injected by `createShell()` middleware into the HTML. During Vite dev mode, the config comes from the `App` component's `config` prop.
