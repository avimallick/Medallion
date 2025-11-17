# Tasks: Medallion Library v1

**Input**: Design documents from `/specs/001-medallion-v1/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per constitution (90%+ coverage on store + session modules).

**Organization**: Tasks are grouped by module and user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Package**: `medallion/` at repository root
- **Tests**: `tests/` at repository root (mirroring module structure)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Project initialization, package structure, and tooling configuration

- [ ] T001 Create medallion package directory structure: `medallion/` and `tests/unit/`, `tests/integration/`, `tests/contract/`

- [ ] T002 Initialize Python project: Create `pyproject.toml` with Python 3.11+ requirement, pydantic>=2.0, pytest>=7.0, mypy>=1.0 dependencies

- [ ] T003 [P] Configure linting: Add ruff or black + flake8 configuration to pyproject.toml

- [ ] T004 [P] Configure type checking: Add mypy configuration to pyproject.toml with strict mode enabled

- [ ] T005 [P] Setup pytest configuration: Create pytest.ini or pyproject.toml pytest settings for coverage reporting (90%+ target on store + session modules)

- [ ] T006 Create package `__init__.py` stub in medallion/__init__.py (will be populated in later phases)

---

## Phase 2: Foundational - Types Module

**Purpose**: Core data models that ALL user stories depend on. MUST complete before any other implementation.

**⚠️ CRITICAL**: No other modules can be implemented until types are complete.

### Types Implementation

- [ ] T007 [P] [US1] Create MedallionScope Pydantic model in medallion/types.py with graph_nodes (List[str]) and tags (List[str]) fields

- [ ] T008 [P] [US1] Create MedallionDecision Pydantic model in medallion/types.py with id (str), statement (str), rationale (str), confidence (float 0.0-1.0) with validator

- [ ] T009 [P] [US1] Create MedallionOpenQuestion Pydantic model in medallion/types.py with id (str), question (str), blocked_on (List[str]), priority (Literal["low","medium","high"])

- [ ] T010 [P] [US1] Create MedallionAffordances Pydantic model in medallion/types.py with recommended_entry_points (List[str]), avoid_repeating (List[str]), invariants (Optional[List[str]])

- [ ] T011 [P] [US1] Create Subsystem Pydantic model in medallion/types.py with name (str), status (Literal["unknown","stable","in_progress","deprecated"]), notes (str)

- [ ] T012 [P] [US1] Create MedallionSummary Pydantic model in medallion/types.py with high_level (str, max_length=300), subsystems (List[Subsystem])

- [ ] T013 [P] [US1] Create MedallionMeta Pydantic model in medallion/types.py with medallion_id (str), schema_version (str, default="medallion.v1"), model (str), created_at (datetime), updated_at (datetime), knowledge_min_ts (Optional[datetime]), knowledge_max_ts (Optional[datetime]), status (Literal["active","stale","superseded"], default="active") and updated_at >= created_at validator

- [ ] T014 [US1] Create Medallion Pydantic model in medallion/types.py composing meta (MedallionMeta), scope (MedallionScope), summary (MedallionSummary), decisions (List[MedallionDecision]), open_questions (List[MedallionOpenQuestion]), affordances (MedallionAffordances)

- [ ] T015 [US1] Create Evidence Pydantic model in medallion/types.py with session_summary (str), transcripts (Optional[List[str]]), artefacts (Optional[Dict[str, Any]])

- [ ] T016 [US1] Create custom exceptions in medallion/types.py: MedallionError (base), SchemaValidationError, StoreError, LLMError

- [ ] T017 [P] [US1] Add JSON serialization helpers to Medallion model: model_dump_json() usage examples and model_validate_json() helper method

### Types Tests

- [ ] T018 [P] [US1] Write unit tests for MedallionScope validation in tests/unit/test_types.py

- [ ] T019 [P] [US1] Write unit tests for MedallionDecision confidence validation (0.0-1.0) in tests/unit/test_types.py

- [ ] T020 [P] [US1] Write unit tests for MedallionMeta timestamp validation (updated_at >= created_at) in tests/unit/test_types.py

- [ ] T021 [P] [US1] Write unit tests for Medallion JSON serialization/deserialization round-trip in tests/unit/test_types.py

- [ ] T022 [P] [US1] Write contract tests for Medallion schema validation against PRD schema in tests/contract/test_schema_contract.py

**Checkpoint**: Types module complete - all data models defined, validated, and tested. Ready for store implementation.

---

## Phase 3: Foundational - Store Interface

**Purpose**: Abstract store interface that all store implementations must satisfy.

**⚠️ CRITICAL**: Must complete before SQLite implementation.

- [ ] T023 [US1] Define MedallionStore Protocol in medallion/store.py with async methods: create(medallion: Medallion) -> None, update(medallion: Medallion) -> None, get_by_id(medallion_id: str) -> Optional[Medallion], get_latest_for_scope(scope: MedallionScope, limit: int = 10) -> List[Medallion]

- [ ] T024 [P] [US1] Write interface contract tests for MedallionStore in tests/unit/test_store.py (using Protocol to test mock implementations)

**Checkpoint**: Store interface complete. Ready for SQLite implementation.

---

## Phase 4: User Story 1 - Checkpoint Creation (Priority: P1) 🎯 MVP

**Goal**: Enable creating and persisting medallions from evidence. This is the foundation capability.

**Independent Test**: Define a scope, call `checkpoint_session` with mocked evidence, verify a valid medallion is created and persisted with all required schema fields.

### SQLite Store Implementation (US1)

- [ ] T025 [US1] Create SQLiteMedallionStore class skeleton in medallion/sqlite_store.py with __init__(db_path: Path | str = "medallion.db") constructor

- [ ] T026 [US1] Implement database initialization in SQLiteMedallionStore.__init__: Create medallions table with schema from data-model.md (id, content_json, created_at, updated_at, status, scope_graph_nodes, scope_tags, knowledge_min_ts, knowledge_max_ts, schema_version) if table doesn't exist

- [ ] T027 [US1] Implement database indexes in SQLiteMedallionStore.__init__: Create indexes on status, updated_at DESC, scope_graph_nodes, scope_tags

- [ ] T028 [US1] Implement SQLiteMedallionStore.create() async method: Validate medallion schema, serialize to JSON, insert into database, raise StoreError if ID exists

- [ ] T029 [US1] Implement SQLiteMedallionStore.get_by_id() async method: Query by ID, deserialize JSON to Medallion, return None if not found

- [ ] T030 [US1] Implement async context manager protocol (__aenter__, __aexit__, close) in SQLiteMedallionStore for resource cleanup

- [ ] T031 [P] [US1] Write unit tests for SQLiteMedallionStore.create() in tests/unit/test_sqlite_store.py (in-memory database, schema validation, duplicate ID error)

- [ ] T032 [P] [US1] Write unit tests for SQLiteMedallionStore.get_by_id() in tests/unit/test_sqlite_store.py (existing ID, non-existent ID returns None)

- [ ] T033 [P] [US1] Write integration tests for SQLiteMedallionStore create/get round-trip in tests/integration/test_store_integration.py

### LLM Stub Implementation (US1)

- [ ] T034 [US1] Define MedallionLLM Protocol in medallion/llm.py with async methods: generate(scope: MedallionScope, evidence: Evidence) -> Medallion, update(existing: Medallion, new_evidence: Evidence) -> Medallion

- [ ] T035 [US1] Implement StubMedallionLLM class in medallion/llm.py: generate() returns minimal valid medallion with generated UUID ID, current timestamps, scope from input, summary from evidence.session_summary, empty decisions/questions, default affordances

- [ ] T036 [US1] Implement StubMedallionLLM.update() in medallion/llm.py: Return existing medallion with updated_at changed to current time, preserve created_at (stub - no actual merging)

- [ ] T037 [P] [US1] Write unit tests for StubMedallionLLM.generate() in tests/unit/test_llm.py (valid medallion output, schema compliance)

- [ ] T038 [P] [US1] Write unit tests for StubMedallionLLM.update() in tests/unit/test_llm.py (timestamp update, created_at preservation)

### Session Helpers - Checkpoint Creation (US1)

- [ ] T039 [US1] Implement checkpoint_session() function in medallion/session.py: Check for existing active medallion via store.get_latest_for_scope(), if none: call llm.generate() -> store.create(), if exists: call llm.update() -> store.update(), return created/updated medallion

- [ ] T040 [US1] Add error handling to checkpoint_session(): Catch LLMError, StoreError, SchemaValidationError and re-raise with context

- [ ] T041 [P] [US1] Write unit tests for checkpoint_session() with new scope (no existing medallion) in tests/unit/test_session.py (mocked store and llm)

- [ ] T042 [P] [US1] Write integration tests for checkpoint_session() end-to-end in tests/integration/test_store_integration.py (real SQLite store, stub LLM)

**Checkpoint**: User Story 1 complete - checkpoint creation works end-to-end. MVP ready! ✅

---

## Phase 5: User Story 2 - Resume from Checkpoint (Priority: P2)

**Goal**: Enable loading existing medallions for a given scope so agents can resume from previous sessions.

**Independent Test**: Create a medallion with a specific scope, call `load_medallions_for_scope(store, scope)`, verify the previously created medallion is retrieved.

### SQLite Store - Scope Queries (US2)

- [ ] T043 [US2] Implement SQLiteMedallionStore.get_latest_for_scope() async method: Query medallions matching scope using subset matching for graph_nodes (requested nodes must be subset of stored nodes), intersection matching for tags, order by updated_at DESC, limit results

- [ ] T044 [US2] Implement scope matching logic in get_latest_for_scope(): Use SQLite JSON1 extension for JSON array operations (json_extract, json_each) or Python-side filtering for subset matching

- [ ] T045 [US2] Handle edge cases in get_latest_for_scope(): Empty scope returns empty list, limit <= 0 returns empty list, no matches returns empty list (not error)

- [ ] T046 [P] [US2] Write unit tests for get_latest_for_scope() exact match in tests/unit/test_sqlite_store.py (same graph_nodes and tags)

- [ ] T047 [P] [US2] Write unit tests for get_latest_for_scope() subset match in tests/unit/test_sqlite_store.py (requested graph_nodes subset of stored nodes)

- [ ] T048 [P] [US2] Write unit tests for get_latest_for_scope() ordering in tests/unit/test_sqlite_store.py (multiple medallions, ordered by updated_at DESC)

- [ ] T049 [P] [US2] Write unit tests for get_latest_for_scope() edge cases in tests/unit/test_sqlite_store.py (empty scope, no matches, limit=0)

### Session Helpers - Loading (US2)

- [ ] T050 [US2] Implement load_medallions_for_scope() sync function in medallion/session.py: Call store.get_latest_for_scope() with scope and limit, wrap async call with asyncio.run() or accept async context

- [ ] T051 [US2] Add error handling to load_medallions_for_scope(): Catch StoreError and re-raise with context

- [ ] T052 [P] [US2] Write unit tests for load_medallions_for_scope() in tests/unit/test_session.py (mocked store, verify scope matching behavior)

- [ ] T053 [P] [US2] Write integration tests for load_medallions_for_scope() end-to-end in tests/integration/test_store_integration.py (real SQLite store, create medallion then load it)

**Checkpoint**: User Story 2 complete - agents can load and resume from checkpoints. ✅

---

## Phase 6: User Story 3 - Update Checkpoint (Priority: P2)

**Goal**: Enable updating existing medallions with new evidence to prevent state duplication.

**Independent Test**: Create a medallion, call `checkpoint_session` again with same scope and new evidence, verify existing medallion is updated (not duplicated) with merged information.

### SQLite Store - Updates (US3)

- [ ] T054 [US3] Implement SQLiteMedallionStore.update() async method: Validate medallion schema, check medallion exists by ID (raise StoreError if not), serialize to JSON, update database row, preserve created_at timestamp from original

- [ ] T055 [US3] Add validation to update(): Ensure updated_at >= created_at (already in Pydantic model), verify medallion_id matches existing record

- [ ] T056 [P] [US3] Write unit tests for SQLiteMedallionStore.update() in tests/unit/test_sqlite_store.py (existing medallion, non-existent ID error, created_at preservation)

- [ ] T057 [P] [US3] Write unit tests for SQLiteMedallionStore.update() timestamp behavior in tests/unit/test_sqlite_store.py (updated_at changes, created_at unchanged)

### Session Helpers - Update Logic (US3)

- [ ] T058 [US3] Update checkpoint_session() to handle existing medallions: Use get_latest_for_scope() to find most recent active medallion, if found: call llm.update(existing, evidence) -> store.update(), preserve existing.created_at

- [ ] T059 [US3] Handle multiple medallions in checkpoint_session(): If multiple medallions exist for scope, use most recent (updated_at DESC, limit=1)

- [ ] T060 [P] [US3] Write unit tests for checkpoint_session() with existing medallion in tests/unit/test_session.py (mocked store/llm, verify update path not create path)

- [ ] T061 [P] [US3] Write integration tests for checkpoint_session() update flow in tests/integration/test_store_integration.py (create medallion, update with new evidence, verify single medallion not duplicated)

**Checkpoint**: User Story 3 complete - checkpoints can be updated without duplication. ✅

---

## Phase 7: User Story 4 - Graph-Anchored State (Priority: P3)

**Goal**: Support complex graph node queries for scoped checkpoint retrieval.

**Independent Test**: Create medallions with different graph_node combinations, query by specific node subsets, verify only relevant medallions are returned.

### Enhanced Scope Matching (US4)

- [ ] T062 [US4] Enhance get_latest_for_scope() tag matching: Implement intersection matching (any tag overlap returns match) or document exact match requirement

- [ ] T063 [US4] Optimize scope query performance: Review SQLite JSON1 queries vs Python-side filtering, add performance tests for 100+ medallions

- [ ] T064 [P] [US4] Write unit tests for complex graph node scenarios in tests/unit/test_sqlite_store.py (multiple nodes per medallion, partial matches, tag-only queries)

- [ ] T065 [P] [US4] Write integration tests for graph-anchored queries in tests/integration/test_store_integration.py (create multiple medallions with different scopes, query subsets)

**Checkpoint**: User Story 4 complete - advanced scope matching works. ✅

---

## Phase 8: Packaging & Documentation

**Purpose**: Make the package installable and usable by developers.

- [ ] T066 [P] Update medallion/__init__.py exports: Export Medallion, MedallionScope, Evidence, MedallionStore, SQLiteMedallionStore, MedallionLLM, StubMedallionLLM, load_medallions_for_scope, checkpoint_session, exception classes

- [ ] T067 [P] Create README.md: Installation instructions, basic usage examples from quickstart.md, links to docs

- [ ] T068 [P] Add package metadata to pyproject.toml: Name, version, description, author, license, requires-python

- [ ] T069 [P] Create setup scripts or build config: Add build system configuration for pip install -e .

- [ ] T070 [P] Add docstrings to all public APIs: Follow Google or NumPy style, include examples for main functions (Medallion, checkpoint_session, load_medallions_for_scope)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Code quality, coverage, and final polish.

### Test Coverage & Quality

- [ ] T071 [P] Run coverage report: Verify 90%+ coverage on medallion/store.py, medallion/sqlite_store.py, medallion/session.py (per constitution requirement)

- [ ] T072 [P] Add missing test cases: Fill gaps to reach 90%+ coverage if needed

- [ ] T073 [P] Run mypy type checking: Fix any type errors, ensure strict mode compliance

- [ ] T074 [P] Run linter: Fix any ruff/black/flake8 violations

### Error Handling & Edge Cases

- [ ] T075 [P] Add error handling for database connection failures in SQLiteMedallionStore: Catch sqlite3.Error and raise StoreError with context

- [ ] T076 [P] Add error handling for JSON serialization failures: Catch JSONEncodeError and raise SchemaValidationError

- [ ] T077 [P] Add edge case handling for empty evidence in checkpoint_session(): Document behavior or add validation

- [ ] T078 [P] Add edge case handling for schema version mismatches: Document that store preserves old versions, validation happens at application layer

### Performance & Optimization

- [ ] T079 [P] Add performance benchmarks: Measure create/update/get operations (target <10ms p95), scope queries (target <50ms p95 for <100 medallions)

- [ ] T080 [P] Optimize database queries if needed: Review indexes, query plans, JSON1 extension usage

### Documentation

- [ ] T081 [P] Validate quickstart.md examples: Run all code examples, update if needed

- [ ] T082 [P] Add architecture diagram or module overview to README.md: Show relationships between types, store, llm, session modules

**Checkpoint**: All Phase 1 (v1 MVP) tasks complete. Package is ready for use! ✅

---

## Phase 10: Future Work (Phase 2 - Out of Scope for v1)

**Purpose**: Deferred features for future releases. DO NOT implement in v1.

### Vector Search & Embeddings (Phase 2)

- [ ] T083 [Phase 2] [P] Design embedding storage strategy: Evaluate separate table vs BLOB column vs external vector DB

- [ ] T084 [Phase 2] [P] Implement embedding generation in MedallionLLM: Add optional embedding generation after medallion creation/update

- [ ] T085 [Phase 2] [P] Implement searchByText() in MedallionStore Protocol: Add method signature for semantic search

- [ ] T086 [Phase 2] [P] Implement searchByText() in SQLiteMedallionStore: Vector similarity search using embeddings

- [ ] T087 [Phase 2] [P] Add vector search tests: Unit and integration tests for semantic search functionality

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational Types (Phase 2)**: Depends on Setup - BLOCKS all other implementation
- **Foundational Store Interface (Phase 3)**: Depends on Types (Phase 2) - BLOCKS store implementation
- **User Story 1 (Phase 4)**: Depends on Types + Store Interface - First MVP story
- **User Story 2 (Phase 5)**: Depends on User Story 1 (uses checkpoint creation)
- **User Story 3 (Phase 6)**: Depends on User Story 1 (uses checkpoint creation)
- **User Story 4 (Phase 7)**: Depends on User Story 2 (enhances scope matching)
- **Packaging (Phase 8)**: Depends on all user stories (exports all modules)
- **Polish (Phase 9)**: Depends on all implementation phases
- **Phase 2 Features (Phase 10)**: Deferred - do not implement in v1

### User Story Dependencies

- **User Story 1 (P1)**: MVP - Can complete independently after foundational phases
- **User Story 2 (P2)**: Requires US1 (needs medallions to exist before loading)
- **User Story 3 (P2)**: Requires US1 (needs checkpoint creation to work first)
- **User Story 4 (P3)**: Requires US2 (enhances scope loading functionality)

### Within Each User Story

- Tests can be written in parallel with implementation (TDD approach)
- Store implementation before session helpers
- LLM stub before session helpers (checkpoint_session depends on LLM)
- Core implementation before integration tests

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- Types model creation tasks (T007-T015) can mostly run in parallel (different models)
- Test tasks marked [P] can run in parallel with implementation
- Packaging tasks (T066-T069) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Types (FOUNDATIONAL - BLOCKS ALL)
3. Complete Phase 3: Store Interface (FOUNDATIONAL - BLOCKS STORE)
4. Complete Phase 4: User Story 1 (Checkpoint Creation)
5. **STOP and VALIDATE**: Test checkpoint creation end-to-end
6. This satisfies Acceptance Criteria 1-3 from PRD: Install, initialize, create checkpoint

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add Packaging → Make installable
7. Add Polish → Production ready

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: SQLite Store implementation (T025-T033)
   - Developer B: LLM Stub implementation (T034-T038)
   - Developer C: Tests for types (T018-T022)
3. Session helpers (T039-T042) depend on both store and LLM

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD where applicable)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Phase 1 (v1 MVP) = Phases 1-8 (Setup through Packaging)
- Phase 2 = Vector search and embeddings (explicitly deferred)

## Task Count Summary

- **Total Tasks**: 87 (82 Phase 1, 5 Phase 2 deferred)
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational Types)**: 11 tasks
- **Phase 3 (Foundational Store Interface)**: 2 tasks
- **Phase 4 (US1 - Checkpoint Creation)**: 15 tasks
- **Phase 5 (US2 - Resume from Checkpoint)**: 11 tasks
- **Phase 6 (US3 - Update Checkpoint)**: 8 tasks
- **Phase 7 (US4 - Graph-Anchored)**: 4 tasks
- **Phase 8 (Packaging)**: 5 tasks
- **Phase 9 (Polish)**: 12 tasks
- **Phase 10 (Deferred)**: 5 tasks

**MVP Scope (Phases 1-4)**: 34 tasks
**Full v1 Scope (Phases 1-8)**: 64 tasks

