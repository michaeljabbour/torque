# Extract torque-ext-async-events Implementation Plan

> **Execution:** Use the subagent-driven-development workflow to implement this plan.
>
> **Quality Review Warning:** The quality review loop exhausted 3 iterations without
> approval. The final verdict was **APPROVED** with all 18 tests passing and no critical
> or important issues. Five suggestions remain unaddressed (see Appendix A). Human
> reviewer should verify the implementation matches expectations during the approval gate.

**Goal:** Extract `packages/eventbus-async/` from the monorepo into a standalone repo at `~/dev/t/torque-ext-async-events/` with bug fixes, tests, and push to GitHub.
**Architecture:** Copy `index.js` (async mixin + standalone bus), `async-queue.js` (InProcessQueue with retry), and `test/async.test.js` from the monorepo. Fix the `drain()` bug (missing retry-limbo check), remove dead code, add a test for the fix, add inline documentation, then push. No build step, no runtime dependencies — only a peer dependency on `@torquedev/eventbus`.
**Tech Stack:** Node.js (ESM), `node:test` + `node:assert/strict` for testing, GitHub CLI for repo creation.

**Dependency:** Task 2 (workspace setup at `~/dev/t/`) must be complete before starting.

---

### Task 1: Initialize the repo directory and git

**Files:**
- Create: `~/dev/t/torque-ext-async-events/` (directory)

**Step 1: Create directory and initialize git**
```bash
mkdir -p ~/dev/t/torque-ext-async-events
cd ~/dev/t/torque-ext-async-events
git init
```
Expected: `Initialized empty Git repository in ~/dev/t/torque-ext-async-events/.git/`

---

### Task 2: Copy source files from monorepo

**Files:**
- Create: `~/dev/t/torque-ext-async-events/index.js`
- Create: `~/dev/t/torque-ext-async-events/async-queue.js`
- Create: `~/dev/t/torque-ext-async-events/test/async.test.js`
- Source: `~/dev/torque/packages/eventbus-async/index.js`
- Source: `~/dev/torque/packages/eventbus-async/async-queue.js`
- Source: `~/dev/torque/packages/eventbus-async/test/async.test.js`

**Step 1: Copy the source files**
```bash
cp ~/dev/torque/packages/eventbus-async/index.js ~/dev/t/torque-ext-async-events/index.js
cp ~/dev/torque/packages/eventbus-async/async-queue.js ~/dev/t/torque-ext-async-events/async-queue.js
mkdir -p ~/dev/t/torque-ext-async-events/test
cp ~/dev/torque/packages/eventbus-async/test/async.test.js ~/dev/t/torque-ext-async-events/test/async.test.js
```

**Step 2: Verify the copies are byte-for-byte identical**
```bash
diff ~/dev/torque/packages/eventbus-async/index.js ~/dev/t/torque-ext-async-events/index.js
diff ~/dev/torque/packages/eventbus-async/async-queue.js ~/dev/t/torque-ext-async-events/async-queue.js
diff ~/dev/torque/packages/eventbus-async/test/async.test.js ~/dev/t/torque-ext-async-events/test/async.test.js
```
Expected: No output (files are identical) for all three diffs.

The package exports:
- `applyAsync(EventBusClass, options)` — mixin that patches an EventBus class prototype with `subscribeAsync()`, `getJobStats()`, `getFailedJobs()`, `drain()`
- `AsyncEventBus` class — standalone bus combining sync `subscribe()` and async `subscribeAsync()`
- `InProcessQueue` class — re-exported from `./async-queue.js`

---

### Task 3: Create package.json

**Files:**
- Create: `~/dev/t/torque-ext-async-events/package.json`

**Step 1: Write package.json**

Create `~/dev/t/torque-ext-async-events/package.json` with exactly this content:

```json
{
  "name": "@torquedev/eventbus-async",
  "version": "0.1.0",
  "type": "module",
  "main": "index.js",
  "description": "Async job queue enhancement for @torquedev/eventbus. Adds subscribeAsync() with retry logic.",
  "peerDependencies": {
    "@torquedev/eventbus": ">=0.1.0"
  },
  "dependencies": {},
  "scripts": {
    "test": "node --test 'test/*.test.js'"
  }
}
```

