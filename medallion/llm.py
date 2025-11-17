"""
LLM interface and stub implementation for medallion generation/update.

This module provides the MedallionLLM Protocol for LLM-based medallion operations
and a stub implementation for testing.
"""

import uuid
from datetime import datetime
from typing import Protocol

from medallion.types import (
    Evidence,
    LLMError,
    Medallion,
    MedallionAffordances,
    MedallionMeta,
    MedallionScope,
    MedallionSummary,
)


class MedallionLLM(Protocol):
    """Abstract interface for LLM-based medallion operations."""

    async def generate(
        self,
        scope: MedallionScope,
        evidence: Evidence,
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
        new_evidence: Evidence,
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


class StubMedallionLLM:
    """Stub implementation of MedallionLLM for testing."""

    async def generate(
        self,
        scope: MedallionScope,
        evidence: Evidence,
    ) -> Medallion:
        """
        Generate a mock medallion (stub implementation).

        Returns a minimal valid medallion with:
        - Generated ID
        - Scope from input
        - Summary from evidence.session_summary
        - Empty decisions, open_questions
        - Default affordances

        Args:
            scope: The scope this medallion applies to
            evidence: Evidence data (session_summary, transcripts, artefacts)

        Returns:
            A minimal valid medallion

        Raises:
            LLMError: If evidence.session_summary is empty
        """
        if not evidence.session_summary or not evidence.session_summary.strip():
            raise LLMError("Evidence session_summary cannot be empty")

        now = datetime.now()
        medallion_id = f"med-{uuid.uuid4().hex[:12]}"

        meta = MedallionMeta(
            medallion_id=medallion_id,
            schema_version="medallion.v1",
            model="stub-llm",
            created_at=now,
            updated_at=now,
            status="active",
        )

        summary = MedallionSummary(
            high_level=evidence.session_summary[:300],  # Respect max_length
            subsystems=[],
        )

        affordances = MedallionAffordances(
            recommended_entry_points=[],
            avoid_repeating=[],
            invariants=None,
        )

        return Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=[],
            open_questions=[],
            affordances=affordances,
        )

    async def update(
        self,
        existing: Medallion,
        new_evidence: Evidence,
    ) -> Medallion:
        """
        Return existing medallion with updated timestamp (stub).

        In real implementation, this would call LLM to merge new evidence.
        This stub just updates the timestamp to simulate an update.

        Args:
            existing: The existing medallion to update
            new_evidence: New evidence (ignored in stub)

        Returns:
            Existing medallion with updated_at changed to current time

        Raises:
            LLMError: If new_evidence.session_summary is empty
        """
        if not new_evidence.session_summary or not new_evidence.session_summary.strip():
            raise LLMError("Evidence session_summary cannot be empty")

        now = datetime.now()

        # Create updated meta with new timestamp but preserved created_at
        updated_meta = MedallionMeta(
            medallion_id=existing.meta.medallion_id,
            schema_version=existing.meta.schema_version,
            model=existing.meta.model,
            created_at=existing.meta.created_at,  # Preserve original
            updated_at=now,  # Update to current time
            status=existing.meta.status,
            knowledge_min_ts=existing.meta.knowledge_min_ts,
            knowledge_max_ts=existing.meta.knowledge_max_ts,
        )

        # Return medallion with updated meta (stub - no actual merging of content)
        return Medallion(
            meta=updated_meta,
            scope=existing.scope,
            summary=existing.summary,
            decisions=existing.decisions,
            open_questions=existing.open_questions,
            affordances=existing.affordances,
        )

