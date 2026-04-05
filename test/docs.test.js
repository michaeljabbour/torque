/**
 * Documentation content tests (TDD)
 * Verifies that documentation files contain required sections per task-11 spec.
 */

import { describe, it, before } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function readDoc(relPath) {
  return readFileSync(join(ROOT, relPath), 'utf8');
}

describe('BUNDLE_AUTHORING.md documentation', () => {
  let content;
  before(() => {
    content = readDoc('docs/BUNDLE_AUTHORING.md');
  });

  describe('Query Operators section', () => {
    it('has a Query Operators heading', () => {
      assert.match(content, /##.*Query Operators/);
    });

    it('shows equality operator example', () => {
      assert.match(content, /equality/i);
    });

    it('shows $ne operator', () => {
      assert.match(content, /\$ne/);
    });

    it('shows $lt operator', () => {
      assert.match(content, /\$lt/);
    });

    it('shows $gte operator', () => {
      assert.match(content, /\$gte/);
    });

    it('shows $lte operator', () => {
      assert.match(content, /\$lte/);
    });

    it('shows $in operator', () => {
      assert.match(content, /\$in/);
    });

    it('shows $like operator', () => {
      assert.match(content, /\$like/);
    });

    it('shows $isNull operator', () => {
      assert.match(content, /\$isNull/);
    });

    it('shows $notNull operator', () => {
      assert.match(content, /\$notNull/);
    });

    it('has a table listing all 10 operators with SQL equivalents', () => {
      // Table should have at least 10 operator rows
      const tableRows = content.match(/\| `?\$[a-zA-Z]+`?/g);
      assert.ok(tableRows && tableRows.length >= 10, `Expected at least 10 operator table rows, got ${tableRows ? tableRows.length : 0}`);
    });

    it('includes aggregation examples (count)', () => {
      assert.match(content, /count/i);
    });

    it('includes aggregation examples (sum with groupBy)', () => {
      assert.match(content, /sum/i);
      assert.match(content, /groupBy/i);
    });

    it('includes avg/min/max aggregation examples', () => {
      assert.match(content, /avg/i);
      assert.match(content, /min/i);
      assert.match(content, /max/i);
    });

    it('includes raw SQL example', () => {
      assert.match(content, /raw/i);
    });

    it('notes table prefixing for raw SQL', () => {
      assert.match(content, /prefix/i);
    });
  });

  describe('Middleware section', () => {
    it('has a Middleware heading', () => {
      assert.match(content, /##.*Middleware/);
    });

    it('shows YAML example with middleware: config', () => {
      assert.match(content, /middleware:/);
    });

    it('shows request_id middleware', () => {
      assert.match(content, /request_id/);
    });

    it('shows request_logging middleware', () => {
      assert.match(content, /request_logging/);
    });

    it('shows compression middleware', () => {
      assert.match(content, /compression/);
    });

    it('shows rate_limit middleware', () => {
      assert.match(content, /rate_limit/);
    });

    it('notes request_id defaults ON', () => {
      assert.match(content, /request_id.*default.*ON|request_id.*defaults.*on|defaults.*ON.*request_id/si);
    });
  });

  describe('Migration Workflow section', () => {
    it('has a Migration Workflow heading', () => {
      assert.match(content, /##.*Migration.*Workflow|##.*Migrations/i);
    });

    it('shows generate CLI subcommand', () => {
      assert.match(content, /torque.*migrat.*generate|generate.*migrat/i);
    });

    it('shows preview CLI subcommand', () => {
      assert.match(content, /torque.*migrat.*preview|preview.*migrat/i);
    });

    it('shows run CLI subcommand', () => {
      assert.match(content, /torque.*migrat.*run|run.*migrat/i);
    });

    it('shows status CLI subcommand', () => {
      assert.match(content, /torque.*migrat.*status|status.*migrat/i);
    });

    it('shows rollback CLI subcommand', () => {
      assert.match(content, /torque.*migrat.*rollback|rollback.*migrat/i);
    });

    it('notes type change detection', () => {
      assert.match(content, /type.*change|column.*type/i);
    });

    it('notes table-rebuild pattern', () => {
      assert.match(content, /rebuild/i);
    });

    it('shows example migration file with up()', () => {
      assert.match(content, /up\(\)/);
    });

    it('shows example migration file with down()', () => {
      assert.match(content, /down\(\)/);
    });
  });
});

describe('REGISTRY.md documentation', () => {
  let content;
  before(() => {
    content = readDoc('REGISTRY.md');
  });

  describe('TypeScript Support section', () => {
    it('has a TypeScript Support heading', () => {
      assert.match(content, /##.*TypeScript.*Support/i);
    });

    it('notes all @torquedev/* packages include .d.ts files', () => {
      assert.match(content, /\.d\.ts/);
    });

    it('has a packages/types table', () => {
      assert.match(content, /\| Package.*\| .*Types/i);
    });

    it('lists core package with key types: Registry, ScopedCoordinator, HookBus, boot()', () => {
      assert.match(content, /Registry/);
      assert.match(content, /ScopedCoordinator/);
      assert.match(content, /HookBus/);
      assert.match(content, /boot\(\)/);
    });

    it('lists datalayer package with DataLayer, BundleScopedData, ValidationError', () => {
      assert.match(content, /DataLayer/);
      assert.match(content, /BundleScopedData/);
      assert.match(content, /ValidationError/);
    });

    it('lists eventbus package with EventBus', () => {
      assert.match(content, /EventBus/);
    });

    it('lists schema package with createTypeValidator, validators, validateRequired', () => {
      assert.match(content, /createTypeValidator/);
      assert.match(content, /validators/);
      assert.match(content, /validateRequired/);
    });

    it('lists server package with createServer, RouteContext', () => {
      assert.match(content, /createServer/);
      assert.match(content, /RouteContext/);
    });
  });
});

describe('README.md documentation', () => {
  let content;
  before(() => {
    content = readDoc('README.md');
  });

  describe('API Documentation section', () => {
    it('has an API Documentation heading', () => {
      assert.match(content, /##.*API.*Documentation|##.*API.*Docs/i);
    });

    it('documents GET /openapi.json endpoint', () => {
      assert.match(content, /\/openapi\.json/);
    });

    it('notes GET /openapi.json is machine-readable spec', () => {
      assert.match(content, /machine-readable|openapi/i);
    });

    it('documents GET /api/docs endpoint for Swagger UI', () => {
      assert.match(content, /\/api\/docs/);
    });

    it('mentions swagger-ui-dist requirement', () => {
      assert.match(content, /swagger-ui-dist/);
    });

    it('notes auto-generation from manifest routes and validate blocks', () => {
      assert.match(content, /auto.generat/i);
      assert.match(content, /manifest/i);
    });
  });
});