Requirements per spec:
- `name`: `@torquedev/eventbus-async`
- `version`: `0.1.0`
- `type`: `module`
- `main`: `index.js`
- `peerDependencies`: `@torquedev/eventbus >=0.1.0`
- `dependencies`: `{}` (zero runtime dependencies)
- `scripts.test`: `node --test 'test/*.test.js'`

Note: The monorepo `package.json` is missing `peerDependencies`. This is intentional — the monorepo didn't need it because packages were co-located.

---

### Task 4: Create .gitignore

**Files:**
- Create: `~/dev/t/torque-ext-async-events/.gitignore`

**Step 1: Write .gitignore**

Create `~/dev/t/torque-ext-async-events/.gitignore` with exactly this content:

```
node_modules/
.DS_Store
```

Two lines, no trailing newline after `.DS_Store`.

---

### Task 5: Run baseline tests (expect pass)

**Files:**
- Test: `~/dev/t/torque-ext-async-events/test/async.test.js`

**Step 1: Run the existing test suite as-is**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected: All tests pass. The test suite is self-contained — `AsyncEventBus` is a standalone class that doesn't import `@torquedev/eventbus`, so no peer dependency installation is needed for testing.

Note the exact test count. The monorepo test file has ~14 tests across `InProcessQueue` (5) and `AsyncEventBus` (9+) describe blocks.

---

### Task 6: Initial commit

**Files:**
- All files in `~/dev/t/torque-ext-async-events/`

**Step 1: Stage all files and commit**
```bash
cd ~/dev/t/torque-ext-async-events
git add .
git commit -m "feat: extract @torquedev/eventbus-async from monorepo"
```

---

### Task 7: Fix drain() bug — missing retry-limbo check

**Files:**
- Modify: `~/dev/t/torque-ext-async-events/async-queue.js`

This is a **bug** in the monorepo version. The `drain()` method returns while jobs are still in retry-timeout limbo (sitting in a `setTimeout` waiting to be re-enqueued). The `_stats.retrying` counter is already properly maintained — it just isn't consulted in the drain loop.

**Step 1: Write the failing test first**

Add this test inside the `describe('InProcessQueue', ...)` block in `test/async.test.js`, after the existing "reports failed jobs after max retries" test:

```javascript
  it('drain() waits for jobs in retry-timeout limbo', async () => {
    let attempts = 0;
    const queue = new InProcessQueue({
      maxRetries: 2,
      baseDelay: 10, // Short delay for testing
      onFailed: () => {},
    });

    queue.enqueue({
      subscriberName: 'test',
      event: { name: 'test', data: {} },
      handler: async () => {
        attempts++;
        if (attempts < 2) throw new Error('Transient failure');
      },
      options: {},
    });

    // drain() alone — NO pre-wait — must handle retry-timeout limbo
    await queue.drain();

    // Job should have been retried and completed
    assert.strictEqual(attempts, 2);
    assert.strictEqual(queue.getStats().completed, 1);
  });
```

**Step 2: Run to verify the test fails (or is flaky)**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected: The new test may fail or be flaky — `drain()` currently returns before retry jobs re-enqueue, so `attempts` may be 1 instead of 2. The bug is a race condition: `drain()` exits because `processing` is false and `queue.length` is 0, even though `_stats.retrying > 0`.

**Step 3: Fix drain() in async-queue.js**

In `~/dev/t/torque-ext-async-events/async-queue.js`, find the `drain()` method and change the while condition:

Before:
```javascript
  async drain() {
    // Wait for current processing to finish
    while (this.processing || this.queue.length > 0) {
      await new Promise(resolve => setImmediate(resolve));
    }
  }
```

After:
```javascript
  /**
   * Drain the queue — wait for all in-flight jobs to complete.
   * Used for graceful shutdown.
   *
   * Note: when retrying > 0, this polls via setImmediate until the retry
   * setTimeout fires. Acceptable for InProcess; swap to BullMQ for production.
   *
   * @returns {Promise<void>}
   */
  async drain() {
    // Wait for current processing to finish
    while (this.processing || this.queue.length > 0 || this._stats.retrying > 0) {
      await new Promise(resolve => setImmediate(resolve));
    }
  }
```

The only code change is adding `|| this._stats.retrying > 0` to the while guard.

**Step 4: Run tests to verify the fix**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected: All tests pass, including the new `drain() waits for jobs in retry-timeout limbo` test.

