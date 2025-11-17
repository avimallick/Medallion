# Data Model: Medallion Library v1

**Date**: 2025-11-17  
**Feature**: Medallion Library v1

## Overview

The Medallion data model consists of Pydantic models for type safety and runtime validation. All models are JSON-serializable and human-inspectable, conforming to the schema defined in the PRD.

## Core Types

### MedallionScope

Defines what a medallion applies to (graph nodes and tags).

```python
from typing import List
from pydantic import BaseModel, Field

class MedallionScope(BaseModel):
    """Scope defining what a medallion applies to."""
    graph_nodes: List[str] = Field(
        default_factory=list,
        description="Array of graph node IDs (e.g., ['repo:muse', 'module:cli'])"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Array of tags for categorization (e.g., ['project_state', 'refactor_sprint_1'])"
    )
```

**Validation Rules**:
- `graph_nodes` and `tags` are both arrays of strings
- Empty arrays are allowed
- No duplicates enforced (enforced at application level if needed)

### MedallionDecision

Represents a canonical decision made about the scope.

```python
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class MedallionDecision(BaseModel):
    """A canonical decision about the scope."""
    id: str = Field(description="Unique decision ID (e.g., 'D-001')")
    statement: str = Field(description="Canonical decision text")
    rationale: str = Field(description="Short explanation of why this decision was made")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level from 0.0 to 1.0"
    )

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
```

**Validation Rules**:
- `confidence` must be between 0.0 and 1.0
- `id`, `statement`, `rationale` are required strings

### MedallionOpenQuestion

Represents an unresolved question about the scope.

```python
from typing import Literal
from pydantic import BaseModel, Field

Priority = Literal["low", "medium", "high"]

class MedallionOpenQuestion(BaseModel):
    """An unresolved question about the scope."""
    id: str = Field(description="Unique question ID (e.g., 'Q-003')")
    question: str = Field(description="The question text")
    blocked_on: List[str] = Field(
        default_factory=list,
        description="List of dependencies blocking resolution (e.g., ['benchmark', 'team_input'])"
    )
    priority: Priority = Field(description="Priority level: low, medium, or high")
```

**Validation Rules**:
- `priority` must be one of "low", "medium", "high"
- `blocked_on` is an array of strings (can be empty)

### MedallionAffordances

Guidance for how agents should use this medallion.

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class MedallionAffordances(BaseModel):
    """Guidance for how agents should use this medallion."""
    recommended_entry_points: List[str] = Field(
        default_factory=list,
        description="Suggested starting points (e.g., ['Start from module:llm-router'])"
    )
    avoid_repeating: List[str] = Field(
        default_factory=list,
        description="Actions to avoid repeating (e.g., ['Do not re-run full repo scan'])"
    )
    invariants: Optional[List[str]] = Field(
        default=None,
        description="Optional rules agents must obey"
    )
```

**Validation Rules**:
- `invariants` is optional (can be None)
- All other fields are arrays of strings (can be empty)

### MedallionSummary

High-level summary and subsystem status.

```python
from typing import List, Literal
from pydantic import BaseModel, Field

SubsystemStatus = Literal["unknown", "stable", "in_progress", "deprecated"]

class Subsystem(BaseModel):
    """Subsystem status information."""
    name: str = Field(description="Subsystem name")
    status: SubsystemStatus = Field(description="Current status of the subsystem")
    notes: str = Field(description="Additional notes about the subsystem")

class MedallionSummary(BaseModel):
    """High-level summary of the scope."""
    high_level: str = Field(
        max_length=300,
        description="High-level summary (<= 300 tokens recommended)"
    )
    subsystems: List[Subsystem] = Field(
        default_factory=list,
        description="List of subsystems with their status"
    )
```

**Validation Rules**:
- `high_level` is required string (length constraint is advisory)
- `subsystems` is an array (can be empty)
- `status` must be one of the defined values

### MedallionMeta

Metadata about the medallion itself.

```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

MedallionStatus = Literal["active", "stale", "superseded"]

class MedallionMeta(BaseModel):
    """Metadata about the medallion."""
    medallion_id: str = Field(description="Unique identifier for this medallion")
    schema_version: str = Field(
        default="medallion.v1",
        description="Schema version (e.g., 'medallion.v1')"
    )
    model: str = Field(description="Model used to generate/update this medallion")
    created_at: datetime = Field(description="ISO 8601 timestamp of creation")
    updated_at: datetime = Field(description="ISO 8601 timestamp of last update")
    knowledge_min_ts: Optional[datetime] = Field(
        default=None,
        description="Earliest data timestamp covered by this medallion"
    )
    knowledge_max_ts: Optional[datetime] = Field(
        default=None,
        description="Latest data timestamp covered (e.g., repo commit time)"
    )
    status: MedallionStatus = Field(
        default="active",
        description="Current status: active, stale, or superseded"
    )

    @field_validator('updated_at')
    @classmethod
    def updated_at_after_created_at(cls, v: datetime, info) -> datetime:
        """Ensure updated_at is >= created_at."""
        if 'created_at' in info.data and v < info.data['created_at']:
            raise ValueError("updated_at must be >= created_at")
        return v
```

**Validation Rules**:
- `schema_version` defaults to "medallion.v1" for v1
- `created_at` and `updated_at` are datetime objects (ISO 8601 strings in JSON)
- `updated_at` must be >= `created_at`
- `status` must be one of "active", "stale", "superseded"
- `knowledge_min_ts` and `knowledge_max_ts` are optional datetime

### Medallion

The complete medallion structure.

```python
from pydantic import BaseModel, Field

