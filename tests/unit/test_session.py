"""Unit tests for session helper functions."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from medallion.llm import MedallionLLM, StubMedallionLLM
from medallion.session import (
    _checkpoint_session_async,
    _load_medallions_for_scope_async,
    checkpoint_session,
    load_medallions_for_scope,
)
from medallion.store import MedallionStore
from medallion.types import (
    Evidence,
    LLMError,
    Medallion,
    MedallionAffordances,
    MedallionMeta,
    MedallionScope,
    MedallionSummary,
    SchemaValidationError,
    StoreError,
)


@pytest.fixture
def mock_store() -> MedallionStore:
    """Create a mock store for testing."""
    store = MagicMock(spec=MedallionStore)
    store.get_latest_for_scope = AsyncMock(return_value=[])
    store.create = AsyncMock()
    store.update = AsyncMock()
    return store


@pytest.fixture
def mock_llm() -> MedallionLLM:
    """Create a mock LLM for testing."""
    llm = MagicMock(spec=MedallionLLM)
    llm.generate = AsyncMock()
    llm.update = AsyncMock()
    return llm


@pytest.fixture
def sample_scope() -> MedallionScope:
    """Create a sample scope for testing."""
    return MedallionScope(
        graph_nodes=["repo:muse"],
        tags=["project_state"],
    )


@pytest.fixture
def sample_evidence() -> Evidence:
    """Create sample evidence for testing."""
    return Evidence(
        session_summary="Test session summary",
        transcripts=[],
        artefacts={},
    )


@pytest.fixture
def sample_medallion() -> Medallion:
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
    return Medallion(
        meta=meta,
        scope=scope,
        summary=summary,
        decisions=[],
        open_questions=[],
        affordances=MedallionAffordances(),
    )


class TestCheckpointSessionNewScope:
    """Tests for checkpoint_session with new scope (no existing medallion)."""

    @pytest.mark.asyncio
    async def test_checkpoint_session_creates_new_medallion(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session creates new medallion when none exists."""
        # Mock: No existing medallions
        mock_store.get_latest_for_scope.return_value = []
        # Mock: LLM generates new medallion
        mock_llm.generate.return_value = sample_medallion

        result = await _checkpoint_session_async(
            mock_store, mock_llm, sample_scope, sample_evidence
        )

        # Verify LLM.generate was called
        mock_llm.generate.assert_called_once_with(sample_scope, sample_evidence)
        # Verify store.create was called with the generated medallion
        mock_store.create.assert_called_once_with(sample_medallion)
        # Verify store.update was NOT called
        mock_store.update.assert_not_called()
        # Verify result
        assert result == sample_medallion

    def test_checkpoint_session_sync_wrapper(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session sync wrapper works (non-async context)."""
        # Note: Testing sync wrapper in sync context (not from async test)
        # The sync wrapper uses asyncio.run(), which cannot be called from async context
        # In real usage, sync wrappers are called from sync code, not from async tests
        mock_store.get_latest_for_scope.return_value = []
        mock_llm.generate.return_value = sample_medallion

        # This will work in sync context (not from async test)
        result = checkpoint_session(
            mock_store, mock_llm, sample_scope, sample_evidence
        )

        assert result == sample_medallion
        mock_store.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_llm_error(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that checkpoint_session handles LLM errors."""
        mock_store.get_latest_for_scope.return_value = []
        mock_llm.generate.side_effect = LLMError("LLM failed")

        with pytest.raises(LLMError, match="Failed to generate medallion"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_store_error_on_create(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session handles store errors on create."""
        mock_store.get_latest_for_scope.return_value = []
        mock_llm.generate.return_value = sample_medallion
        mock_store.create.side_effect = StoreError("Store failed")

        with pytest.raises(StoreError, match="Failed to create medallion"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_schema_validation_error_on_create(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session handles schema validation errors on create."""
        mock_store.get_latest_for_scope.return_value = []
        mock_llm.generate.return_value = sample_medallion
        mock_store.create.side_effect = SchemaValidationError("Schema invalid")

        with pytest.raises(SchemaValidationError, match="Generated medallion schema validation failed"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )


class TestCheckpointSessionExistingMedallion:
    """Tests for checkpoint_session with existing medallion."""

    @pytest.mark.asyncio
    async def test_checkpoint_session_updates_existing_medallion(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session updates existing medallion."""
        # Mock: Existing medallion found
        mock_store.get_latest_for_scope.return_value = [sample_medallion]
        # Mock: LLM updates medallion
        updated_medallion = Medallion(
            meta=sample_medallion.meta,
            scope=sample_medallion.scope,
            summary=sample_medallion.summary,
            decisions=sample_medallion.decisions,
            open_questions=sample_medallion.open_questions,
            affordances=sample_medallion.affordances,
        )
        mock_llm.update.return_value = updated_medallion

        result = await _checkpoint_session_async(
            mock_store, mock_llm, sample_scope, sample_evidence
        )

        # Verify LLM.update was called with existing medallion
        mock_llm.update.assert_called_once_with(sample_medallion, sample_evidence)
        # Verify store.update was called with updated medallion
        mock_store.update.assert_called_once_with(updated_medallion)
        # Verify store.create was NOT called
        mock_store.create.assert_not_called()
        # Verify LLM.generate was NOT called
        mock_llm.generate.assert_not_called()
        # Verify result
        assert result == updated_medallion

    @pytest.mark.asyncio
    async def test_checkpoint_session_uses_most_recent_medallion(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that checkpoint_session uses most recent medallion if multiple exist."""
        now = datetime.now()
        # Create two medallions (most recent first)
        medallion1 = Medallion(
            meta=MedallionMeta(
                medallion_id="med-001",
                model="gpt-4",
                created_at=now,
                updated_at=now,
            ),
            scope=sample_scope,
            summary=MedallionSummary(high_level="Recent", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        medallion2 = Medallion(
            meta=MedallionMeta(
                medallion_id="med-002",
                model="gpt-4",
                created_at=now,
                updated_at=now,
            ),
            scope=sample_scope,
            summary=MedallionSummary(high_level="Older", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        mock_store.get_latest_for_scope.return_value = [medallion1, medallion2]
        mock_llm.update.return_value = medallion1

        await _checkpoint_session_async(
            mock_store, mock_llm, sample_scope, sample_evidence
        )

        # Verify update was called with most recent (first) medallion
        mock_llm.update.assert_called_once_with(medallion1, sample_evidence)

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_llm_error_on_update(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session handles LLM errors on update."""
        mock_store.get_latest_for_scope.return_value = [sample_medallion]
        mock_llm.update.side_effect = LLMError("LLM update failed")

        with pytest.raises(LLMError, match="Failed to update medallion"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_store_error_on_update(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session handles store errors on update."""
        mock_store.get_latest_for_scope.return_value = [sample_medallion]
        updated_medallion = Medallion(
            meta=sample_medallion.meta,
            scope=sample_medallion.scope,
            summary=sample_medallion.summary,
            decisions=sample_medallion.decisions,
            open_questions=sample_medallion.open_questions,
            affordances=sample_medallion.affordances,
        )
        mock_llm.update.return_value = updated_medallion
        mock_store.update.side_effect = StoreError("Store update failed")

        with pytest.raises(StoreError, match="Failed to update medallion in store"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_schema_validation_error_on_update(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
        sample_medallion: Medallion,
    ) -> None:
        """Test that checkpoint_session handles schema validation errors on update."""
        mock_store.get_latest_for_scope.return_value = [sample_medallion]
        updated_medallion = Medallion(
            meta=sample_medallion.meta,
            scope=sample_medallion.scope,
            summary=sample_medallion.summary,
            decisions=sample_medallion.decisions,
            open_questions=sample_medallion.open_questions,
            affordances=sample_medallion.affordances,
        )
        mock_llm.update.return_value = updated_medallion
        mock_store.update.side_effect = SchemaValidationError("Schema invalid")

        with pytest.raises(SchemaValidationError, match="Updated medallion schema validation failed"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )

    @pytest.mark.asyncio
    async def test_checkpoint_session_handles_unexpected_error(
        self,
        mock_store: MedallionStore,
        mock_llm: MedallionLLM,
        sample_scope: MedallionScope,
        sample_evidence: Evidence,
    ) -> None:
        """Test that checkpoint_session wraps unexpected errors."""
        # Raise an unexpected exception
        mock_store.get_latest_for_scope.side_effect = ValueError("Unexpected error")

        with pytest.raises(StoreError, match="Unexpected error during checkpoint_session"):
            await _checkpoint_session_async(
                mock_store, mock_llm, sample_scope, sample_evidence
            )


class TestLoadMedallionsForScope:
    """Tests for load_medallions_for_scope."""

    @pytest.mark.asyncio
    async def test_load_medallions_for_scope_calls_store(
        self,
        mock_store: MedallionStore,
        sample_scope: MedallionScope,
        sample_medallion: Medallion,
    ) -> None:
        """Test that load_medallions_for_scope calls store.get_latest_for_scope."""
        mock_store.get_latest_for_scope.return_value = [sample_medallion]

        result = await _load_medallions_for_scope_async(mock_store, sample_scope, 10)

        mock_store.get_latest_for_scope.assert_called_once_with(sample_scope, limit=10)
        assert result == [sample_medallion]

    def test_load_medallions_for_scope_sync_wrapper(
        self,
        mock_store: MedallionStore,
        sample_scope: MedallionScope,
        sample_medallion: Medallion,
    ) -> None:
        """Test that load_medallions_for_scope sync wrapper works (non-async context)."""
        # Note: Testing sync wrapper in sync context (not from async test)
        # The sync wrapper uses asyncio.run(), which cannot be called from async context
        # In real usage, sync wrappers are called from sync code, not from async tests
        mock_store.get_latest_for_scope.return_value = [sample_medallion]

        result = load_medallions_for_scope(mock_store, sample_scope, 10)

        assert result == [sample_medallion]

    @pytest.mark.asyncio
    async def test_load_medallions_for_scope_handles_empty_result(
        self, mock_store: MedallionStore, sample_scope: MedallionScope
    ) -> None:
        """Test that load_medallions_for_scope handles empty results."""
        mock_store.get_latest_for_scope.return_value = []

        result = await _load_medallions_for_scope_async(mock_store, sample_scope)

        assert result == []

    @pytest.mark.asyncio
    async def test_load_medallions_for_scope_handles_store_error(
        self, mock_store: MedallionStore, sample_scope: MedallionScope
    ) -> None:
        """Test that load_medallions_for_scope handles store errors."""
        mock_store.get_latest_for_scope.side_effect = StoreError("Store failed")

        # StoreError is re-raised as-is, not wrapped
        with pytest.raises(StoreError, match="Store failed"):
            await _load_medallions_for_scope_async(mock_store, sample_scope)

    @pytest.mark.asyncio
    async def test_load_medallions_for_scope_handles_unexpected_error(
        self, mock_store: MedallionStore, sample_scope: MedallionScope
    ) -> None:
        """Test that load_medallions_for_scope wraps unexpected errors."""
        # Use a non-StoreError exception to test wrapping
        mock_store.get_latest_for_scope.side_effect = ValueError("Unexpected error")

        with pytest.raises(StoreError, match="Unexpected error loading medallions"):
            await _load_medallions_for_scope_async(mock_store, sample_scope)


class TestCheckpointSessionIntegration:
    """Integration-style tests using real implementations."""

    @pytest.mark.asyncio
    async def test_checkpoint_session_end_to_end(
        self, sample_scope: MedallionScope, sample_evidence: Evidence
    ) -> None:
        """Test checkpoint_session with real SQLite store and stub LLM."""
        from medallion.sqlite_store import SQLiteMedallionStore

        async with SQLiteMedallionStore(":memory:") as store:
            llm = StubMedallionLLM()

            # First call - creates new medallion
            medallion1 = await _checkpoint_session_async(
                store, llm, sample_scope, sample_evidence
            )
            assert medallion1.meta.medallion_id.startswith("med-")
            assert medallion1.meta.status == "active"

            # Verify it was persisted
            retrieved = await store.get_by_id(medallion1.meta.medallion_id)
            assert retrieved is not None
            assert retrieved.meta.medallion_id == medallion1.meta.medallion_id

            # Second call - updates existing medallion
            new_evidence = Evidence(
                session_summary="Updated summary",
                transcripts=[],
                artefacts={},
            )
            medallion2 = await _checkpoint_session_async(
                store, llm, sample_scope, new_evidence
            )
            assert medallion2.meta.medallion_id == medallion1.meta.medallion_id
            assert medallion2.meta.created_at == medallion1.meta.created_at
            assert medallion2.meta.updated_at > medallion1.meta.updated_at