**Step 5: Commit**
```bash
cd ~/dev/t/torque-ext-async-events
git add async-queue.js test/async.test.js
git commit -m "fix: drain() waits for jobs in retry-timeout limbo"
```

---

### Task 8: Remove dead code in applyAsync

**Files:**
- Modify: `~/dev/t/torque-ext-async-events/index.js`

The monorepo `index.js` contains two dead code lines in `applyAsync()`:

```javascript
// Store original constructor
const OriginalConstructor = EventBusClass;
// ...
const originalInit = proto._init || proto.constructor; // never used
```

These variables are assigned but never referenced. Remove them.

**Step 1: Remove the dead code**

In `~/dev/t/torque-ext-async-events/index.js`, find and delete these two lines inside the `applyAsync` function:

1. Remove the line: `const OriginalConstructor = EventBusClass;`
2. Remove the line: `const originalInit = proto._init || proto.constructor;`
3. Remove any associated comment lines (e.g. `// Store original constructor`)

**Step 2: Run tests to verify nothing broke**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected: All tests pass (dead code removal should not affect behavior).

**Step 3: Commit**
```bash
cd ~/dev/t/torque-ext-async-events
git add index.js
git commit -m "refactor: remove dead code in applyAsync (OriginalConstructor, originalInit)"
```

---

### Task 9: Address code quality review suggestions

**Files:**
- Modify: `~/dev/t/torque-ext-async-events/async-queue.js`
- Modify: `~/dev/t/torque-ext-async-events/test/async.test.js`

The code quality review identified 5 suggestions. Apply the ones that are low-risk improvements. Skip suggestions that add complexity without clear benefit at POC scope.

**Step 1: Extract duplicated event-name resolution in `_executeJob`**

In `~/dev/t/torque-ext-async-events/async-queue.js`, the expression `typeof job.event === 'object' ? job.event.name : String(job.event)` appears (or would appear) twice inside `_executeJob`. Extract it once before the two objects that use it:

Find the section in `_executeJob` where the max-retries-exceeded branch begins. At the top of that branch, add:

```javascript
        const resolvedEventName = typeof job.event === 'object' ? job.event.name : String(job.event);
```

Then use `resolvedEventName` in both the `failedJob` object (`eventName: resolvedEventName`) and the `_onFailed` callback object (`event: resolvedEventName`).

**Step 2: Add documentation comment for the dual-shape design**

In `~/dev/t/torque-ext-async-events/async-queue.js`, above the `failedJob` object construction, add this comment explaining why `_failedJobs` and the `onFailed` callback use different shapes:

```javascript
        // NOTE: _failedJobs and the onFailed callback use intentionally different shapes:
        //   _failedJobs: { subscriberName, eventName, error, stack, attempts, timestamp }
        //     — optimised for log readability and post-mortem inspection (includes stack).
        //   onFailed callback: { subscriber, event, error, attempts, originalEvent }
        //     — optimised for handler ergonomics (includes full originalEvent object).
```

**Step 3: Add documentation comment for _failedJobs unbounded growth**

In `~/dev/t/torque-ext-async-events/async-queue.js`, above the `this._failedJobs = [];` line in the constructor, add:

```javascript
    // Failed job log (in-memory, resets on restart).
    // Note: grows without bound in long-running processes with persistent failure storms.
    // For production use, consider capping via a constructor option (e.g. maxFailedJobs: 1000)
    // or swap to BullMQ which manages job history externally.
```

**Step 4: Add documentation comment for drain() busy-polling**

This was already added as part of the drain() fix in Task 7 (the JSDoc comment above the method). Verify it's present:

```javascript
   * Note: when retrying > 0, this polls via setImmediate until the retry
   * setTimeout fires. Acceptable for InProcess; swap to BullMQ for production.
```

**Step 5: Fix test indentation for 'per-job maxRetries overrides default'**

In `~/dev/t/torque-ext-async-events/test/async.test.js`, find the test `it('per-job maxRetries overrides default', ...)`. If it is indented at 4 spaces inside the `describe('InProcessQueue')` block (while other tests use 2 spaces), fix the indentation to match the surrounding tests at 2 spaces.

**Step 6: Run tests to verify nothing broke**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected: All tests pass (18 total: 6 InProcessQueue + 12 AsyncEventBus).

