"""
Medallion data types and schema definitions.

This module contains all Pydantic models for the Medallion schema,
including validation rules and custom exceptions.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# Type aliases for better type safety
Priority = Literal["low", "medium", "high"]
SubsystemStatus = Literal["unknown", "stable", "in_progress", "deprecated"]
MedallionStatus = Literal["active", "stale", "superseded"]


# Custom Exceptions
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


# Core Types
class MedallionScope(BaseModel):
    """Scope defining what a medallion applies to."""

    graph_nodes: List[str] = Field(
        default_factory=list,
        description="Array of graph node IDs (e.g., ['repo:muse', 'module:cli'])",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Array of tags for categorization (e.g., ['project_state', 'refactor_sprint_1'])",
    )


class MedallionDecision(BaseModel):
    """A canonical decision about the scope."""

    id: str = Field(description="Unique decision ID (e.g., 'D-001')")
    statement: str = Field(description="Canonical decision text")
    rationale: str = Field(description="Short explanation of why this decision was made")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level from 0.0 to 1.0",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class MedallionOpenQuestion(BaseModel):
    """An unresolved question about the scope."""

    id: str = Field(description="Unique question ID (e.g., 'Q-003')")
    question: str = Field(description="The question text")
    blocked_on: List[str] = Field(
        default_factory=list,
        description="List of dependencies blocking resolution (e.g., ['benchmark', 'team_input'])",
    )
    priority: Priority = Field(description="Priority level: low, medium, or high")


class MedallionAffordances(BaseModel):
    """Guidance for how agents should use this medallion."""

    recommended_entry_points: List[str] = Field(
        default_factory=list,
        description="Suggested starting points (e.g., ['Start from module:llm-router'])",
    )
    avoid_repeating: List[str] = Field(
        default_factory=list,
        description="Actions to avoid repeating (e.g., ['Do not re-run full repo scan'])",
    )
    invariants: Optional[List[str]] = Field(
        default=None,
        description="Optional rules agents must obey",
    )


class Subsystem(BaseModel):
    """Subsystem status information."""

    name: str = Field(description="Subsystem name")
    status: SubsystemStatus = Field(description="Current status of the subsystem")
    notes: str = Field(description="Additional notes about the subsystem")


class MedallionSummary(BaseModel):
    """High-level summary of the scope."""

    high_level: str = Field(
        max_length=300,
        description="High-level summary (<= 300 tokens recommended)",
    )
    subsystems: List[Subsystem] = Field(
        default_factory=list,
        description="List of subsystems with their status",
    )


class MedallionMeta(BaseModel):
    """Metadata about the medallion."""

    medallion_id: str = Field(description="Unique identifier for this medallion")
    schema_version: str = Field(
        default="medallion.v1",
        description="Schema version (e.g., 'medallion.v1')",
    )
    model: str = Field(description="Model used to generate/update this medallion")
    created_at: datetime = Field(description="ISO 8601 timestamp of creation")
    updated_at: datetime = Field(description="ISO 8601 timestamp of last update")
    knowledge_min_ts: Optional[datetime] = Field(
        default=None,
        description="Earliest data timestamp covered by this medallion",
    )
    knowledge_max_ts: Optional[datetime] = Field(
        default=None,
        description="Latest data timestamp covered (e.g., repo commit time)",
    )
    status: MedallionStatus = Field(
        default="active",
        description="Current status: active, stale, or superseded",
    )

    @model_validator(mode="after")
    def validate_timestamps(self) -> "MedallionMeta":
        """Ensure updated_at is >= created_at."""
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be >= created_at")
        return self


class Medallion(BaseModel):
    """A semantic checkpoint for LLM agents."""

    meta: MedallionMeta = Field(description="Metadata about this medallion")
    scope: MedallionScope = Field(description="Scope this medallion applies to")
    summary: MedallionSummary = Field(description="High-level summary")
    decisions: List[MedallionDecision] = Field(
        default_factory=list,
        description="Canonical decisions made about the scope",
    )
    open_questions: List[MedallionOpenQuestion] = Field(
        default_factory=list,
        description="Unresolved questions about the scope",
    )
    affordances: MedallionAffordances = Field(description="Guidance for agent usage")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "meta": {
                    "medallion_id": "med-001",
                    "schema_version": "medallion.v1",
                    "model": "gpt-4",
                    "created_at": "2025-01-01T12:00:00Z",
                    "updated_at": "2025-01-01T12:00:00Z",
                    "status": "active",
                },
                "scope": {
                    "graph_nodes": ["repo:muse"],
                    "tags": ["project_state"],
                },
                "summary": {
                    "high_level": "Project Muse is a semantic checkpointing system...",
                    "subsystems": [
                        {
                            "name": "Store",
                            "status": "stable",
                            "notes": "SQLite backend implemented",
                        }
                    ],
                },
                "decisions": [
                    {
                        "id": "D-001",
                        "statement": "Use Python 3.11+",
                        "rationale": "Modern type hints and async support",
                        "confidence": 0.9,
                    }
                ],
                "open_questions": [
                    {
                        "id": "Q-001",
                        "question": "Should we add vector search?",
                        "blocked_on": ["performance_benchmark"],
                        "priority": "medium",
                    }
                ],
                "affordances": {
                    "recommended_entry_points": ["Start from types.py"],
                    "avoid_repeating": ["Do not re-scan entire repo"],
                    "invariants": ["Always validate schema before storage"],
                },
            }
        }

    def model_dump_json(self, *, indent: int = 2, **kwargs: Any) -> str:
        """
        Serialize medallion to JSON string.

        Args:
            indent: JSON indentation level (default: 2 for readability)
            **kwargs: Additional arguments passed to Pydantic's model_dump_json

        Returns:
            JSON string representation of the medallion
        """
        return super().model_dump_json(indent=indent, **kwargs)

    @classmethod
    def model_validate_json(cls, json_data: str | bytes, **kwargs: Any) -> "Medallion":
        """
        Deserialize medallion from JSON string.

        Args:
            json_data: JSON string or bytes to parse
            **kwargs: Additional arguments passed to Pydantic's model_validate_json

        Returns:
            Medallion instance

        Raises:
            ValidationError: If JSON does not conform to Medallion schema
        """
        return super().model_validate_json(json_data, **kwargs)


class Evidence(BaseModel):
    """Evidence data for generating or updating a medallion."""

    session_summary: str = Field(
        description="High-level description of what happened this session"
    )
    transcripts: Optional[List[str]] = Field(
        default=None,
        description="Optional list of important conversation segments or planner steps",
    )
    artefacts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured info (e.g., file diffs, test results)",
    )