class Medallion(BaseModel):
    """A semantic checkpoint for LLM agents."""
    meta: MedallionMeta = Field(description="Metadata about this medallion")
    scope: MedallionScope = Field(description="Scope this medallion applies to")
    summary: MedallionSummary = Field(description="High-level summary")
    decisions: List[MedallionDecision] = Field(
        default_factory=list,
        description="Canonical decisions made about the scope"
    )
    open_questions: List[MedallionOpenQuestion] = Field(
        default_factory=list,
        description="Unresolved questions about the scope"
    )
    affordances: MedallionAffordances = Field(description="Guidance for agent usage")

    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "medallion_id": "med-001",
                    "schema_version": "medallion.v1",
                    "model": "gpt-4",
                    "created_at": "2025-01-01T12:00:00Z",
                    "updated_at": "2025-01-01T12:00:00Z",
                    "status": "active"
                },
                "scope": {
                    "graph_nodes": ["repo:muse"],
                    "tags": ["project_state"]
                },
                "summary": {
                    "high_level": "Project Muse is a semantic checkpointing system...",
                    "subsystems": [
                        {
                            "name": "Store",
                            "status": "stable",
                            "notes": "SQLite backend implemented"
                        }
                    ]
                },
                "decisions": [
                    {
                        "id": "D-001",
                        "statement": "Use Python 3.11+",
                        "rationale": "Modern type hints and async support",
                        "confidence": 0.9
                    }
                ],
                "open_questions": [
                    {
                        "id": "Q-001",
                        "question": "Should we add vector search?",
                        "blocked_on": ["performance_benchmark"],
                        "priority": "medium"
                    }
                ],
                "affordances": {
                    "recommended_entry_points": ["Start from types.py"],
                    "avoid_repeating": ["Do not re-scan entire repo"],
                    "invariants": ["Always validate schema before storage"]
                }
            }
        }
```

**Validation Rules**:
- All top-level fields are required except arrays (which default to empty lists)
- Schema validation happens automatically via Pydantic
- JSON serialization via `.model_dump_json()` and `.model_validate_json()`

## Supporting Types

### Evidence

Input data for medallion generation/update.

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    """Evidence data for generating or updating a medallion."""
    session_summary: str = Field(description="High-level description of what happened this session")
    transcripts: Optional[List[str]] = Field(
        default=None,
        description="Optional list of important conversation segments or planner steps"
    )
    artefacts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured info (e.g., file diffs, test results)"
    )
```

**Validation Rules**:
- `session_summary` is required
- `transcripts` and `artefacts` are optional

## Database Schema

### Table: medallions

```sql
CREATE TABLE medallions (
    id TEXT PRIMARY KEY,                    -- MedallionMeta.medallion_id
    content_json TEXT NOT NULL,             -- Full Medallion JSON
    created_at TEXT NOT NULL,               -- ISO 8601 timestamp
    updated_at TEXT NOT NULL,               -- ISO 8601 timestamp
    status TEXT NOT NULL,                   -- 'active', 'stale', 'superseded'
    scope_graph_nodes TEXT NOT NULL,        -- JSON array of graph nodes
    scope_tags TEXT NOT NULL,               -- JSON array of tags
    knowledge_min_ts TEXT,                  -- ISO 8601 timestamp (nullable)
    knowledge_max_ts TEXT,                  -- ISO 8601 timestamp (nullable)
    schema_version TEXT NOT NULL DEFAULT 'medallion.v1'
);

-- Indexes for efficient scope queries
CREATE INDEX idx_medallions_status ON medallions(status);
CREATE INDEX idx_medallions_updated_at ON medallions(updated_at DESC);
CREATE INDEX idx_medallions_scope_nodes ON medallions(scope_graph_nodes);
CREATE INDEX idx_medallions_scope_tags ON medallions(scope_tags);
```

**Storage Strategy**:
- Store full medallion JSON in `content_json` for flexibility
- Store indexed fields separately for efficient querying
- Use SQLite JSON1 extension for JSON operations
- Index `status`, `updated_at`, and scope fields for queries

**Migration Strategy (v1)**:
- No migration needed (initial schema)
- Future versions can add migration scripts
- Schema version stored in both table column and JSON content

## State Transitions

### Medallion Status

- **active**: Default status for newly created or recently updated medallions
- **stale**: Set when medallion is outdated (manual operation, future)
- **superseded**: Set when a new medallion replaces this one (future)

**Transition Rules**:
- New medallions start as "active"
- Status persists during updates (stays "active" unless explicitly changed)
- Status changes are manual (no automatic transitions in v1)

## Validation and Error Handling

### Schema Validation

- Pydantic validates all fields on model creation
- Custom validators enforce business rules (confidence range, timestamp ordering)
- Validation errors raise `pydantic.ValidationError`

### Custom Exceptions

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
```

## Serialization

### JSON Serialization

- `medallion.model_dump_json()`: Serialize to JSON string
- `Medallion.model_validate_json(json_str)`: Deserialize from JSON string
- Datetime objects serialize to ISO 8601 strings
- Human-readable indentation supported

### Database Serialization

- Store full medallion as JSON in `content_json` column
- Store indexed fields as separate columns (for queries)
- Reconstruct medallion from `content_json` on load
