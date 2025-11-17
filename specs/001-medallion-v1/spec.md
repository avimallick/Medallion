# Feature Specification: Medallion Library v1

**Feature Branch**: `001-medallion-v1`  
**Created**: 2025-11-17  
**Status**: Draft  
**Input**: User description: "Create a high-level product specification for the Medallion library v1 with schema, store interface, SQLite implementation, LLM helpers, and session helpers"

## Problem & Goals

### Problem Statement

Current LLM agent frameworks (LangChain, LangGraph, etc.) treat knowledge stores as static data and conversation & reasoning as ephemeral per-session. This leads to:

1. **Non-deterministic re-inference**: Restarting a session forces the model to re-interpret the same graph/docs from scratch, with "understanding" and decisions varying from run to run.

2. **Loss of progress**: Multi-day/multi-session work lives in raw chat logs or ad-hoc summaries, not as first-class state. New sessions don't know what's already been resolved.

3. **No canonical "project state"**: Agents can't easily tell what's already decided, what's stable ground truth, and what's still open/TODO.

### Goals

Provide a reusable, framework-agnostic **semantic checkpointing layer** that lets LLM agents resume work from canonical, structured "savepoints" attached to a knowledge graph or project state. Medallions capture what has been understood, decided, and left open about a scope (e.g., repo, project, customer, document subtree), enabling agents to "load save file" and continue from previous sessions.

---

## In-Scope Features (v1)

### Core Components

1. **Medallion Schema**: Structured JSON data model encoding:
   - Scope (graph_nodes, tags)
   - Summary (high-level overview, subsystems status)
   - Decisions (canonical statements with rationale and confidence)
   - Open questions (blocked items, priorities)
   - Affordances (recommended entry points, avoid repeating, invariants)
   - Metadata (version, timestamps, model info, status)

2. **MedallionStore Interface**: Abstract interface defining:
   - `create(medallion)`: Persist a new medallion
   - `update(medallion)`: Update an existing medallion
   - `getById(id)`: Fetch medallion by exact ID
   - `getLatestForScope(scope, limit)`: Fetch latest medallions for a scope

3. **SQLiteMedallionStore Implementation**: Concrete SQLite-backed store implementing MedallionStore interface with schema supporting all medallion fields and scope queries.

4. **MedallionLLM Interface**: LLM orchestration helpers:
   - `generate(scope, evidence)`: Build a new medallion from evidence (session summary, transcripts, artefacts)
   - `update(existing, new_evidence)`: Merge new evidence into existing medallion

5. **Session Helpers**: Integration functions:
   - `load_medallions_for_scope(store, scope, options)`: Retrieve relevant medallions for session start
   - `checkpoint_session(store, llm, scope, evidence)`: Create or update medallion at session end/milestone

---

## Out-of-Scope (Future Work)

The following features are explicitly **not** included in v1:

- **Vector search**: Semantic/embedding-based retrieval over medallion content (`searchByText` is deferred)
- **UI/Dashboard**: Complex user interfaces for browsing or editing medallions (CLI and logs only for v1)
- **Distributed sync/CRDTs**: Multi-cluster synchronization or conflict resolution mechanisms
- **Framework-specific integrations**: Deep coupling to LangChain/LangGraph internals (lightweight adapters/examples only)

---

## Users & Personas

### Persona 1: Agent Framework Developer

**Who**: Developer integrating Medallion into an existing agent loop (LangChain, LangGraph, or custom framework).

**Needs**: 
- Clean, framework-agnostic API to plug into agent lifecycle
- Ability to load medallions at session start
- Ability to create/update medallions at session end or milestones
- Deterministic, reproducible checkpoint behavior

**Goals**: Give their agent framework continuity between sessions without tight coupling to Medallion internals.

### Persona 2: Power User / Engineer

**Who**: Engineer using an LLM agent to work on a large codebase or project.

**Needs**:
- Agent "remembers where we left off" in a stable, structured way
- Persistent state that survives session restarts
- Ability to inspect medallions (human-readable JSON)
- Confidence that decisions and understanding are preserved

**Goals**: Avoid re-discovery in every session and maintain consistent project state across multiple agent interactions.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Checkpoint Creation (Priority: P1)

As a user, after a long session where the agent explored a repo and made decisions, I want the system to create a medallion that captures the current state of understanding, so that future sessions can resume quickly and consistently.

**Why this priority**: Checkpoint creation is the foundation capability. Without it, no medallions exist and the system provides no value. This is the minimum viable product (MVP).

**Independent Test**: Can be fully tested by defining a scope, calling `checkpoint_session` with mocked evidence, and verifying a valid medallion is created and persisted in the store with all required schema fields.

**Acceptance Scenarios**:

1. **Given** an initialized MedallionStore and MedallionLLM, **When** a user calls `checkpoint_session(store, llm, scope, evidence)` with a new scope, **Then** a new medallion is generated via LLM, persisted to the store, and returned with valid schema fields (meta, scope, summary, decisions, open_questions, affordances).

