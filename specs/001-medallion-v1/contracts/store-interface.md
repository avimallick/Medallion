# API Contract: MedallionStore Interface

**Feature**: Medallion Library v1  
**Date**: 2025-11-17  
**Purpose**: Define abstract MedallionStore interface and SQLiteMedallionStore implementation contract

---

## MedallionStore Interface

Abstract interface for medallion storage operations. Defined in `medallion/store.py`.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from medallion.types import Medallion, MedallionScope

class MedallionStore(ABC):
    """Abstract interface for medallion storage operations."""
    
    @abstractmethod
    def create(self, medallion: Medallion) -> None:
        """Persist a new medallion to storage.
        
        Args:
            medallion: The medallion to persist
            
        Raises:
            MedallionValidationError: If medallion schema is invalid
            StoreConflictError: If medallion with same ID already exists
            StoreError: For other storage errors
        """
        pass
    
    @abstractmethod
    def update(self, medallion: Medallion) -> None:
        """Update an existing medallion in storage.
        
        Args:
            medallion: The updated medallion (must have existing ID)
            
        Raises:
            MedallionValidationError: If medallion schema is invalid
            StoreNotFoundError: If medallion with given ID doesn't exist
            StoreError: For other storage errors
        """
        pass
    
    @abstractmethod
    def get_by_id(self, medallion_id: str) -> Optional[Medallion]:
        """Fetch a medallion by exact ID.
        
        Args:
            medallion_id: The unique identifier of the medallion
            
        Returns:
            The medallion if found, None otherwise
            
        Raises:
            StoreError: For storage errors (not for not-found cases)
        """
        pass
    
    @abstractmethod
    def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10
    ) -> List[Medallion]:
        """Fetch latest medallions matching the given scope.
        
        Args:
            scope: The scope to match (graph_nodes and/or tags)
            limit: Maximum number of medallions to return (default: 10)
            
        Returns:
            List of medallions matching the scope, ordered by updated_at descending,
            up to limit. Returns empty list if no matches found.
            
        Raises:
            StoreError: For storage errors
        """
        pass
```

---

## SQLiteMedallionStore Implementation

Concrete SQLite-backed implementation of MedallionStore. Defined in `medallion/sqlite_store.py`.

```python
from pathlib import Path
from typing import List, Optional
from medallion.types import Medallion, MedallionScope
from medallion.store import MedallionStore
from medallion.exceptions import StoreError, StoreNotFoundError, StoreConflictError, MedallionValidationError

