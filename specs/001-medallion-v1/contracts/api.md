# API Contracts: Medallion Library v1

**Date**: 2025-11-17  
**Feature**: Medallion Library v1

## Overview

This document defines the API contracts for the Medallion library v1. All interfaces use `typing.Protocol` for structural typing and dependency injection.

## Module: `medallion.store`

### MedallionStore (Protocol)

Abstract interface for medallion storage operations.

```python
from typing import Protocol, Optional, List
from medallion.types import Medallion, MedallionScope

class MedallionStore(Protocol):
    """Abstract interface for medallion storage."""
    
    async def create(self, medallion: Medallion) -> None:
        """
        Persist a new medallion.
        
        Args:
            medallion: The medallion to persist
            
        Raises:
            StoreError: If medallion already exists (by ID) or persistence fails
            SchemaValidationError: If medallion schema validation fails
        """
        ...
    
    async def update(self, medallion: Medallion) -> None:
        """
        Update an existing medallion.
        
        Args:
            medallion: The medallion to update (must have existing ID)
            
        Raises:
            StoreError: If medallion doesn't exist or update fails
            SchemaValidationError: If medallion schema validation fails
        """
        ...
    
    async def get_by_id(self, medallion_id: str) -> Optional[Medallion]:
        """
        Fetch a medallion by its ID.
        
        Args:
            medallion_id: The unique identifier of the medallion
            
        Returns:
            The medallion if found, None otherwise
            
        Raises:
            StoreError: If database query fails
        """
        ...
    
    async def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10
    ) -> List[Medallion]:
        """
        Fetch the latest medallions matching the given scope.
        
        Scope matching rules:
        - graph_nodes: Requested nodes must be a subset of stored nodes (subset match)
        - tags: Exact match or intersection (implementation decision)
        - Results ordered by updated_at DESC (latest first)
        
        Args:
            scope: The scope to match against
            limit: Maximum number of medallions to return (default: 10)
            
        Returns:
            List of matching medallions, ordered by updated_at DESC
            
        Raises:
            StoreError: If database query fails
            
        Edge cases:
        - Empty scope (no graph_nodes, no tags): Returns empty list
        - No matches: Returns empty list (not an error)
        - Limit 0 or negative: Returns empty list
        """
        ...
```

**Behavior**:
- All methods are async (future-proofing for I/O)
- `create` raises error if medallion with same ID already exists
- `update` raises error if medallion doesn't exist
- `get_latest_for_scope` uses subset matching for graph_nodes (see Scope Matching below)

### SQLiteMedallionStore

Concrete implementation using SQLite.

```python
from pathlib import Path
from typing import Optional
from medallion.types import Medallion
from medallion.store import MedallionStore

class SQLiteMedallionStore:
    """SQLite-backed implementation of MedallionStore."""
    
    def __init__(self, db_path: Path | str = "medallion.db") -> None:
        """
        Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file (default: "medallion.db")
            
        Raises:
            StoreError: If database initialization fails
        """
        ...
    
    async def create(self, medallion: Medallion) -> None:
        """Implementation of MedallionStore.create."""
        ...
    
    async def update(self, medallion: Medallion) -> None:
        """Implementation of MedallionStore.update."""
        ...
    
    async def get_by_id(self, medallion_id: str) -> Optional[Medallion]:
        """Implementation of MedallionStore.get_by_id."""
        ...
    
    async def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10
    ) -> List[Medallion]:
        """Implementation of MedallionStore.get_latest_for_scope."""
        ...
    
    async def close(self) -> None:
        """Close database connection."""
        ...
    
    async def __aenter__(self) -> "SQLiteMedallionStore":
        """Async context manager entry."""
        ...
    
    async def __aexit__(self, *args) -> None:
        """Async context manager exit (calls close)."""
        ...
```

**Implementation details**:
- Uses `aiosqlite` or `asyncio` wrapper for async SQLite operations
- Automatically creates database and schema on first use
- Validates medallion schema before persistence
- Uses parameterized queries to prevent SQL injection
- Supports async context manager protocol