2. **Given** a scope with graph_nodes and tags, **When** a checkpoint is created, **Then** the medallion's scope field matches the input scope exactly.

3. **Given** evidence containing session_summary, transcripts, and artefacts, **When** a checkpoint is created, **Then** the LLM generates a medallion that incorporates all evidence into the summary, decisions, and open_questions fields.

4. **Given** a checkpoint is created, **When** the medallion is retrieved from the store, **Then** all fields are preserved and the medallion is human-inspectable (valid JSON).

---

### User Story 2 - Resume from Checkpoint (Priority: P2)

As a user starting a new session on the same project, I want the agent to automatically load the most relevant medallion(s) for that project, so that it does not re-discover everything from scratch and stays aligned with past decisions.

**Why this priority**: Loading checkpoints is the second critical capability. While checkpoint creation enables state capture, loading enables state reuse, which is the primary value proposition.

**Independent Test**: Can be fully tested by creating a medallion with a specific scope, then calling `load_medallions_for_scope(store, scope)` and verifying the previously created medallion is retrieved and returned.

**Acceptance Scenarios**:

1. **Given** a medallion exists in the store for scope `{"graph_nodes": ["repo:muse"], "tags": ["project_state"]}`, **When** `load_medallions_for_scope(store, scope, {limit: 3})` is called with the same scope, **Then** the medallion is returned in the results list.

2. **Given** multiple medallions exist for the same scope with different timestamps, **When** `load_medallions_for_scope` is called, **Then** medallions are returned in descending order by `updated_at` (latest first) up to the limit.

3. **Given** a scope that partially matches (e.g., requesting `["repo:muse"]` when medallion has `["repo:muse", "module:cli"]`), **When** `load_medallions_for_scope` is called, **Then** the matching medallion is returned if the requested nodes are a subset of the stored nodes.

4. **Given** no medallions exist for a scope, **When** `load_medallions_for_scope` is called, **Then** an empty list is returned (not an error).

---

### User Story 3 - Update Checkpoint (Priority: P2)

As the agent discovers new information or changes prior decisions, I want it to update the existing medallion rather than create conflicting state, so that there is a canonical "project state" at any given time.

**Why this priority**: Updates prevent state duplication and ensure there's a single source of truth. This is essential for maintaining consistency across sessions.

**Independent Test**: Can be fully tested by creating a medallion, calling `checkpoint_session` again with new evidence for the same scope, and verifying the existing medallion is updated (not duplicated) with merged information.

**Acceptance Scenarios**:

1. **Given** a medallion exists in the store for a scope, **When** `checkpoint_session` is called again with the same scope and new evidence, **Then** the LLM's `update` method is called (not `generate`), and the existing medallion is updated in the store with a new `updated_at` timestamp.

2. **Given** an existing medallion with decision "D-001: Use Python 3.11+", **When** new evidence contradicts this decision, **Then** the updated medallion reflects the new decision, and the old decision is marked obsolete or removed (per LLM update logic).

3. **Given** an existing medallion with open question "Q-003: Should we use async?", **When** new evidence resolves this question, **Then** the question is removed from `open_questions` or marked resolved, and any related decision is added to `decisions`.

4. **Given** `checkpoint_session` updates an existing medallion, **When** the medallion is retrieved by ID, **Then** both the original `created_at` and new `updated_at` timestamps are preserved, and `meta.status` remains "active".

---

### User Story 4 - Graph-Anchored State (Priority: P3)

As a framework dev with a knowledge graph, I want medallions to be associated with graph nodes (e.g., repo, component, customer), so that agents can fetch state for a specific part of the graph.

**Why this priority**: Graph anchoring enables scoped checkpointing, allowing different parts of a large system to maintain independent state. While valuable, this can be satisfied by the scope filtering in User Story 2, so it's lower priority.

**Independent Test**: Can be fully tested by creating medallions with different graph_node combinations, then querying by specific node subsets and verifying only relevant medallions are returned.

**Acceptance Scenarios**:

1. **Given** medallions exist with scopes `["repo:muse"]`, `["repo:muse", "module:cli"]`, and `["repo:other"]`, **When** `load_medallions_for_scope` is called with scope `{"graph_nodes": ["repo:muse"], "tags": []}`, **Then** both muse-related medallions are returned (exact and subset matches).

2. **Given** a medallion with scope `{"graph_nodes": ["repo:muse", "module:llm_router"], "tags": ["project_state"]}`, **When** querying by tags only `{"graph_nodes": [], "tags": ["project_state"]}`, **Then** the medallion is returned if tag matching is supported, or returns empty if graph_nodes are required.

3. **Given** multiple graph nodes in a scope, **When** a medallion is created, **Then** all nodes are stored and can be used for retrieval queries involving any subset.

---

### Edge Cases

- What happens when `checkpoint_session` is called with evidence that contains no meaningful content (empty session_summary)?
  - The LLM should still generate a minimal medallion with empty or placeholder fields, or return an error if evidence is truly invalid.

