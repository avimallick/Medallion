# Medallion: Semantic Checkpointing Layer for LLM Agents

## 1. Overview

**Product Name:** Medallion

**Goal:** Provide a reusable, framework-agnostic **semantic checkpointing layer** that lets LLM agents resume work from **canonical, structured "savepoints"** attached to a knowledge graph or project state, instead of re-deriving context from scratch each session.

Medallions:
* Capture **what has been understood, decided, and left open** about a scope (e.g., repo, project, customer, document subtree).
* Are **structured, machine-first** objects (JSON-like), but still human-inspectable.
* Are **linked to the knowledge graph** and to prior sessions/runs.
* Can be retrieved and injected into new sessions so that agents can "load save file" and continue.

This is a standalone module that can be integrated into LangChain, LangGraph, or any custom agent framework.

---

## 2. Problem Statement

Current LLM agent frameworks (LangChain, LangGraph, etc.) treat:
* Knowledge stores (RAG, graphs) as **static data**.
* Conversation & reasoning as **ephemeral per-session**.

Problems:

1. **Non-deterministic re-inference**
   Clearing/restarting a session forces the model to re-interpret the same graph/docs from scratch. The "understanding" and decisions vary from run to run.

2. **Loss of progress**
   Multi-day/multi-session work lives in raw chat logs or ad-hoc summaries, not as **first-class state**. New sessions don't know what's already been resolved.

3. **No canonical "project state"**
   Agents can't easily tell what's:
   * Already decided,
   * Stable ground truth,
   * Still open / TODO.

Medallion solves this by introducing **explicit, versioned semantic checkpoints** attached to the graph and project scopes.

---

## 3. Objectives & Non-Objectives

### 3.1 Objectives

* Provide a **Medallion data model** that encodes:
  * Scope (what it applies to),
  * Summaries,
  * Decisions,
  * Open questions,
  * Affordances (how agents should use it),
  * Metadata (version, timestamps, model info).

* Implement a **Medallion Store** with:
  * Create / update / fetch APIs.
  * Storage in a simple backend (TinyDB / SQLite / JSON file) for v0.
  * Optional vector search over medallion content for best match.

* Implement **LLM orchestration helpers**:
  * generate_medallion – build a medallion from evidence (graph nodes + transcripts + artefacts).
  * update_medallion – merge new evidence into an existing medallion.
  * load_medallions_for_scope – retrieve relevant medallions for a new session.

* Provide **integration hooks**:
  * Simple wrapper functions that agents can call at:
    * Session start: auto-load medallions.
    * Session end or milestone: auto-create/update medallion.

### 3.2 Non-Objectives (v1)

* No distributed sync/CRDTs across multiple clusters.
* No complex UI/dashboard for medallions (CLI + logs only is fine).
* No hard coupling to LangChain/LangGraph internals; integration can be via lightweight adapters or examples.

---

## 4. Personas & User Stories

### 4.1 Personas

* **Agent Framework Developer** – wants to plug Medallion into an existing agent loop to give it continuity between sessions.
* **Power User / Engineer** – uses an LLM agent to work on a large codebase or project and wants the agent to "remember where we left off" in a stable, structured way.

### 4.2 Key User Stories

1. **Checkpoint creation**
   > As a user, after a long session where the agent explored a repo and made decisions,
   > I want the system to create a medallion that captures the current state of understanding,
   > so that future sessions can resume quickly and consistently.

2. **Resuming from a checkpoint**
   > As a user starting a new session on the same project,
   > I want the agent to automatically load the most relevant medallion(s) for that project,
   > so that it does not re-discover everything from scratch and stays aligned with past decisions.

3. **Updating a checkpoint**
   > As the agent discovers new information or changes prior decisions,
   > I want it to update the existing medallion rather than create conflicting state,
   > so that there is a canonical "project state" at any given time.

4. **Graph-anchored state**
   > As a framework dev with a knowledge graph,
   > I want medallions to be associated with graph nodes (e.g., repo, component, customer),
   > so that agents can fetch state for a specific part of the graph.

---

## 5. High-Level Architecture

### 5.1 Components

1. **Medallion Schema** (pure data model)

2. **Medallion Store** (persistence + retrieval):
   * v0: SQLite or TinyDB backend.
   * Optional vector index (e.g., sentence-transformers embedding via an LLM provider or local model).

3. **LLM Orchestrator Helpers**
   * generate_medallion(schema, evidence) -> Medallion
   * update_medallion(existing_medallion, new_evidence) -> Medallion
   * summarise_for_prompt(medallion) -> prompt-snippet

4. **Integration Layer**
   * load_medallions_for_scope(scope) -> List[Medallion]
   * Hooks for:
     * on_session_start(scope)
     * on_session_end(scope, evidence)

---

## 6. Data Model: Medallion Schema (v0)

Use JSON-serializable objects; language: TypeScript-like or Python dataclasses.

### 6.1 Core Schema