## Module: `medallion.llm`

### MedallionLLM (Protocol)

Abstract interface for LLM-based medallion generation/update.

```python
from typing import Protocol
from medallion.types import Medallion, MedallionScope, Evidence

class MedallionLLM(Protocol):
    """Abstract interface for LLM-based medallion operations."""
    
    async def generate(
        self,
        scope: MedallionScope,
        evidence: Evidence
    ) -> Medallion:
        """
        Generate a new medallion from evidence.
        
        Args:
            scope: The scope this medallion applies to
            evidence: Evidence data (session_summary, transcripts, artefacts)
            
        Returns:
            A new medallion with:
            - Generated medallion_id (UUID v4)
            - Schema version "medallion.v1"
            - Current timestamps (created_at == updated_at)
            - Status "active"
            - Summary, decisions, open_questions, affordances derived from evidence
            
        Raises:
            LLMError: If LLM call fails or response is invalid JSON
            SchemaValidationError: If generated medallion doesn't conform to schema
            
        Edge cases:
        - Empty evidence.session_summary: LLM should generate minimal medallion or raise error
        - Invalid JSON from LLM: Raise LLMError with context
        - Schema violations in LLM response: Raise SchemaValidationError
        """
        ...
    
    async def update(
        self,
        existing: Medallion,
        new_evidence: Evidence
    ) -> Medallion:
        """
        Update an existing medallion with new evidence.
        
        Args:
            existing: The existing medallion to update
            new_evidence: New evidence to merge into the medallion
            
        Returns:
            An updated medallion with:
            - Same medallion_id as existing
            - Same created_at as existing
            - New updated_at timestamp
            - Status remains "active" (unless explicitly changed)
            - Summary, decisions, open_questions updated based on new evidence
            - Preserves IDs of existing decisions/questions unless obsolete
            
        Raises:
            LLMError: If LLM call fails or response is invalid JSON
            SchemaValidationError: If updated medallion doesn't conform to schema
            
        Edge cases:
        - Conflicting decisions: LLM should resolve (update or remove old, add new)
        - Resolved questions: LLM should remove from open_questions
        - Invalid JSON from LLM: Raise LLMError with context
        - Schema violations: Raise SchemaValidationError
        """
        ...
```

**Behavior**:
- Both methods call external LLM (network I/O, hence async)
- LLM is responsible for prompt construction and JSON schema enforcement
- Generated medallions are validated against Pydantic schema before return
- For v1, stub implementation returns mock medallions (for testing)

### StubMedallionLLM (Implementation)

Stub implementation for testing (v1).

```python
from medallion.types import Medallion, MedallionScope, Evidence
from medallion.llm import MedallionLLM

class StubMedallionLLM:
    """Stub implementation of MedallionLLM for testing."""
    
    async def generate(
        self,
        scope: MedallionScope,
        evidence: Evidence
    ) -> Medallion:
        """
        Generate a mock medallion (stub implementation).
        
        Returns a minimal valid medallion with:
        - Generated ID
        - Scope from input
        - Summary from evidence.session_summary
        - Empty decisions, open_questions
        - Default affordances
        """
        ...
    
    async def update(
        self,
        existing: Medallion,
        new_evidence: Evidence
    ) -> Medallion:
        """
        Return existing medallion with updated timestamp (stub).
        
        In real implementation, this would call LLM to merge new evidence.
        """
        ...
```

## Module: `medallion.session`

### load_medallions_for_scope

Load medallions for a given scope at session start.

```python
from typing import Optional
from medallion.types import Medallion, MedallionScope
from medallion.store import MedallionStore

def load_medallions_for_scope(
    store: MedallionStore,
    scope: MedallionScope,
    *,
    limit: int = 10
) -> list[Medallion]:
    """
    Load medallions for a given scope (sync wrapper).
    
    Args:
        store: The medallion store instance
        scope: The scope to query
        limit: Maximum number of medallions to return (default: 10)
        
    Returns:
        List of medallions matching the scope, ordered by updated_at DESC
        
    Raises:
        StoreError: If database query fails
        
    Edge cases:
        - Empty scope: Returns empty list
        - No matches: Returns empty list (not an error)
        - Limit <= 0: Returns empty list
    """
    ...
```

