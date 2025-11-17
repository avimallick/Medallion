<!--
Sync Impact Report:
Version: 1.0.0 (initial constitution)
Modified principles: None (new document)
Added sections: Core Principles (7 principles), Technology Stack, Development Standards
Removed sections: None
Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section will reference new principles
  ⚠️ .specify/templates/spec-template.md - Review for alignment with framework-agnostic, determinism principles
  ⚠️ .specify/templates/tasks-template.md - Review for test coverage requirements (90%+)
Follow-up TODOs: None
-->

# Medallion Constitution

## Core Principles

### I. Modular Architecture
Medallion MUST be organized as small, composable modules: `types`, `store`, `llm`, `session`, `cli`. Each module MUST be independently testable and clearly separated by responsibility. Modules MUST communicate through well-defined interfaces, not through shared global state or hidden dependencies. The package structure MUST remain clean and navigable.

**Rationale**: Small, composable modules enable independent development, testing, and maintenance. This structure supports the framework-agnostic design goal and makes it easier to integrate Medallion into different agent systems.

### II. Testability (NON-NEGOTIABLE)
Core logic (store + session helpers) MUST achieve 90%+ unit test coverage. Tests MUST be written using standard Python testing frameworks (pytest). Test fixtures MUST be isolated and deterministic. Integration tests MUST cover the critical paths: medallion creation, updates, retrieval, and LLM integration. All tests MUST run in CI/CD pipelines before merge.

**Rationale**: High test coverage ensures reliability and makes refactoring safe. Testability directly supports determinism and reproducibility goals by catching regressions early.

### III. Determinism and Reproducibility
Medallion operations MUST produce deterministic outputs for identical inputs. Storage operations MUST be idempotent where applicable. Medallion generation and updates MUST use structured JSON schemas that eliminate ambiguity. The system MUST support reproducible checkpoint creation and loading, ensuring agents can resume from identical states.

**Rationale**: Non-deterministic behavior defeats the purpose of checkpointing. Agents must be able to rely on medallions as a stable source of truth that produces consistent results across sessions.

### IV. Framework-Agnostic Design
Medallion MUST work with LangChain, LangGraph, and custom agent frameworks without coupling to their internals. Integration MUST occur through lightweight adapters or simple wrapper functions. The core library MUST NOT import framework-specific dependencies in its base modules. Public APIs MUST be framework-neutral.

**Rationale**: Framework lock-in would limit adoption and increase maintenance burden. Medallion's value is as a universal checkpointing layer, not as a framework-specific feature.

### V. Strict Typing and Error Handling
All code MUST be type-annotated and mypy-compliant (strict mode). Public APIs MUST use typed dataclasses or Pydantic models for Medallion schema. Errors MUST be explicitly raised with clear exception types. Error messages MUST provide actionable information for debugging. Type safety MUST be enforced at module boundaries.

**Rationale**: Strict typing catches errors at development time and makes the codebase self-documenting. Clear error handling improves debuggability and user experience.

### VI. Versioned Structured State
Medallions MUST be structured JSON objects with a strict, versioned schema. Each medallion MUST include schema version metadata. Medallions MUST be both human-inspectable (readable JSON) AND machine-consumable (validated against schema). Schema evolution MUST be explicitly versioned, and backward compatibility MUST be maintained or migration paths provided. Medallions MUST be safely updatable over time without data loss.

**Rationale**: Structured, versioned state ensures medallions remain usable as the system evolves. Human-inspectability enables debugging and verification, while machine-consumability enables programmatic use.

### VII. No Hidden Global State
All dependencies MUST be injected explicitly. Functions and classes MUST accept dependencies as parameters or constructor arguments. Configuration MUST be passed explicitly, not accessed through global variables or singletons. The system MUST be dependency-injection friendly, enabling easy testing and integration.

**Rationale**: Hidden global state makes testing difficult and creates implicit dependencies that break modularity. Explicit dependency injection supports testability and framework-agnostic design.

## Technology Stack

**Language**: Python 3.11+ for v0. The implementation MUST use modern Python features (dataclasses, type hints, async/await where appropriate). The package MUST be installable via standard Python package managers (pip, poetry).

**Storage Backend**: SQLite or TinyDB for v0. The store abstraction MUST allow pluggable backends. Vector search (embeddings) is OPTIONAL for v1.

**Schema Validation**: Pydantic or similar for runtime schema validation. JSON Schema for schema definition and documentation.

**Non-Goals for v1**: Distributed/clustered deployment, complex UIs, heavy observability stacks. Focus on core functionality with minimal dependencies.

## Development Standards

**Code Quality**: All code MUST pass linting (ruff or black + flake8) and type checking (mypy strict mode) before merge. Code reviews MUST verify constitution compliance.

**Documentation**: Public APIs MUST be documented with docstrings following Google or NumPy style. README MUST include quickstart examples. Schema definitions MUST be documented with examples.

**Error Handling**: All external operations (LLM calls, database operations) MUST have explicit error handling. Errors MUST be logged with appropriate context. User-facing errors MUST be clear and actionable.

**Testing Strategy**: Unit tests for all core logic (90%+ coverage requirement). Integration tests for store operations and LLM integration. Contract tests for schema validation. Tests MUST run deterministically and in isolation.

## Governance

This constitution supersedes all other development practices. Amendments require:
1. Documentation of the rationale for change
2. Impact assessment on existing code and dependencies
3. Version bump following semantic versioning (MAJOR.MINOR.PATCH)
4. Update of affected templates and documentation

All pull requests and code reviews MUST verify compliance with these principles. Complexity beyond these principles MUST be explicitly justified and documented. Violations of core principles MUST be addressed before merge, unless granted explicit exception with documented rationale.

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