```ts
// Pseudo-TypeScript; equivalent dataclasses can be used in Python.

type MedallionScope = {
  // Arbitrary string IDs that link this medallion to graph nodes / entities.
  graph_nodes: string[]; // e.g. ["repo:muse", "module:cli", "service:llm-router"]
  tags: string[];        // e.g. ["project_state", "refactor_sprint_1"]
};

type MedallionDecision = {
  id: string;           // e.g. "D-001"
  statement: string;    // Canonical decision text.
  rationale: string;    // Short explanation why.
  confidence: number;   // 0.0–1.0.
};

type MedallionOpenQuestion = {
  id: string;          // e.g. "Q-003"
  question: string;
  blocked_on: string[]; // e.g. ["benchmark", "team_input"]
  priority: "low" | "medium" | "high";
};

type MedallionAffordances = {
  recommended_entry_points: string[]; // e.g. "Start from module:llm-router".
  avoid_repeating: string[];          // e.g. "Do not re-run full repo scan".
  invariants?: string[];              // Optional: rules agents must obey.
};

type MedallionSummary = {
  high_level: string;  // <= 300 tokens.
  subsystems: {
    name: string;
    status: "unknown" | "stable" | "in_progress" | "deprecated";
    notes: string;
  }[];
};

type MedallionMeta = {
  medallion_id: string;       // Unique identifier.
  schema_version: string;     // e.g. "medallion.v1".
  model: string;              // Model used to generate/update.
  created_at: string;         // ISO 8601.
  updated_at: string;         // ISO 8601.
  knowledge_min_ts?: string;  // The earliest data timestamp covered.
  knowledge_max_ts?: string;  // The latest data timestamp covered (e.g. repo commit time).
  status: "active" | "stale" | "superseded";
};

type Medallion = {
  meta: MedallionMeta;
  scope: MedallionScope;
  summary: MedallionSummary;
  decisions: MedallionDecision[];
  open_questions: MedallionOpenQuestion[];
  affordances: MedallionAffordances;
};
```

### 6.2 Storage Schema (DB)

**Table: medallions**

* id (PK, string)
* content_json (TEXT / JSON)
* created_at (TEXT)
* updated_at (TEXT)
* status (TEXT)
* scope_graph_nodes (TEXT; JSON array)
* scope_tags (TEXT; JSON array)
* knowledge_min_ts (TEXT, nullable)
* knowledge_max_ts (TEXT, nullable)
* embedding (BLOB or separate table) – optional v0: can be skipped or implemented later.

---

## 7. Core APIs (for Cursor to Implement)

Design as a small library module, e.g. `medallion/`.

### 7.1 Public Interface (Conceptual)

#### 7.1.1 Medallion Store

```ts
interface MedallionStore {
  create(medallion: Medallion): Promise<void>;
  update(medallion: Medallion): Promise<void>;

  // Fetch by exact ID.
  getById(id: string): Promise<Medallion | null>;

  // Fetch latest medallion(s) for a given scope.
  getLatestForScope(scope: MedallionScope, limit?: number): Promise<Medallion[]>;

  // Optional: vector-based retrieval using content.
  searchByText(scope: MedallionScope, query: string, limit?: number): Promise<Medallion[]>;
}
```

The default implementation: `SQLiteMedallionStore` (or `TinyDBMedallionStore`).

#### 7.1.2 LLM-Oriented Functions

```ts
type Evidence = {
  // High-level description of what happened this session.
  session_summary: string;
  // Optional: list of important messages / logs / planner steps.
  transcripts?: string[];
  // Optional: additional structured info (e.g. file diffs, test results).
  artefacts?: Record<string, any>;
};

interface MedallionLLM {
  generate(scope: MedallionScope, evidence: Evidence): Promise<Medallion>;
  update(existing: Medallion, newEvidence: Evidence): Promise<Medallion>;
}
```

Implementation detail for Cursor:
* These will call an LLM with a **strict JSON schema prompt** to ensure Medallions follow the schema.

#### 7.1.3 Session Helpers

```ts
// Called at the start of a session.
async function loadMedallionsForScope(
  store: MedallionStore,
  scope: MedallionScope,
  options?: { limit?: number }
): Promise<Medallion[]>;

// Called at the end of a session or milestone.
async function checkpointSession(
  store: MedallionStore,
  llm: MedallionLLM,
  scope: MedallionScope,
  evidence: Evidence
): Promise<Medallion>;
```

**Behavior:**
* checkpointSession:
  * Checks if a recent active medallion exists for this scope.
  * If none: `llm.generate(...)` → `store.create(...)`.
  * If exists: `llm.update(existing, evidence)` → `store.update(...)`.

---

## 8. Prompt Design (for Cursor's LLM Integration)

### 8.1 Generate Medallion Prompt Skeleton

