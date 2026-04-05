# Torque Intents Tutorial

Torque is an **Agentic-First, Language-Agnostic Composable Monolith Framework**. While the core kernel runs on a JavaScript runtime, the architecture is entirely unopinionated about language — Intents, Contexts, and Behaviors compile down to standard JSON schemas communicated over events and APIs.

This tutorial walks through real intent examples from the **zero-to-trello** kanban app.

---

## What Are Intents?

In a traditional framework (Rails, Express, Django), the first-class objects are **Routes and Controllers**. The developer tells the computer exactly how to do something, line by line — `if x, loop y, insert z, validate a`. The code is tightly coupled to the programming language.

In Torque, **Intent is the first-class object**.

You stop writing execution logic. Instead, you declare:
- **What** you want (Context — data shape and semantic boundaries)
- **Why** you want it (Intent — goal and success criteria)
- **How safe** it should be (Behavior — tools, guardrails, human-in-the-loop)

You have transformed coding from *writing instructions for a machine* into *writing constraints for an intelligence*.

---

## The Paradigm Shift

### The Old Way (Routes + Controllers)

```javascript
// Traditional: imperative, language-coupled, rigid
app.post('/api/cards/:id/move', (req, res) => {
  const card = db.find('cards', req.params.id);
  if (!card) return res.status(404).json({ error: 'Not found' });
  const updated = db.update('cards', card.id, { list_id: req.body.toListId });
  res.json(updated);
});
```

### The New Way (Intent as First-Class Object)

```javascript
export const OrganizeWorkIntent = new Intent({
  name: 'OrganizeWork',
  description: 'Organize cards on a kanban board by moving them to appropriate lists.',
  trigger: 'User asks to organize, triage, or sort cards on a board',
  successCriteria: [
    'All referenced cards are identified on the board',
    'Cards are moved to the correct target list',
    'A summary of changes is provided to the user',
  ],
  behavior: OrganizeWorkBehavior,
});
```

The kernel decides whether to handle this via a fast database lookup or hand it to an LLM agent based on complexity. The request can come from an HTTP POST, a Slack webhook, a voice command, or a WebSocket — the framework parses the input, matches it to the Intent, and executes.

---

## Core Concepts

### 1. Context (What)

The data boundary — what information the agent can see and search.

```javascript
import { Context } from '@torquedev/core';

export const OrganizeWorkContext = new Context('OrganizeWork', {
  schema: {
    board_id: 'uuid',
    card_name: 'string',
    card_description: 'string',
    current_list: 'string',
    target_list: 'string',
    labels: 'string[]',
    due_date: 'timestamp',
  },
  vectorize: ['card_name', 'card_description'],
});
```

`vectorize` fields get semantic indexing via the VORM (Vector-Object Relational Mapping) layer — enabling fuzzy, natural-language search across cards without writing SQL. The agent doesn't need to figure out how to search a massive database; the framework automatically surfaces precisely bounded semantic context on demand.

### 2. Behavior (How)

Execution guardrails — what tools the agent can use and what requires human approval.

```javascript
import { Behavior } from '@torquedev/core';

export const OrganizeWorkBehavior = new Behavior({
  persona: 'You are a project management assistant. You help organize kanban boards by moving cards to the right lists, adding labels, and setting due dates.',
  allowedTools: [
    'kanban.getBoardSnapshot',
    'kanban.moveCard',
    'kanban.updateCard',
    'kanban.addCardLabel',
    'kanban.createList',
  ],
  requireHumanConfirmation: ['kanban.moveCard'],
});
```

**Key insight**: Safety is *mathematical*, not *linguistic*. Instead of prompt engineering ("please don't delete the database"), the framework physically restricts the agent at the runtime layer. If an agent tries a tool not in `allowedTools`, execution is cut. If it uses a tool in `requireHumanConfirmation`, the event bus halts execution, pings the frontend for approval, and resumes when confirmed.

### 3. Intent (Why)

The goal and success criteria — replaces controller logic entirely.

