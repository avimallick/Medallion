"""Unit tests for MedallionLLM stub implementation."""

from datetime import datetime

import pytest

from medallion.llm import StubMedallionLLM
from medallion.types import (
    Evidence,
    LLMError,
    Medallion,
    MedallionScope,
    MedallionSummary,
)


@pytest.fixture
def llm() -> StubMedallionLLM:
    """Create a stub LLM instance for testing."""
    return StubMedallionLLM()


@pytest.fixture
def sample_scope() -> MedallionScope:
    """Create a sample scope for testing."""
    return MedallionScope(
        graph_nodes=["repo:muse", "module:cli"],
        tags=["project_state"],
    )


@pytest.fixture
def sample_evidence() -> Evidence:
    """Create sample evidence for testing."""
    return Evidence(
        session_summary="Test session summary",
        transcripts=["transcript 1", "transcript 2"],
        artefacts={"key": "value"},
    )


class TestStubMedallionLLMGenerate:
    """Tests for StubMedallionLLM.generate()."""

    @pytest.mark.asyncio
    async def test_generate_returns_valid_medallion(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that generate returns a valid medallion."""
        medallion = await llm.generate(sample_scope, sample_evidence)
        assert isinstance(medallion, Medallion)
        assert medallion.meta.medallion_id.startswith("med-")
        assert medallion.meta.schema_version == "medallion.v1"
        assert medallion.meta.status == "active"
        assert medallion.meta.model == "stub-llm"

    @pytest.mark.asyncio
    async def test_generate_preserves_scope(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that generate preserves the input scope."""
        medallion = await llm.generate(sample_scope, sample_evidence)
        assert medallion.scope.graph_nodes == sample_scope.graph_nodes
        assert medallion.scope.tags == sample_scope.tags

    @pytest.mark.asyncio
    async def test_generate_uses_session_summary(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
    ) -> None:
        """Test that generate uses evidence.session_summary."""
        evidence = Evidence(session_summary="Custom summary text")
        medallion = await llm.generate(sample_scope, evidence)
        assert medallion.summary.high_level == "Custom summary text"

    @pytest.mark.asyncio
    async def test_generate_creates_empty_decisions_and_questions(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that generate creates empty decisions and questions (stub behavior)."""
        medallion = await llm.generate(sample_scope, sample_evidence)
        assert medallion.decisions == []
        assert medallion.open_questions == []

    @pytest.mark.asyncio
    async def test_generate_sets_timestamps(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that generate sets current timestamps."""
        before = datetime.now()
        medallion = await llm.generate(sample_scope, sample_evidence)
        after = datetime.now()

        assert before <= medallion.meta.created_at <= after
        assert before <= medallion.meta.updated_at <= after
        assert medallion.meta.created_at == medallion.meta.updated_at

    @pytest.mark.asyncio
    async def test_generate_raises_error_on_empty_summary(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
    ) -> None:
        """Test that generate raises LLMError on empty session_summary."""
        evidence = Evidence(session_summary="")
        with pytest.raises(LLMError, match="cannot be empty"):
            await llm.generate(sample_scope, evidence)

    @pytest.mark.asyncio
    async def test_generate_raises_error_on_whitespace_only_summary(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
    ) -> None:
        """Test that generate raises LLMError on whitespace-only session_summary."""
        evidence = Evidence(session_summary="   \n\t  ")
        with pytest.raises(LLMError, match="cannot be empty"):
            await llm.generate(sample_scope, evidence)

    @pytest.mark.asyncio
    async def test_generate_schema_compliance(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that generate returns schema-compliant medallion."""
        medallion = await llm.generate(sample_scope, sample_evidence)
        # Verify JSON serialization works (validates schema)
        json_str = medallion.model_dump_json()
        assert isinstance(json_str, str)
        assert len(json_str) > 0


class TestStubMedallionLLMUpdate:
    """Tests for StubMedallionLLM.update()."""

    @pytest.fixture
    async def existing_medallion(
        self,
        llm: StubMedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> Medallion:
        """Create an existing medallion for update tests."""
        return await llm.generate(sample_scope, sample_evidence)

    @pytest.mark.asyncio
    async def test_update_preserves_medallion_id(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update preserves medallion_id."""
        new_evidence = Evidence(session_summary="Updated summary")
        updated = await llm.update(existing_medallion, new_evidence)
        assert updated.meta.medallion_id == existing_medallion.meta.medallion_id

    @pytest.mark.asyncio
    async def test_update_preserves_created_at(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update preserves created_at timestamp."""
        new_evidence = Evidence(session_summary="Updated summary")
        updated = await llm.update(existing_medallion, new_evidence)
        assert updated.meta.created_at == existing_medallion.meta.created_at

    @pytest.mark.asyncio
    async def test_update_changes_updated_at(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update changes updated_at timestamp."""
        import time

        original_updated_at = existing_medallion.meta.updated_at
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        new_evidence = Evidence(session_summary="Updated summary")
        updated = await llm.update(existing_medallion, new_evidence)
        assert updated.meta.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_update_raises_error_on_empty_summary(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update raises LLMError on empty session_summary."""
        new_evidence = Evidence(session_summary="")
        with pytest.raises(LLMError, match="cannot be empty"):
            await llm.update(existing_medallion, new_evidence)

    @pytest.mark.asyncio
    async def test_update_raises_error_on_whitespace_only_summary(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update raises LLMError on whitespace-only session_summary."""
        new_evidence = Evidence(session_summary="   \n\t  ")
        with pytest.raises(LLMError, match="cannot be empty"):
            await llm.update(existing_medallion, new_evidence)

    @pytest.mark.asyncio
    async def test_update_schema_compliance(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update returns schema-compliant medallion."""
        new_evidence = Evidence(session_summary="Updated summary")
        updated = await llm.update(existing_medallion, new_evidence)
        # Verify JSON serialization works (validates schema)
        json_str = updated.model_dump_json()
        assert isinstance(json_str, str)

    @pytest.mark.asyncio
    async def test_update_preserves_other_fields(
        self,
        llm: StubMedallionLLM,
        existing_medallion: Medallion,
    ) -> None:
        """Test that update preserves other fields (stub behavior - no merging)."""
        new_evidence = Evidence(session_summary="Updated summary")
        updated = await llm.update(existing_medallion, new_evidence)
        # Stub doesn't merge content, so these should be unchanged
        assert updated.scope == existing_medallion.scope
        assert updated.summary == existing_medallion.summary
        assert updated.decisions == existing_medallion.decisions
        assert updated.open_questions == existing_medallion.open_questions

