"""Unit tests for Medallion type definitions."""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from medallion.types import (
    Evidence,
    Medallion,
    MedallionAffordances,
    MedallionDecision,
    MedallionMeta,
    MedallionOpenQuestion,
    MedallionScope,
    MedallionSummary,
    Priority,
    Subsystem,
    SubsystemStatus,
)


class TestMedallionScope:
    """Tests for MedallionScope model."""

    def test_create_with_graph_nodes_and_tags(self) -> None:
        """Test creating scope with graph nodes and tags."""
        scope = MedallionScope(
            graph_nodes=["repo:muse", "module:cli"],
            tags=["project_state", "refactor_sprint_1"],
        )
        assert scope.graph_nodes == ["repo:muse", "module:cli"]
        assert scope.tags == ["project_state", "refactor_sprint_1"]

    def test_create_with_empty_arrays(self) -> None:
        """Test creating scope with empty arrays (allowed)."""
        scope = MedallionScope()
        assert scope.graph_nodes == []
        assert scope.tags == []

    def test_create_with_only_graph_nodes(self) -> None:
        """Test creating scope with only graph nodes."""
        scope = MedallionScope(graph_nodes=["repo:muse"])
        assert scope.graph_nodes == ["repo:muse"]
        assert scope.tags == []

    def test_create_with_only_tags(self) -> None:
        """Test creating scope with only tags."""
        scope = MedallionScope(tags=["project_state"])
        assert scope.graph_nodes == []
        assert scope.tags == ["project_state"]


class TestMedallionDecision:
    """Tests for MedallionDecision model."""

    def test_create_valid_decision(self) -> None:
        """Test creating a valid decision."""
        decision = MedallionDecision(
            id="D-001",
            statement="Use Python 3.11+",
            rationale="Modern type hints and async support",
            confidence=0.9,
        )
        assert decision.id == "D-001"
        assert decision.statement == "Use Python 3.11+"
        assert decision.confidence == 0.9

    def test_confidence_minimum(self) -> None:
        """Test confidence at minimum value (0.0)."""
        decision = MedallionDecision(
            id="D-001",
            statement="Test",
            rationale="Test",
            confidence=0.0,
        )
        assert decision.confidence == 0.0

    def test_confidence_maximum(self) -> None:
        """Test confidence at maximum value (1.0)."""
        decision = MedallionDecision(
            id="D-001",
            statement="Test",
            rationale="Test",
            confidence=1.0,
        )
        assert decision.confidence == 1.0

    def test_confidence_below_minimum(self) -> None:
        """Test confidence below 0.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MedallionDecision(
                id="D-001",
                statement="Test",
                rationale="Test",
                confidence=-0.1,
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("confidence",) and error["type"] == "greater_than_equal"
            for error in errors
        )

    def test_confidence_above_maximum(self) -> None:
        """Test confidence above 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            MedallionDecision(
                id="D-001",
                statement="Test",
                rationale="Test",
                confidence=1.1,
            )
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("confidence",) and error["type"] == "less_than_equal"
            for error in errors
        )

    def test_confidence_field_validator(self) -> None:
        """Test custom field validator for confidence."""
        # Valid values should pass
        decision1 = MedallionDecision(
            id="D-001", statement="Test", rationale="Test", confidence=0.5
        )
        assert decision1.confidence == 0.5


class TestMedallionOpenQuestion:
    """Tests for MedallionOpenQuestion model."""

    def test_create_valid_question(self) -> None:
        """Test creating a valid question."""
        question = MedallionOpenQuestion(
            id="Q-001",
            question="Should we add vector search?",
            blocked_on=["performance_benchmark"],
            priority="medium",
        )
        assert question.id == "Q-001"
        assert question.question == "Should we add vector search?"
        assert question.priority == "medium"
        assert question.blocked_on == ["performance_benchmark"]

    def test_priority_values(self) -> None:
        """Test all valid priority values."""
        for priority in ["low", "medium", "high"]:
            question = MedallionOpenQuestion(
                id="Q-001",
                question="Test",
                priority=priority,
            )
            assert question.priority == priority

    def test_invalid_priority(self) -> None:
        """Test invalid priority raises ValidationError."""
        with pytest.raises(ValidationError):
            MedallionOpenQuestion(
                id="Q-001",
                question="Test",
                priority="invalid",  # type: ignore[arg-type]
            )

    def test_empty_blocked_on(self) -> None:
        """Test empty blocked_on list (allowed)."""
        question = MedallionOpenQuestion(
            id="Q-001",
            question="Test",
            priority="low",
            blocked_on=[],
        )
        assert question.blocked_on == []


