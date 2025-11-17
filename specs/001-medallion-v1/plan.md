# Implementation Plan: Medallion Library v1

**Branch**: `001-medallion-v1` | **Date**: 2025-11-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-medallion-v1/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Medallion v1 provides a semantic checkpointing layer for LLM agents, enabling them to resume work from structured "savepoints" instead of re-deriving context each session. The implementation delivers a Python package with: (1) a strict Medallion schema using Pydantic models, (2) a MedallionStore interface with SQLite implementation, (3) an LLM helper interface for medallion generation/update (stub for now), and (4) session helper functions for loading and checkpointing. All modules are dependency-injection friendly, strictly typed, and achieve 90%+ test coverage on core logic.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- `pydantic>=2.0` for schema validation and type safety
- `sqlite3` (stdlib) for database operations
- `pytest>=7.0` for testing
- `mypy>=1.0` for type checking
- `ruff` or `black` + `flake8` for linting

**Storage**: SQLite database file (`medallion.db` by default) with a `medallions` table storing JSON content and indexed scope fields for efficient queries.

**Testing**: pytest with unit tests (90%+ coverage on store + session modules), integration tests for store operations, and contract tests for schema validation.

**Target Platform**: Python 3.11+ on Linux, macOS, Windows (cross-platform compatible).

**Project Type**: Single Python library package (not web/mobile).

**Performance Goals**: 
- Store operations (create/update/get) <10ms p95
- Scope queries (<100 medallions) <50ms p95
- Schema validation <1ms per medallion

**Constraints**: 
- No network calls in core library (LLM client injected)
- No framework-specific dependencies in base modules
- SQLite file-based storage (no server required)
- Deterministic operations (same inputs → same outputs)

**Scale/Scope**: 
- Supports 1000s of medallions per database
- Single-user/single-process usage pattern (v1)
- No distributed sync or multi-user concurrency (future)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modular Architecture ✅
**Status**: COMPLIANT
- Package structure matches: `types.py`, `store.py`, `sqlite_store.py`, `llm.py`, `session.py`
- Each module is independently testable with clear responsibilities
- No shared global state; all dependencies injected

### II. Testability (NON-NEGOTIABLE) ✅
**Status**: COMPLIANT
- 90%+ unit test coverage target on `store.py` + `session.py` (core logic)
- pytest framework selected
- Test fixtures isolated and deterministic

### III. Determinism and Reproducibility ✅
**Status**: COMPLIANT
- Storage operations are idempotent (create/update)
- Medallion schema enforces structured JSON
- Schema validation ensures consistent outputs

### IV. Framework-Agnostic Design ✅
**Status**: COMPLIANT
- No framework imports in core modules
- LLM client injected via interface (no network calls in core)
- Public APIs are framework-neutral

### V. Strict Typing and Error Handling ✅
**Status**: COMPLIANT
- All code type-annotated with mypy strict mode
- Pydantic models for schema validation
- Explicit exception types for errors

### VI. Versioned Structured State ✅
**Status**: COMPLIANT
- Medallion schema includes `schema_version` in meta
- Human-inspectable JSON (readable)
- Machine-consumable (Pydantic validation)

### VII. No Hidden Global State ✅
**Status**: COMPLIANT
- All dependencies injected (store, llm passed as parameters)
- Configuration passed explicitly
- DI-friendly design

**GATE RESULT**: ✅ PASS - All principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-medallion-v1/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api.md           # API signatures
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
medallion/
├── __init__.py          # Package exports: Medallion, MedallionStore, SQLiteMedallionStore, etc.
├── types.py             # Medallion schema (Pydantic models): Medallion, MedallionScope, Evidence, etc.
├── store.py             # MedallionStore abstract base class (Protocol/ABC)
├── sqlite_store.py      # SQLiteMedallionStore implementation
├── llm.py               # MedallionLLM interface (Protocol) + stub implementation
└── session.py           # load_medallions_for_scope, checkpoint_session functions

tests/
├── unit/
│   ├── test_types.py    # Schema validation tests
│   ├── test_store.py    # MedallionStore interface tests (mocked)
│   ├── test_sqlite_store.py  # SQLiteMedallionStore implementation tests
│   ├── test_llm.py      # MedallionLLM stub tests
│   └── test_session.py  # Session helper function tests
├── integration/
│   └── test_store_integration.py  # End-to-end store operations
└── contract/
    └── test_schema_contract.py    # Schema validation contract tests
```

**Structure Decision**: Single Python package layout (`medallion/`) with tests mirroring module structure under `tests/`. This aligns with Python packaging standards and constitution modularity requirements.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. Architecture is simple and aligned with constitution.