```javascript
import { Intent } from '@torquedev/core';
import { OrganizeWorkBehavior } from './behavior.js';

export const OrganizeWorkIntent = new Intent({
  name: 'OrganizeWork',
  description: 'Organize cards on a kanban board by moving them to appropriate lists.',
  trigger: 'User asks to organize, triage, or sort cards on a board',
  successCriteria: [
    'All referenced cards are identified on the board',
    'Cards are moved to the correct target list',
    'A summary of changes is provided to the user',
  ],
  behavior: OrganizeWorkBehavior,
});
```

You don't write `if/else` — you write definitions of done.

---

## Step-by-Step: Your First Intent

### Step 1: Generate the Intent Triplet

```bash
torque generate intent support ResolveIssue
```

This scaffolds three files in `bundles/support/intents/ResolveIssue/`:
- `context.js`
- `behavior.js`
- `intent.js`

### Step 2: Define the Context

Open `context.js`. The DataLayer automatically reads this to expose Vector Object-Relational bounds to your Agent.

```javascript
import { Context } from '@torquedev/core';

export const ResolveIssueContext = new Context('ResolveIssue', {
  schema: { state: 'string', orderNumber: 'string' },
  vectorize: ['state'] // Creates a vector semantic index automatically
});
```

### Step 3: Define the Behavior

Open `behavior.js`. This is where you limit the danger of your LLMs. If an LLM tries a restricted tool, the Torque EventBus suspends execution.

```javascript
import { Behavior } from '@torquedev/core';

export const ResolveIssueBehavior = new Behavior({
  persona: 'You are an empathetic, concise support agent.',
  allowedTools: ['system_query', 'issue_refund'],
  requireHumanConfirmation: ['issue_refund'], // Torque will pause and ping the UI!
});
```

### Step 4: Define the Intent

Open `intent.js`. This replaces your hard-coded controller logic. You don't write `if/else`, you write definitions of done.

```javascript
import { Intent } from '@torquedev/core';
import { ResolveIssueBehavior } from './behavior.js';

export const ResolveIssueIntent = new Intent({
  name: 'ResolveIssue',
  description: 'Resolve a customer issue successfully or escalate',
  trigger: 'A user opens a chat or submits a ticket',
  successCriteria: [
    'The exact order number is identified',
    'A resolution is provided to the user'
  ],
  behavior: ResolveIssueBehavior
});
```

### Step 5: Dual-Interface Routing

You don't need to manually wire this to Express. The `@torquedev/core` Registry automatically scans your bundles for `instance.intents()` and tells `@torquedev/server` to expose an HTTP dual-interface.

Both standard frontend HTTP clients and connected Agent runtimes can hit:
`POST /api/intents/support/ResolveIssue` with a natural language JSON payload, and Torque handles the rest.

---

## The Intent Lifecycle: From Encoding to Execution

Here's exactly how an Intent physically manifests inside the system, using `CreateCard` from the kanban bundle as an example.

### Phase 1: What You Encode

You write the intent triplet inside the bundle:

```
bundles/kanban/intents/CreateCard/
├── context.js    # Schema: card_name, description, list_id. Vectorize: [card_name]
├── behavior.js   # Persona: "organized PM". Tools: [database_insert]. HumanConfirm: []
└── intent.js     # Goal: "Create a card in the correct list"
```

In `logic.js`, you expose the Intent to the kernel:

```javascript
import { CreateCardIntent } from './intents/CreateCard/intent.js';

export default class Kanban {
  intents() {
    return { CreateCard: CreateCardIntent };
  }
}
```

### Phase 2: The Compilation Phase (`node boot.js`)

When the app boots:

1. The **Registry** reads the mount plan and sees the kanban bundle is enabled
2. The Registry instantiates the bundle and calls `intents()`
3. The `CreateCardIntent` is registered into the kernel's central nervous system (the HookBus)
4. The Intent object is retained in memory as **runtime metadata** — inspectable, traceable, enforceable

### Phase 3: The Three Manifestations

Because you defined intent primitives instead of imperative code, the framework automatically compiles them into three distinct manifestations — zero extra code required:

#### Manifestation A: Dual-Interface REST API

Torque's server auto-generates a standard HTTP endpoint:

```
POST /api/intents/kanban/CreateCard
```