System prompt example:
> You are a strict state summarizer.
> Your job is to create a structured semantic checkpoint called a "Medallion".
> It describes the current canonical understanding, decisions, open questions, and affordances for agents.
> You MUST respond with valid JSON matching the given schema and no extra text.

User prompt example:
* Inputs: scope, evidence.

```jsonc
{
  "task": "generate_medallion",
  "schema_version": "medallion.v1",
  "scope": {
    "graph_nodes": ["repo:muse", "module:llm_router"],
    "tags": ["project_state", "refactor_sprint_1"]
  },
  "evidence": {
    "session_summary": "Short <500 token summary of what happened...",
    "transcripts": [
      "Key conversation segments or planner steps...",
      "..."
    ],
    "artefacts": {
      "test_results": "...",
      "files_touched": ["llm_router.py", "config.yaml"]
    }
  }
}
```

The assistant must output a Medallion JSON object.

### 8.2 Update Medallion Prompt Skeleton

System prompt:
> You are updating an existing Medallion state object using new evidence.
> Modify the given JSON object with minimal changes.
> Only change fields that are contradicted or extended by new evidence.
> Preserve IDs of existing decisions and questions unless they are obsolete, in which case mark them clearly or remove them.
> Respond with valid JSON only.

User prompt contains:
* Old medallion JSON.
* New evidence.

---

## 9. Example Flow

### 9.1 Session Start

1. User opens "Project Muse" in the agent UI.
2. Backend defines scope:

```json
{
  "graph_nodes": ["repo:muse"],
  "tags": ["project_state"]
}
```

3. `loadMedallionsForScope(store, scope, { limit: 3 })` returns 1–3 latest medallions.
4. Agent system prompt includes:
   > You are resuming work on Project Muse.
   > These objects describe the current canonical understanding and decisions. Treat them as ground truth unless explicitly overridden:
   > [MEDALLION_JSON_1, MEDALLION_JSON_2, ...]
5. Agent plans tasks using that state.

### 9.2 Session End / Checkpoint

1. On significant milestone or at session end:
   * The agent generates a `session_summary` and collects evidence.
2. The framework calls:

```ts
await checkpointSession(store, medallionLLM, scope, evidence);
```

3. LLM either creates or updates a medallion.
4. Store persists it.

---

## 10. Non-Functional Requirements

* **Language / Runtime (for v0 prototype):**
  * Prefer **TypeScript/Node** or **Python** – choose one and keep everything modular.

* **Testability:**
  * Unit tests for:
    * Medallion schema validation.
    * Store operations (create/update/get/search).
    * LLM helper wrapper (mock LLM responses).

* **Observability:**
  * Logging of:
    * Medallion creation/update events.
    * Scope used for retrieval.

* **Configurability:**
  * Pluggable LLM client.
  * Pluggable embedding model (for search).
  * Config-driven DB path (e.g., `medallion.db`).

---

## 11. Initial File/Module Layout (Suggestion for Cursor)

Example (TypeScript/Node):

```
medallion/
  src/
    index.ts
    types.ts           # Medallion schema types
    store/
      MedallionStore.ts
      SQLiteMedallionStore.ts
    llm/
      MedallionLLM.ts
      prompts.ts
    session/
      checkpoint.ts    # loadMedallionsForScope, checkpointSession
  test/
    store.test.ts
    llm.test.ts
  docs/
    medallion_prd.md   # this document
  package.json
  tsconfig.json
  README.md
```

Or Python equivalent:

```
medallion/
  medallion/
    __init__.py
    types.py
    store.py
    sqlite_store.py
    llm.py
    session.py
  tests/
    test_store.py
    test_llm.py
  docs/
    medallion_prd.md
  pyproject.toml
  README.md
```

---

## 12. Milestones / Phases

### Phase 1 – Core Library (No Embeddings)

* Implement:
  * Medallion types/schema.
  * SQLiteMedallionStore (or TinyDB).
  * loadMedallionsForScope (simple filter by graph_nodes + tags).
  * checkpointSession with stubbed LLM (pass-through in tests).
* Add unit tests.

### Phase 2 – LLM Integration

* Add MedallionLLM with:
  * generate() / update() using structured JSON prompts.
* Basic CLI or scripts:
  * `medallion generate-from-log` (manual test).
  * `medallion list --scope repo:muse`.

### Phase 3 – Vector Search (Optional)

* Add embedding support to index medallions.
* Implement searchByText.

---

## 13. Acceptance Criteria (v1)

* A developer can:
  1. Install the medallion module.
  2. Initialise a Medallion store (e.g. SQLite file).
  3. From a script:
     * Define a scope,
     * Call checkpointSession with mocked evidence,
     * See a Medallion created and persisted.
  4. Start a new script run, call `loadMedallionsForScope(scope)`, and get that Medallion back.
  5. Call checkpointSession again with new evidence and see the medallion updated (not duplicated).

* LLM responses are **valid JSON** and conform to schema in normal cases.

* Unit tests cover core behaviors.

---