class SQLiteMedallionStore(MedallionStore):
    """SQLite-backed implementation of MedallionStore."""
    
    def __init__(self, db_path: str | Path = "medallion.db"):
        """Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file (default: "medallion.db")
            
        Raises:
            StoreError: If database initialization fails
        """
        pass
    
    def create(self, medallion: Medallion) -> None:
        """Persist a new medallion to SQLite.
        
        Implementation details:
        1. Validate medallion schema (via Pydantic)
        2. Check if medallion with same ID exists (raise StoreConflictError if yes)
        3. Serialize medallion to JSON
        4. Insert into medallions table with indexed fields
        5. Commit transaction
        
        Args:
            medallion: The medallion to persist
            
        Raises:
            MedallionValidationError: If medallion schema is invalid
            StoreConflictError: If medallion with same ID already exists
            StoreError: For other storage errors (SQL errors, etc.)
        """
        pass
    
    def update(self, medallion: Medallion) -> None:
        """Update an existing medallion in SQLite.
        
        Implementation details:
        1. Validate medallion schema (via Pydantic)
        2. Check if medallion exists (raise StoreNotFoundError if not)
        3. Serialize medallion to JSON
        4. Update medallions table (preserve created_at, update updated_at)
        5. Commit transaction
        
        Args:
            medallion: The updated medallion (must have existing ID)
            
        Raises:
            MedallionValidationError: If medallion schema is invalid
            StoreNotFoundError: If medallion with given ID doesn't exist
            StoreError: For other storage errors
        """
        pass
    
    def get_by_id(self, medallion_id: str) -> Optional[Medallion]:
        """Fetch a medallion by exact ID from SQLite.
        
        Implementation details:
        1. Query medallions table by ID
        2. If found, deserialize JSON to Medallion object
        3. Return Medallion or None
        
        Args:
            medallion_id: The unique identifier of the medallion
            
        Returns:
            The medallion if found, None otherwise
            
        Raises:
            StoreError: For storage errors (SQL errors, JSON deserialization errors)
        """
        pass
    
    def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10
    ) -> List[Medallion]:
        """Fetch latest medallions matching the given scope from SQLite.
        
        Implementation details:
        1. Handle empty scope (return empty list immediately)
        2. Build SQL query with scope matching:
           - Match graph_nodes: WHERE scope_graph_nodes contains all requested nodes (JSON subset match)
           - Match tags: WHERE scope_tags contains all requested tags (JSON subset match)
           - OR logic: If both graph_nodes and tags provided, match if either matches
           - Filter by status='active' only
        3. Order by updated_at DESC
        4. Limit results
        5. Deserialize JSON to Medallion objects
        6. Return list
        
        Scope matching logic:
        - Empty scope ({graph_nodes: [], tags: []}) -> return empty list
        - If graph_nodes provided: Match medallions where stored graph_nodes contains all requested nodes
        - If tags provided: Match medallions where stored tags contains all requested tags
        - If both provided: Match if either condition is true (OR logic)
        
        Args:
            scope: The scope to match (graph_nodes and/or tags)
            limit: Maximum number of medallions to return (default: 10)
            
        Returns:
            List of medallions matching the scope, ordered by updated_at descending,
            up to limit. Returns empty list if no matches found.
            
        Raises:
            StoreError: For storage errors
        """
        pass
    
    def _ensure_schema(self) -> None:
        """Ensure database schema exists (create tables if needed).
        
        Internal method called during initialization.
        
        Raises:
            StoreError: If schema creation fails
        """
        pass
```

---

## Error Handling

### Exception Hierarchy

```python
# medallion/exceptions.py

class MedallionError(Exception):
    """Base exception for medallion operations."""
    pass

class MedallionValidationError(MedallionError):
    """Raised when medallion schema validation fails."""
    pass

class StoreError(MedallionError):
    """Base exception for store operations."""
    pass

class StoreNotFoundError(StoreError):
    """Raised when medallion not found in store."""
    pass

class StoreConflictError(StoreError):
    """Raised when creating medallion with duplicate ID."""
    pass
```

### Error Scenarios

| Operation | Condition | Exception |
|-----------|-----------|-----------|
| `create()` | Invalid schema | `MedallionValidationError` |
| `create()` | Duplicate ID | `StoreConflictError` |
| `create()` | SQL error | `StoreError` |
| `update()` | Invalid schema | `MedallionValidationError` |
| `update()` | ID not found | `StoreNotFoundError` |
| `update()` | SQL error | `StoreError` |
| `get_by_id()` | ID not found | Returns `None` (not an exception) |
| `get_by_id()` | SQL/JSON error | `StoreError` |
| `get_latest_for_scope()` | No matches | Returns `[]` (not an exception) |
| `get_latest_for_scope()` | SQL/JSON error | `StoreError` |

---

## Testing Contract

### Unit Tests (Mocked)

- Test `MedallionStore` interface with mock implementation
- Verify all methods are called with correct parameters
- Verify exceptions are raised correctly

### Integration Tests (Real SQLite)

- Test `SQLiteMedallionStore` with in-memory SQLite database
- Test schema creation
- Test CRUD operations (create, update, get_by_id, get_latest_for_scope)
- Test scope matching logic (exact match, subset match, empty scope)
- Test error handling (duplicate ID, not found, invalid JSON)
- Test concurrent access (if needed for v1)

---

## Database Schema

See `data-model.md` for detailed database schema. Key points:
- Table: `medallions`
- Primary key: `id` (medallion_id)
- Indexes: `status`, `updated_at` (for scope queries)
- JSON storage: `content_json` (full Medallion JSON)
- Indexed fields: `scope_graph_nodes`, `scope_tags` (for query matching)