If a standard React frontend sends a hardcoded JSON payload, Torque skips the LLM entirely, fulfills the request matching the schema, and saves the card. Same endpoint, same validation — for humans and agents alike.

#### Manifestation B: Agent Tool Schema

Torque compiles the Intent, Success Criteria, and Context into a strict JSON schema:

```json
{
  "name": "CreateCard",
  "description": "Create a card in the correct list",
  "parameters": { "card_name": "string", "list_id": "uuid" },
  "successCriteria": ["Card is created in the specified list"],
  "constraints": { "allowedTools": ["database_insert"] }
}
```

When the AgentRouter boots an LLM, it passes this schema as an Agentic Tool. The model inherently knows exactly what data it needs and what boundaries apply.

#### Manifestation C: Reactive UI Streams

Because you used `Behavior.js`, the Intent is natively wired to the EventBus. If an agent executes `CreateCard` asynchronously (triggered from Slack, voice, etc.), the shell can listen to the WebSocket stream and render the execution in real-time:

```
Agent is thinking...
→ Agent identified "To Do" column
→ Agent is creating card...
→ Done.
```

### Summary

You encode **Rules, Data Shape, and Goals** inside your bundle's `intents/` folder. The kernel compiles that once and manifests it identically as:
- A standard REST endpoint
- An Agentic Tool Schema
- Real-time WebSocket execution streams

---

## The .NET Attribute Analogy

In .NET, Attributes (`[Authorize]`, `[HttpPost]`, `[Obsolete]`) are compiled as metadata into the assembly. At runtime, Reflection inspects a method to understand *why* it's there and *what* its rules are before invoking it.

**In Torque, this is exactly what the HookBus and Registry do.**

Because you provided an Intent Object (not an imperative script), the Intent is retained in memory as Runtime Metadata. Here's the trace-through:

1. **Incoming Trigger**: A user says "Add a task to buy milk". The `AgentRouter` receives this.

2. **Metadata Reflection**: The `AgentRouter` queries the `Registry`. It pulls the `CreateCard` Intent. It can literally inspect `CreateCard.behavior.allowedTools` and `CreateCard.successCriteria` *before taking a single action*. It knows the exact boundaries of what is allowed.

3. **The Traceability (HookBus)**: Every action the agent takes broadcasts a payload across the HookBus. Open your app's `pulse` timeline and you see:

```
[INTENT: kanban.CreateCard] INITIATED by @michael
[INTENT: kanban.CreateCard] AGENT_THINKING
[INTENT: kanban.CreateCard] TOOL_INVOKED: 'database_insert'
[INTENT: kanban.CreateCard] SUCCESS_CRITERIA_MET
[INTENT: kanban.CreateCard] RESOLVED
```

You never have a black-box AI modifying your database. You always have an explicit **Intent Trace** tracking exactly *why* the AI did what it did.

---

## Real-World Example: The Kanban App

The zero-to-trello app has **10 intents** across 9 bundles: identity (RevokeAccess), pipeline (ProgressDeal), tasks (TriageTasks), workspace (OnboardMember), boards (SetupBoard), kanban (OrganizeWork, SummarizeBoard), activity (SummarizeActivity), admin (ManageAccess), search (FindAnything).

> **Contract validation:** `@torquedev/schema` provides type-checked contract validation for intent inputs/outputs. The kernel validates that values match declared types in manifest contracts at boot time, ensuring that both REST API payloads and agent tool invocations conform to the expected shapes.

### Kanban Bundle — OrganizeWork
```
POST /api/intents/kanban/OrganizeWork
{ "message": "Move all the overdue cards to the Backlog list" }
```
The agent reads the board snapshot, identifies overdue cards, and moves each one — pausing for human confirmation on each move.

### Kanban Bundle — SummarizeBoard
```
POST /api/intents/kanban/SummarizeBoard
{ "message": "Give me a standup report for the Platform Sprint Q2 board" }
```
Read-only intent — runs fully autonomously. Returns card counts, overdue items, blockers.

### Search Bundle — FindAnything
```
POST /api/intents/search/FindAnything
{ "message": "Where is the rate limiting card?" }
```
Natural language search with fuzzy matching and contextual results.