class TestMedallionMeta:
    """Tests for MedallionMeta model."""

    def test_create_valid_meta(self) -> None:
        """Test creating valid metadata."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        assert meta.medallion_id == "med-001"
        assert meta.schema_version == "medallion.v1"
        assert meta.status == "active"
        assert meta.created_at == now
        assert meta.updated_at == now

    def test_updated_at_after_created_at(self) -> None:
        """Test updated_at after created_at is valid."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        updated = datetime(2025, 1, 1, 13, 0, 0)
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=created,
            updated_at=updated,
        )
        assert meta.updated_at > meta.created_at

    def test_updated_at_same_as_created_at(self) -> None:
        """Test updated_at same as created_at is valid."""
        now = datetime(2025, 1, 1, 12, 0, 0)
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        assert meta.updated_at == meta.created_at

    def test_updated_at_before_created_at_raises_error(self) -> None:
        """Test updated_at before created_at raises ValidationError."""
        created = datetime(2025, 1, 1, 13, 0, 0)
        updated = datetime(2025, 1, 1, 12, 0, 0)
        with pytest.raises(ValidationError) as exc_info:
            MedallionMeta(
                medallion_id="med-001",
                model="gpt-4",
                created_at=created,
                updated_at=updated,
            )
        errors = exc_info.value.errors()
        assert any("updated_at must be >= created_at" in str(error) for error in errors)

    def test_status_values(self) -> None:
        """Test all valid status values."""
        now = datetime.now()
        for status in ["active", "stale", "superseded"]:
            meta = MedallionMeta(
                medallion_id="med-001",
                model="gpt-4",
                created_at=now,
                updated_at=now,
                status=status,
            )
            assert meta.status == status

    def test_optional_knowledge_timestamps(self) -> None:
        """Test optional knowledge timestamps."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
            knowledge_min_ts=datetime(2025, 1, 1),
            knowledge_max_ts=datetime(2025, 1, 2),
        )
        assert meta.knowledge_min_ts is not None
        assert meta.knowledge_max_ts is not None


class TestMedallionJSONSerialization:
    """Tests for Medallion JSON serialization and deserialization."""

    def create_sample_medallion(self) -> Medallion:
        """Create a sample medallion for testing."""
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
        return Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=[],
            open_questions=[],
            affordances=affordances,
        )

    def test_serialize_to_json(self) -> None:
        """Test serializing medallion to JSON."""
        medallion = self.create_sample_medallion()
        json_str = medallion.model_dump_json()
        assert isinstance(json_str, str)
        assert "med-001" in json_str
        assert "repo:muse" in json_str

    def test_deserialize_from_json(self) -> None:
        """Test deserializing medallion from JSON."""
        medallion = self.create_sample_medallion()
        json_str = medallion.model_dump_json()
        deserialized = Medallion.model_validate_json(json_str)
        assert deserialized.meta.medallion_id == medallion.meta.medallion_id
        assert deserialized.scope.graph_nodes == medallion.scope.graph_nodes

    def test_json_round_trip(self) -> None:
        """Test JSON round-trip preserves all fields."""
        medallion = self.create_sample_medallion()
        json_str = medallion.model_dump_json()
        deserialized = Medallion.model_validate_json(json_str)
        assert deserialized.model_dump() == medallion.model_dump()

    def test_serialize_with_indentation(self) -> None:
        """Test serializing with indentation for readability."""
        medallion = self.create_sample_medallion()
        json_str = medallion.model_dump_json(indent=2)
        assert isinstance(json_str, str)
        # Check for newlines indicating indentation
        assert "\n" in json_str

    def test_deserialize_with_decisions_and_questions(self) -> None:
        """Test deserializing medallion with decisions and questions."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-002",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        scope = MedallionScope(graph_nodes=["repo:test"], tags=["test"])
        summary = MedallionSummary(high_level="Test", subsystems=[])
        decisions = [
            MedallionDecision(
                id="D-001",
                statement="Use Python 3.11+",
                rationale="Modern features",
                confidence=0.9,
            )
        ]
        open_questions = [
            MedallionOpenQuestion(
                id="Q-001",
                question="Should we add vector search?",
                blocked_on=["benchmark"],
                priority="medium",
            )
        ]
        affordances = MedallionAffordances()
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=decisions,
            open_questions=open_questions,
            affordances=affordances,
        )
        json_str = medallion.model_dump_json()
        deserialized = Medallion.model_validate_json(json_str)
        assert len(deserialized.decisions) == 1
        assert len(deserialized.open_questions) == 1
        assert deserialized.decisions[0].id == "D-001"
        assert deserialized.open_questions[0].id == "Q-001"


class TestEvidence:
    """Tests for Evidence model."""

    def test_create_with_required_fields(self) -> None:
        """Test creating evidence with required fields only."""
        evidence = Evidence(session_summary="Test session")
        assert evidence.session_summary == "Test session"
        assert evidence.transcripts is None
        assert evidence.artefacts is None

    def test_create_with_all_fields(self) -> None:
        """Test creating evidence with all fields."""
        evidence = Evidence(
            session_summary="Test session",
            transcripts=["transcript 1", "transcript 2"],
            artefacts={"key": "value"},
        )
        assert evidence.session_summary == "Test session"
        assert evidence.transcripts == ["transcript 1", "transcript 2"]
        assert evidence.artefacts == {"key": "value"}

    def test_empty_session_summary_allowed(self) -> None:
        """Test empty session_summary is allowed (validation at application level)."""
        evidence = Evidence(session_summary="")
        assert evidence.session_summary == ""

