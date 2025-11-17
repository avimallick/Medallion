"""Contract tests for Medallion schema validation against PRD schema."""

from datetime import datetime

import pytest

from medallion.types import (
    Medallion,
    MedallionAffordances,
    MedallionDecision,
    MedallionMeta,
    MedallionOpenQuestion,
    MedallionScope,
    MedallionSummary,
    Subsystem,
)


class TestSchemaContract:
    """Contract tests ensuring schema matches PRD specification."""

    def test_medallion_schema_has_all_required_fields(self) -> None:
        """Test that Medallion has all required fields from PRD."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        summary = MedallionSummary(
            high_level="Test summary",
            subsystems=[],
        )
        affordances = MedallionAffordances()

        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=[],
            open_questions=[],
            affordances=affordances,
        )

        # Verify all required top-level fields exist
        assert hasattr(medallion, "meta")
        assert hasattr(medallion, "scope")
        assert hasattr(medallion, "summary")
        assert hasattr(medallion, "decisions")
        assert hasattr(medallion, "open_questions")
        assert hasattr(medallion, "affordances")

    def test_medallion_meta_has_all_required_fields(self) -> None:
        """Test that MedallionMeta has all required fields from PRD."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )

        # Verify all required fields exist
        assert hasattr(meta, "medallion_id")
        assert hasattr(meta, "schema_version")
        assert hasattr(meta, "model")
        assert hasattr(meta, "created_at")
        assert hasattr(meta, "updated_at")
        assert hasattr(meta, "status")
        # Optional fields
        assert hasattr(meta, "knowledge_min_ts")
        assert hasattr(meta, "knowledge_max_ts")

    def test_medallion_scope_has_required_fields(self) -> None:
        """Test that MedallionScope has required fields from PRD."""
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        assert hasattr(scope, "graph_nodes")
        assert hasattr(scope, "tags")
        assert isinstance(scope.graph_nodes, list)
        assert isinstance(scope.tags, list)

    def test_medallion_decision_has_required_fields(self) -> None:
        """Test that MedallionDecision has required fields from PRD."""
        decision = MedallionDecision(
            id="D-001",
            statement="Test statement",
            rationale="Test rationale",
            confidence=0.9,
        )
        assert hasattr(decision, "id")
        assert hasattr(decision, "statement")
        assert hasattr(decision, "rationale")
        assert hasattr(decision, "confidence")

    def test_medallion_open_question_has_required_fields(self) -> None:
        """Test that MedallionOpenQuestion has required fields from PRD."""
        question = MedallionOpenQuestion(
            id="Q-001",
            question="Test question",
            blocked_on=["benchmark"],
            priority="medium",
        )
        assert hasattr(question, "id")
        assert hasattr(question, "question")
        assert hasattr(question, "blocked_on")
        assert hasattr(question, "priority")

    def test_medallion_affordances_has_required_fields(self) -> None:
        """Test that MedallionAffordances has required fields from PRD."""
        affordances = MedallionAffordances(
            recommended_entry_points=["Start here"],
            avoid_repeating=["Don't do this"],
            invariants=["Always validate"],
        )
        assert hasattr(affordances, "recommended_entry_points")
        assert hasattr(affordances, "avoid_repeating")
        assert hasattr(affordances, "invariants")

    def test_medallion_summary_has_required_fields(self) -> None:
        """Test that MedallionSummary has required fields from PRD."""
        summary = MedallionSummary(
            high_level="Test summary",
            subsystems=[
                Subsystem(
                    name="Store",
                    status="stable",
                    notes="SQLite backend",
                )
            ],
        )
        assert hasattr(summary, "high_level")
        assert hasattr(summary, "subsystems")
        assert isinstance(summary.subsystems, list)

    def test_subsystem_has_required_fields(self) -> None:
        """Test that Subsystem has required fields from PRD."""
        subsystem = Subsystem(
            name="Store",
            status="stable",
            notes="SQLite backend",
        )
        assert hasattr(subsystem, "name")
        assert hasattr(subsystem, "status")
        assert hasattr(subsystem, "notes")

    def test_full_medallion_contract(self) -> None:
        """Test full medallion structure matches PRD contract."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-001",
            schema_version="medallion.v1",
            model="gpt-4",
            created_at=now,
            updated_at=now,
            status="active",
        )
        scope = MedallionScope(
            graph_nodes=["repo:muse", "module:cli"],
            tags=["project_state", "refactor_sprint_1"],
        )
        summary = MedallionSummary(
            high_level="Project Muse is a semantic checkpointing system...",
            subsystems=[
                Subsystem(
                    name="Store",
                    status="stable",
                    notes="SQLite backend implemented",
                )
            ],
        )
        decisions = [
            MedallionDecision(
                id="D-001",
                statement="Use Python 3.11+",
                rationale="Modern type hints and async support",
                confidence=0.9,
            )
        ]
        open_questions = [
            MedallionOpenQuestion(
                id="Q-001",
                question="Should we add vector search?",
                blocked_on=["performance_benchmark"],
                priority="medium",
            )
        ]
        affordances = MedallionAffordances(
            recommended_entry_points=["Start from types.py"],
            avoid_repeating=["Do not re-scan entire repo"],
            invariants=["Always validate schema before storage"],
        )

        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=decisions,
            open_questions=open_questions,
            affordances=affordances,
        )

        # Verify complete structure
        assert medallion.meta.schema_version == "medallion.v1"
        assert len(medallion.scope.graph_nodes) == 2
        assert len(medallion.decisions) == 1
        assert len(medallion.open_questions) == 1
        assert medallion.decisions[0].confidence == 0.9
        assert medallion.open_questions[0].priority == "medium"

        # Verify JSON serialization works (human-inspectable requirement)
        json_str = medallion.model_dump_json()
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Verify JSON deserialization works (machine-consumable requirement)
        deserialized = Medallion.model_validate_json(json_str)
        assert deserialized.meta.medallion_id == "med-001"