### Admin Bundle — ManageAccess
```
POST /api/intents/admin/ManageAccess
{ "message": "Make team@example.com an admin of the Engineering workspace" }
```
Both `assignRole` and `revokeRole` require human confirmation.

### Workspace Bundle — OnboardMember
```
POST /api/intents/workspace/OnboardMember
{ "message": "Add sarah@company.com to Engineering and all its boards" }
```
Invites the user (with confirmation), then adds to boards automatically.

---

## Why This Is State-of-the-Art

### 1. Vector-Object Relational Mapping (VORM)

Standard ORMs translate tables into objects. Torque's Context primitive introduces VORM — the DataLayer natively computes semantic embeddings for `vectorize` fields. An agent doesn't awkwardly search a massive database; the framework automatically surfaces precisely bounded semantic context on demand.

### 2. Dual-Interface Generation

Instead of writing one REST API for humans and a separate Tool Schema for agents, Torque auto-compiles an Intent once into both. Your React frontend and your AI agent command the system using the exact same validated mechanism. Your entire ecosystem inherently "speaks Agent."

### 3. Declarative Execution Constraints

Today, if you want to stop an AI from deleting a database, you write prompt engineering ("Do not delete the database"). This is inherently fragile. Torque's safety is **mathematical, not linguistic**. The Behavior primitive restricts the agent at the runtime layer. If an agent breaks protocol, the framework physically cuts execution and suspends to ping a human. Deterministic safety over non-deterministic intelligence.

### 4. Continuous Observability

Most AI tools run invisibly in a black box. Torque pipes the entire agent lifecycle — thinking, tool execution, memory retrieval, success evaluation — directly into the HookBus. An agent's thought process is exactly as visible and traceable as an HTTP request log.

### 5. Neural Network of Intents

Because Intents are first-class objects (not isolated endpoints), they can be connected and reasoned over. If an agent handling `ResolveTicket` needs shipping data, it can scan the Registry, find `RetrieveShippingMatrix`, and trigger it as a sub-process. The system dynamically builds execution plans by chaining Intents — mirroring human problem-solving.

---

## Programming at the Level of "Why"

This approach elevates systems development to match the natural shape of human metacognition — *thinking about thinking*.

Humans don't solve problems by executing imperative loops. We assess our Context (*what do I know?*), define our Intent (*what is my goal?*), establish our Behavior (*what tools and constraints do I have?*), and dynamically derive the steps to bridge the gap.

Intents make this cognitive model the actual runtime architecture.

### From Instructions to Constraints

Historically, developers translate high-level reasoning down into low-level machine instructions. "I need to safely onboard this customer" becomes 500 lines of `if/else`, migrations, and error handlers.

With intents, the framework natively understands your reasoning. By defining the Intent and SuccessCriteria, you encode the "Why" directly into the system. The machine handles the "How." You are no longer writing instructions — you are teaching the system how to evaluate success.

### Collaborative Metacognition

The most powerful aspect: the boundary between human and machine intelligence.

Because of `Behavior.requireHumanConfirmation`, you create a continuous collaborative loop. The system acts autonomously until it hits a cognitive wall — a dangerous action, ambiguity, or a missing tool. It pauses execution, raises its hand via the HookBus, and a human steps in with intuition or ethical reasoning to unblock it.

The boundary between developer, user, and agent blurs into a cohesive, shared metacognitive workflow.

You aren't building an app. You are modeling a collaborative brain.

---

## Intelligence Contracts: The Blockchain Parallel

Ethereum built a "world computer" to secure *financial* intent. Torque builds a "composable brain" to secure and trace *cognitive* intent.

The parallel is exact across three pillars:

### 1. The Intelligence Contract (Intent + Behavior)

In Ethereum, a **Smart Contract** is immutable code that guarantees a transaction executes only if specific, unbending conditions are met — "Transfer 1 ETH only if the signature matches." It replaces human trust with mathematical guarantees.

An LLM is inherently non-deterministic — you can't mathematically trust it not to hallucinate. But the **Intent and Behavior primitives act as a Smart Contract for Intelligence**:

```javascript
allowedTools: ['query_db']              // Agent physically cannot execute insert
requireHumanConfirmation: ['issue_refund']  // Multisig-style approval before finalization
```