**Step 7: Commit**
```bash
cd ~/dev/t/torque-ext-async-events
git add async-queue.js test/async.test.js
git commit -m "refactor: address code quality suggestions from review"
```

---

### Task 10: Final verification and push to GitHub

**Files:**
- All files in `~/dev/t/torque-ext-async-events/`

**Step 1: Run the full test suite one final time**
```bash
cd ~/dev/t/torque-ext-async-events
node --test 'test/*.test.js'
```
Expected output includes:
```
# tests 18
# suites 2
# pass 18
# fail 0
```

**Step 2: Verify the final file tree**
```bash
cd ~/dev/t/torque-ext-async-events
find . -not -path './.git/*' -not -path './.git' | sort
```
Expected:
```
.
./.gitignore
./async-queue.js
./index.js
./package.json
./test
./test/async.test.js
```

**Step 3: Verify git log**
```bash
cd ~/dev/t/torque-ext-async-events
git log --oneline
```
Expected (4 commits, newest first):
```
<hash> refactor: address code quality suggestions from review
<hash> refactor: remove dead code in applyAsync (OriginalConstructor, originalInit)
<hash> fix: drain() waits for jobs in retry-timeout limbo
<hash> feat: extract @torquedev/eventbus-async from monorepo
```

**Step 4: Create private GitHub repo and push**
```bash
cd ~/dev/t/torque-ext-async-events
gh repo create torque-framework/torque-ext-async-events --private --source=. --push
```
Expected: Repo created at `github.com/torque-framework/torque-ext-async-events` (private).

**Step 5: Verify the push**
```bash
cd ~/dev/t/torque-ext-async-events
git remote -v
```
Expected: Shows `origin` pointing to `github.com/torque-framework/torque-ext-async-events.git` (https or ssh).

```bash
gh repo view torque-framework/torque-ext-async-events --json isPrivate
```
Expected: `{"isPrivate": true}`

---

## Acceptance Criteria Checklist

- [ ] `~/dev/t/torque-ext-async-events/` exists as a git repo
- [ ] `index.js` exports `applyAsync`, `AsyncEventBus`, and `InProcessQueue`
- [ ] `async-queue.js` implements `InProcessQueue` with retry + exponential backoff
- [ ] `drain()` correctly waits for jobs in retry-timeout limbo (`_stats.retrying > 0`)
- [ ] Dead code (`OriginalConstructor`, `originalInit`) removed from `index.js`
- [ ] `package.json` has name `@torquedev/eventbus-async`, version `0.1.0`, type `module`, main `index.js`, peerDependencies `@torquedev/eventbus >=0.1.0`, scripts test
- [ ] `.gitignore` contains `node_modules/` and `.DS_Store`
- [ ] `test/async.test.js` includes drain-retry-limbo test
- [ ] `node --test 'test/*.test.js'` passes all 18 tests
- [ ] Repo pushed to GitHub at `torque-framework/torque-ext-async-events` (private)

---

## Appendix A: Unresolved Quality Review Suggestions

The quality review loop exhausted 3 iterations. The final verdict was **APPROVED** (all
18 tests pass, no critical or important issues). The following suggestions were flagged
as "nice to have" — none block merge, but the human reviewer should be aware:

1. **Duplicated event-name extraction** in `_executeJob` — `typeof job.event === 'object' ? job.event.name : String(job.event)` appeared twice. **Addressed in Task 9** by extracting to `resolvedEventName`.

2. **Inconsistent shape between `_failedJobs` and `onFailed` callback** — `_failedJobs` uses `{ subscriberName, eventName, stack }` while callback uses `{ subscriber, event, originalEvent }`. **Addressed in Task 9** with inline documentation explaining the intentional divergence.

3. **Test indentation inconsistency** — `'per-job maxRetries overrides default'` was indented at 4 spaces instead of 2. **Addressed in Task 9**.

4. **`drain()` busy-polls during retry windows** — spins on `setImmediate` while waiting for `setTimeout` backoff (1s, 4s, 9s). Acceptable for POC. **Addressed in Task 9** with inline comment.

5. **`_failedJobs` grows without bound** — `clearFailedJobs()` exists but is never called automatically. **Addressed in Task 9** with inline comment noting the POC scope and suggesting `maxFailedJobs` for production.
