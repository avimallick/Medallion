# Research: Medallion Library v1

**Date**: 2025-11-17  
**Feature**: Medallion Library v1  
**Purpose**: Resolve technical decisions and clarify implementation details

## Technology Choices

### Schema Validation: Pydantic

**Decision**: Use Pydantic v2+ for Medallion schema validation and type safety.

**Rationale**:
- Constitution requires strict typing and mypy-compliant code
- Pydantic provides runtime validation, type hints, and JSON serialization
- Native dataclass-like API with automatic validation
- Excellent error messages for schema violations
- Widely adopted in Python ecosystem

**Alternatives considered**:
- Plain dataclasses: Rejected because no built-in validation, manual JSON serialization needed
- TypedDict: Rejected because no runtime validation, type hints only
- Marshmallow: Rejected because more verbose API, less type-checking integration

**Implementation notes**:
- Use Pydantic BaseModel for Medallion and nested types
- Enable strict mode for type coercion
- Use Pydantic's JSON schema generation for documentation

### Database: SQLite

**Decision**: Use SQLite with JSON storage for medallion content.

**Rationale**:
- Constitution specifies SQLite for v0
- File-based, no server required (matches constraints)
- Native JSON support (JSON1 extension) for querying
- Excellent performance for single-user/single-process use case
- Zero configuration

**Alternatives considered**:
- TinyDB: Rejected because less query flexibility, JSON-only storage
- PostgreSQL: Rejected because requires server setup, overkill for v1

**Implementation notes**:
- Use SQLite JSON1 extension for JSON operations
- Store full medallion JSON in `content_json` column
- Index `scope_graph_nodes` and `scope_tags` for efficient queries
- Use parameterized queries to prevent SQL injection

### Protocol/ABC for Interfaces

**Decision**: Use `typing.Protocol` for MedallionStore and MedallionLLM interfaces.

**Rationale**:
- Structural typing (duck typing) aligns with Python philosophy
- No runtime overhead (unlike ABC)
- Works seamlessly with dependency injection
- Type checkers (mypy) validate protocol conformance
- Easier to test (no need to inherit)

**Alternatives considered**:
- Abstract Base Classes (ABC): Rejected because requires inheritance, more ceremony
- Plain type hints: Rejected because no formal contract enforcement

**Implementation notes**:
- Define MedallionStore as Protocol with async methods
- Define MedallionLLM as Protocol with async methods
- Use Protocol for test doubles (mocks) as well

### Testing: pytest

**Decision**: Use pytest for all tests.

**Rationale**:
- Standard Python testing framework
- Excellent fixture system for isolation
- Rich assertion introspection
- Plugins for coverage, async testing
- Constitution requires pytest

**Implementation notes**:
- Use pytest fixtures for database setup/teardown
- Use pytest-asyncio for async store methods
- Use pytest-cov for coverage reporting (90%+ target)
- Use pytest-mock for mocking LLM clients

### Type Checking: mypy

**Decision**: Use mypy in strict mode for type checking.

**Rationale**:
- Constitution requires mypy strict mode compliance
- Catches type errors at development time
- Integrates with Pydantic seamlessly
- Industry standard for Python type checking

**Implementation notes**:
- Configure mypy with `strict = true`
- Use type stubs for stdlib modules if needed
- Enable `--warn-unused-configs` to catch config issues

### JSON Schema Versioning

**Decision**: Use `schema_version` field in MedallionMeta to track schema versions (e.g., "medallion.v1").

**Rationale**:
- Constitution requires versioned structured state
- Enables future schema evolution
- Allows migration paths in future versions
- Human-readable version string

**Implementation notes**:
- For v1, always use "medallion.v1"
- Store versions in meta field, preserve during updates
- Validate schema version on load (reject unsupported versions)

### Scope Query Matching

**Decision**: Use subset matching for `graph_nodes` (requested nodes must be subset of stored nodes) and exact/intersection matching for tags.

**Rationale**:
- PRD examples show subset matching behavior
- Enables querying by partial scope (e.g., ["repo:muse"] matches ["repo:muse", "module:cli"])
- Tags support exact match or intersection
- Practical for knowledge graph integration

**Implementation notes**:
- SQLite JSON1 extension supports JSON array operations
- Query: `WHERE json_array_length(json_extract(content_json, '$.scope.graph_nodes')) >= json_array_length(?) AND json_each(?) = json_each(content_json, '$.scope.graph_nodes')`
- Or use Python-side filtering for simpler logic

### Error Handling Strategy

**Decision**: Define custom exception types: `MedallionError`, `SchemaValidationError`, `StoreError`, `LLMError`.

**Rationale**:
- Constitution requires clear exception types
- Enables framework-specific error handling
- Makes debugging easier with context

**Implementation notes**:
- Base exception: `MedallionError(Exception)`
- Subclasses: `SchemaValidationError`, `StoreError`, `LLMError`
- Include context in error messages (scope, operation type)

### Async vs Sync

**Decision**: Use async/await for store and LLM methods (future-proofing), sync wrapper for session helpers.

**Rationale**:
- LLM calls are naturally async (network I/O)
- Store operations can benefit from async for concurrency
- Sync wrapper simplifies usage for non-async frameworks

**Implementation notes**:
- MedallionStore methods: async
- MedallionLLM methods: async
- Session helpers: sync wrappers that call async internally (using asyncio.run or accept async context)

### Migration Strategy (v1)

**Decision**: No migration needed for v1 (initial schema). Document migration approach for future versions.

**Rationale**:
- v1 is the first version, no existing data to migrate
- Future versions can add migration scripts
- Store preserves raw JSON, migration can happen at read time

**Implementation notes**:
- Document migration strategy in comments
- Schema version check on load (future-proofing)
- Reject unsupported schema versions with clear error

## Unresolved / Future Decisions

- **LLM Provider**: Deferred to implementation (interface-based, any provider can be injected)
- **Prompt Engineering**: Deferred to implementation (LLM module handles prompt construction)
- **Embedding Model**: Deferred (vector search out of scope for v1)
- **Concurrency**: Deferred (single-process, single-user for v1, last-write-wins acceptable)

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLite JSON1 Extension](https://www.sqlite.org/json1.html)
- [Python typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [pytest Documentation](https://docs.pytest.org/)
- [mypy Strict Mode](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