**Implementation**:
- Sync wrapper that calls async `store.get_latest_for_scope` internally
- Uses `asyncio.run` or accepts async context
- For async frameworks, use `store.get_latest_for_scope` directly

### checkpoint_session

Create or update a medallion at session end/milestone.

```python
from medallion.types import Medallion, MedallionScope, Evidence
from medallion.store import MedallionStore
from medallion.llm import MedallionLLM

def checkpoint_session(
    store: MedallionStore,
    llm: MedallionLLM,
    scope: MedallionScope,
    evidence: Evidence
) -> Medallion:
    """
    Create or update a medallion for a session (sync wrapper).
    
    Behavior:
    1. Check if active medallion exists for scope (via get_latest_for_scope)
    2. If none exists: call llm.generate() → store.create()
    3. If exists: call llm.update(existing, evidence) → store.update()
    4. Return the created/updated medallion
    
    Args:
        store: The medallion store instance
        llm: The LLM helper instance
        scope: The scope for this checkpoint
        evidence: Evidence data from the session
        
    Returns:
        The created or updated medallion
        
    Raises:
        StoreError: If store operations fail
        LLMError: If LLM operations fail
        SchemaValidationError: If medallion validation fails
        
    Edge cases:
        - No active medallion for scope: Creates new one
        - Multiple medallions for scope: Uses most recent (updated_at DESC)
        - Stale medallions: Treats as existing (updates them)
        - Empty evidence: LLM should handle (generate minimal or error)
        - LLM returns invalid JSON: Raises LLMError
        - LLM returns schema violation: Raises SchemaValidationError
    """
    ...
```

**Implementation details**:
- Sync wrapper that calls async methods internally
- "Active" medallion means status="active" (default)
- Always uses most recent medallion if multiple exist
- Preserves `created_at` on update (sets new `updated_at`)

## Scope Matching Rules

### graph_nodes Matching

**Rule**: Subset matching (requested nodes must be subset of stored nodes).

Examples:
- Request: `["repo:muse"]`
- Matches: `["repo:muse"]`, `["repo:muse", "module:cli"]`
- Does not match: `["repo:other"]`, `[]`

Implementation:
```python
# Requested nodes must all be present in stored nodes
requested_nodes = set(scope.graph_nodes)
stored_nodes = set(medallion.scope.graph_nodes)
matches = requested_nodes.issubset(stored_nodes)
```

### tags Matching

**Rule**: Intersection matching (any tag match).

Examples:
- Request: `["project_state"]`
- Matches: `["project_state"]`, `["project_state", "refactor"]`
- Does not match: `[]`, `["other_tag"]`

Implementation:
```python
# Any tag overlap means match
requested_tags = set(scope.tags)
stored_tags = set(medallion.scope.tags)
matches = len(requested_tags & stored_tags) > 0 or len(requested_tags) == 0
```

**Edge case**: Empty tags list matches any tags (if graph_nodes also match).

## Error Types

```python
class MedallionError(Exception):
    """Base exception for Medallion operations."""
    pass

class SchemaValidationError(MedallionError):
    """Raised when medallion schema validation fails."""
    pass

class StoreError(MedallionError):
    """Raised when store operations fail."""
    pass

class LLMError(MedallionError):
    """Raised when LLM operations fail."""
    pass
```

All exceptions include context in error messages (scope, operation type, etc.).

## Testing Contracts

### Test Doubles

- **MockMedallionStore**: Implements MedallionStore protocol for testing
- **MockMedallionLLM**: Implements MedallionLLM protocol for testing
- **StubMedallionLLM**: Provided stub implementation for integration tests

### Contract Tests

- Schema validation: All medallions must pass Pydantic validation
- Store operations: All MedallionStore implementations must pass interface tests
- Session helpers: Must work with any MedallionStore/MedallionLLM implementation