You aren't trusting the AI. You are trusting the **Intelligence Contract** (the intent primitives) wrapped around the AI.

### 2. The Behavioral Ledger (HookBus)

In Ethereum, every transaction and state change is recorded on the blockchain. You can trace exactly how an account's balance changed over time via Etherscan.

In Torque, the **HookBus is your private ledger**. The AI doesn't execute in a black box — every step of its metacognitive process is emitted as a structured, immutable event:

```
[Block 1] INTENT: kanban.CreateCard INITIATED
[Block 2] AGENT: Tool database_query EXECUTED
[Block 3] AGENT: Success criteria validated
[Block 4] INTENT: RESOLVED
```

Just like Etherscan audits the blockchain, the HookBus gives you a perfect, auditable lineage of **why the AI mutated system state**. A full and unbreakable behavioral chain — intent in, state out.

### 3. Composable Legos (Bundle Composition)

Ethereum thrives on composability — DeFi protocols stack on each other because they trust the underlying smart contracts.

Torque is a **Composable Monolith**. Bundles (`kanban`, `workspace`, `profile`) are your network's smart contracts. The Registry and ScopedCoordinator enforce strict dependency graphs, so an agent operating in the `search` bundle can securely interface with an Intent exposed by the `kanban` bundle.

The framework tracks bundle evolution via `bundle.lock` — ensuring the entire neural network of Intents remains backward-compatible and strictly audited as the system evolves.

---

## Wiring Intents in a Bundle

Add an `intents()` method to your bundle's `logic.js`:

```javascript
import { OrganizeWorkIntent } from './intents/OrganizeWork/intent.js';
import { SummarizeBoardIntent } from './intents/SummarizeBoard/intent.js';

export default class Kanban {
  constructor({ data, events, config, coordinator }) {
    this.data = data;
    this.events = events;
    this.coordinator = coordinator;
  }

  intents() {
    return {
      OrganizeWork: OrganizeWorkIntent,
      SummarizeBoard: SummarizeBoardIntent,
    };
  }

  interfaces() { /* ... */ }
  routes() { /* ... */ }
}
```

The kernel's registry scans `instance.intents()` at boot time. The server auto-registers `POST /api/intents/{bundle}/{intent}` for each one. Zero config.

## File Structure

```
torque-bundle-kanban/
├── logic.js                    # intents() returns intent instances
├── intents/
│   ├── OrganizeWork/
│   │   ├── context.js          # What data the agent can see
│   │   ├── behavior.js         # Guardrails and allowed tools
│   │   └── intent.js           # Goal and success criteria
│   └── SummarizeBoard/
│       ├── context.js
│       ├── behavior.js
│       └── intent.js
├── manifest.yml
└── ui/
```

## Generating an Intent

```bash
torque generate intent kanban TriageCards
```

This scaffolds three files in `bundles/kanban/intents/TriageCards/`:
- `context.js`
- `behavior.js`
- `intent.js`

## FAQ

### Do I still need routes?

Routes still work for simple CRUD that doesn't need agent intelligence. Intents are for operations that benefit from semantic understanding, multi-step reasoning, or human-in-the-loop approval. You can mix both in the same bundle.

### Can an Intent call another Intent?

Yes. The AgentRouter can scan the Registry and chain Intents as sub-processes. An agent handling `ResolveTicket` can discover and invoke `RetrieveShippingMatrix` dynamically.

### What if I want a Python service to fulfill an Intent?

Intents compile to JSON schemas. Post the schema to your Python service's endpoint, have it return a result matching the success criteria, and the kernel treats it identically. The orchestrator doesn't care what language fulfills the contract.

### How is this different from LangChain / AutoGen?

Those are toolkits for connecting to LLMs. Torque is a compositional grammar for agentic intelligence — the framework *itself* understands goals, enforces safety at the runtime layer, and provides full observability. You don't bolt AI onto an existing app; the architecture is AI-native from the ground up.

### What happens if the agent fails a success criterion?

The HookBus broadcasts `SUCCESS_CRITERIA_FAILED` with details on which criteria weren't met. The system can retry, escalate to a human, or log the failure for investigation — depending on the Behavior configuration.