- How does the system handle schema version mismatches when loading old medallions?
  - The store should preserve old schema versions, and the application layer should handle migration or validation as needed (migration logic deferred to implementation).

- What happens when two sessions simultaneously try to update the same medallion?
  - The last-write-wins approach is acceptable for v1 (no distributed locking required per out-of-scope).

- How does the system handle LLM failures during medallion generation or update?
  - Errors should be propagated clearly with context (scope, operation type), and no partial medallion state should be persisted.

- What happens when `load_medallions_for_scope` is called with an empty scope (`{"graph_nodes": [], "tags": []}`)?
  - System should return empty list or all medallions based on implementation decision (documented behavior required).

- How are invalid medallions (schema violations) handled during store operations?
  - Store operations should validate schema before persistence and raise clear errors on violations.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Medallion data model with strict schema including: meta (id, schema_version, timestamps, status), scope (graph_nodes, tags), summary (high_level, subsystems), decisions (id, statement, rationale, confidence), open_questions (id, question, blocked_on, priority), and affordances (recommended_entry_points, avoid_repeating, invariants).

- **FR-002**: System MUST provide a MedallionStore abstract interface with methods: `create(medallion)`, `update(medallion)`, `getById(id)`, and `getLatestForScope(scope, limit)`.

- **FR-003**: System MUST provide a SQLiteMedallionStore implementation that persists medallions to SQLite with schema supporting all medallion fields, indexes for scope queries, and proper handling of JSON content.

- **FR-004**: System MUST provide a MedallionLLM interface with methods `generate(scope, evidence)` that creates a new medallion from evidence, and `update(existing, new_evidence)` that merges new evidence into an existing medallion.

- **FR-005**: System MUST provide a `load_medallions_for_scope(store, scope, options)` function that retrieves the latest medallions matching the given scope, ordered by `updated_at` descending, up to the specified limit.

- **FR-006**: System MUST provide a `checkpoint_session(store, llm, scope, evidence)` function that checks for existing active medallions for the scope, calls `llm.generate()` if none exist, or `llm.update()` if one exists, then persists the result via the store.

- **FR-007**: Medallions MUST be JSON-serializable and human-inspectable while conforming to the strict schema.

- **FR-008**: MedallionStore operations MUST validate medallion schema before persistence and raise clear errors on violations.

- **FR-009**: `checkpoint_session` MUST preserve the original `created_at` timestamp when updating an existing medallion and set a new `updated_at` timestamp.

- **FR-010**: `getLatestForScope` MUST support querying by graph_nodes (exact match or subset) and tags, returning results ordered by `updated_at` descending.

- **FR-011**: MedallionLLM `generate()` and `update()` MUST return medallions with valid JSON conforming to the schema in normal cases (LLM failures are error cases).

- **FR-012**: System MUST handle missing medallions gracefully: `getById` returns null/None for non-existent IDs, `load_medallions_for_scope` returns empty list for non-matching scopes.

### Key Entities

- **Medallion**: The core entity representing a semantic checkpoint. Contains meta (metadata), scope (graph_nodes, tags), summary (high-level and subsystem details), decisions (canonical choices made), open_questions (unresolved items), and affordances (usage guidance). Stored as JSON in the database with indexed fields for querying.

- **MedallionScope**: Defines what a medallion applies to. Contains `graph_nodes` (string array of entity IDs like "repo:muse", "module:cli") and `tags` (string array for categorization like "project_state", "refactor_sprint_1"). Used for querying and scoping state.

- **Evidence**: Input data for medallion generation/update. Contains `session_summary` (string description of session events), `transcripts` (optional array of conversation segments), and `artefacts` (optional structured data like file diffs, test results).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can install the medallion module, initialize a Medallion store (SQLite file), and call `checkpoint_session` with mocked evidence to create and persist a medallion with all required schema fields (meta, scope, summary, decisions, open_questions, affordances).

- **SC-002**: A developer can start a new script run, call `load_medallions_for_scope(scope)`, and retrieve a previously created medallion for that scope, with all fields preserved and human-readable.

- **SC-003**: A developer can call `checkpoint_session` again with new evidence for the same scope and see the existing medallion updated (not duplicated), with `updated_at` timestamp changed and `created_at` preserved.

- **SC-004**: LLM responses from `generate()` and `update()` are valid JSON and conform to the Medallion schema in 95%+ of normal cases (non-error scenarios).

- **SC-005**: Unit tests cover core behaviors: schema validation, store operations (create/update/get/getLatestForScope), and session helpers (load_medallions_for_scope, checkpoint_session with mocked LLM), achieving 90%+ code coverage on store and session modules per constitution.

- **SC-006**: A developer can integrate Medallion into an agent framework by calling `load_medallions_for_scope` at session start and `checkpoint_session` at session end, with minimal framework-specific code (lightweight wrapper functions only).
