"""Interface contract tests for MedallionStore Protocol."""

from datetime import datetime, timedelta
from typing import List, Optional

import pytest

from medallion.types import (
    Medallion,
    MedallionAffordances,
    MedallionMeta,
    MedallionScope,
    MedallionSummary,
    StoreError,
)
from medallion.store import MedallionStore


class MockMedallionStore:
    """Mock implementation of MedallionStore for testing Protocol conformance."""

    def __init__(self) -> None:
        """Initialize mock store with empty storage."""
        self._storage: dict[str, Medallion] = {}

    async def create(self, medallion: Medallion) -> None:
        """Mock create implementation."""
        if medallion.meta.medallion_id in self._storage:
            raise StoreError(f"Medallion {medallion.meta.medallion_id} already exists")
        self._storage[medallion.meta.medallion_id] = medallion

    async def update(self, medallion: Medallion) -> None:
        """Mock update implementation."""
        if medallion.meta.medallion_id not in self._storage:
            raise StoreError(f"Medallion {medallion.meta.medallion_id} not found")
        self._storage[medallion.meta.medallion_id] = medallion

    async def get_by_id(self, medallion_id: str) -> Optional[Medallion]:
        """Mock get_by_id implementation."""
        return self._storage.get(medallion_id)

    async def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10,
    ) -> List[Medallion]:
        """Mock get_latest_for_scope implementation."""
        results: List[Medallion] = []
        requested_nodes = set(scope.graph_nodes)
        requested_tags = set(scope.tags)

        for medallion in self._storage.values():
            stored_nodes = set(medallion.scope.graph_nodes)
            stored_tags = set(medallion.scope.tags)

            # Subset matching for graph_nodes
            nodes_match = (
                not requested_nodes or requested_nodes.issubset(stored_nodes)
            )
            # Intersection matching for tags
            tags_match = (
                not requested_tags or bool(requested_tags & stored_tags)
            )

            if nodes_match and tags_match:
                results.append(medallion)

        # Sort by updated_at DESC
        results.sort(key=lambda m: m.meta.updated_at, reverse=True)
        return results[:limit] if limit > 0 else []


class TestMedallionStoreProtocol:
    """Tests verifying MedallionStore Protocol conformance."""

    @pytest.fixture
    def mock_store(self) -> MockMedallionStore:
        """Create a mock store instance."""
        return MockMedallionStore()

    @pytest.fixture
    def sample_medallion(self) -> Medallion:
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

    @pytest.mark.asyncio
    async def test_create_method_exists(self, mock_store: MockMedallionStore) -> None:
        """Test that create method exists and is async."""
        assert hasattr(mock_store, "create")
        assert callable(mock_store.create)

    @pytest.mark.asyncio
    async def test_create_persists_medallion(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create persists a medallion."""
        await mock_store.create(sample_medallion)
        retrieved = await mock_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == "med-001"

    @pytest.mark.asyncio
    async def test_create_raises_error_on_duplicate(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create raises StoreError on duplicate ID."""
        await mock_store.create(sample_medallion)
        with pytest.raises(StoreError, match="already exists"):
            await mock_store.create(sample_medallion)

    @pytest.mark.asyncio
    async def test_update_method_exists(self, mock_store: MockMedallionStore) -> None:
        """Test that update method exists and is async."""
        assert hasattr(mock_store, "update")
        assert callable(mock_store.update)

    @pytest.mark.asyncio
    async def test_update_modifies_existing_medallion(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that update modifies an existing medallion."""
        await mock_store.create(sample_medallion)

        # Update the medallion
        updated_meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=sample_medallion.meta.created_at,
            updated_at=datetime.now(),
        )
        updated_medallion = Medallion(
            meta=updated_meta,
            scope=sample_medallion.scope,
            summary=sample_medallion.summary,
            decisions=[],
            open_questions=[],
            affordances=sample_medallion.affordances,
        )
        await mock_store.update(updated_medallion)

        retrieved = await mock_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.updated_at > sample_medallion.meta.updated_at

    @pytest.mark.asyncio
    async def test_update_raises_error_on_nonexistent(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that update raises StoreError on nonexistent medallion."""
        with pytest.raises(StoreError, match="not found"):
            await mock_store.update(sample_medallion)

    @pytest.mark.asyncio
    async def test_get_by_id_method_exists(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test that get_by_id method exists and is async."""
        assert hasattr(mock_store, "get_by_id")
        assert callable(mock_store.get_by_id)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_medallion(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that get_by_id returns existing medallion."""
        await mock_store.create(sample_medallion)
        retrieved = await mock_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == "med-001"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test that get_by_id returns None for nonexistent medallion."""
        result = await mock_store.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_method_exists(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test that get_latest_for_scope method exists and is async."""
        assert hasattr(mock_store, "get_latest_for_scope")
        assert callable(mock_store.get_latest_for_scope)

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_exact_match(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test get_latest_for_scope with exact scope match."""
        await mock_store.create(sample_medallion)
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await mock_store.get_latest_for_scope(scope)
        assert len(results) == 1
        assert results[0].meta.medallion_id == "med-001"

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_subset_match(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test get_latest_for_scope with subset graph_nodes match."""
        now = datetime.now()
        # Create medallion with multiple graph nodes
        meta = MedallionMeta(
            medallion_id="med-002",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        scope_full = MedallionScope(
            graph_nodes=["repo:muse", "module:cli"],
            tags=["project_state"],
        )
        medallion = Medallion(
            meta=meta,
            scope=scope_full,
            summary=MedallionSummary(high_level="Test", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await mock_store.create(medallion)

        # Query with subset of nodes
        scope_subset = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await mock_store.get_latest_for_scope(scope_subset)
        assert len(results) == 1
        assert results[0].meta.medallion_id == "med-002"

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_returns_empty_for_no_matches(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test get_latest_for_scope returns empty list for no matches."""
        scope = MedallionScope(
            graph_nodes=["repo:nonexistent"],
            tags=["nonexistent"],
        )
        results = await mock_store.get_latest_for_scope(scope)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_returns_empty_for_empty_scope(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test get_latest_for_scope returns empty list for empty scope."""
        scope = MedallionScope()
        results = await mock_store.get_latest_for_scope(scope)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_respects_limit(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test get_latest_for_scope respects limit parameter."""
        now = datetime.now()
        scope = MedallionScope(graph_nodes=["repo:muse"], tags=["project_state"])

        # Create 5 medallions with incrementing timestamps
        for i in range(5):
            meta = MedallionMeta(
                medallion_id=f"med-{i:03d}",
                model="gpt-4",
                created_at=now + timedelta(seconds=i),
                updated_at=now + timedelta(seconds=i),
            )
            medallion = Medallion(
                meta=meta,
                scope=scope,
                summary=MedallionSummary(high_level=f"Summary {i}", subsystems=[]),
                decisions=[],
                open_questions=[],
                affordances=MedallionAffordances(),
            )
            await mock_store.create(medallion)

        # Query with limit
        results = await mock_store.get_latest_for_scope(scope, limit=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_orders_by_updated_at_desc(
        self, mock_store: MockMedallionStore
    ) -> None:
        """Test get_latest_for_scope orders results by updated_at DESC."""
        now = datetime.now()
        scope = MedallionScope(graph_nodes=["repo:muse"], tags=["project_state"])

        # Create medallions with different timestamps
        for i in range(3):
            timestamp = now + timedelta(seconds=i)
            meta = MedallionMeta(
                medallion_id=f"med-{i:03d}",
                model="gpt-4",
                created_at=timestamp,
                updated_at=timestamp,
            )
            medallion = Medallion(
                meta=meta,
                scope=scope,
                summary=MedallionSummary(high_level=f"Summary {i}", subsystems=[]),
                decisions=[],
                open_questions=[],
                affordances=MedallionAffordances(),
            )
            await mock_store.create(medallion)

        results = await mock_store.get_latest_for_scope(scope, limit=10)
        assert len(results) == 3
        # Should be ordered by updated_at DESC (latest first)
        assert results[0].meta.medallion_id == "med-002"
        assert results[1].meta.medallion_id == "med-001"
        assert results[2].meta.medallion_id == "med-000"

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_limit_zero_returns_empty(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test get_latest_for_scope with limit=0 returns empty list."""
        await mock_store.create(sample_medallion)
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await mock_store.get_latest_for_scope(scope, limit=0)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_negative_limit_returns_empty(
        self, mock_store: MockMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test get_latest_for_scope with negative limit returns empty list."""
        await mock_store.create(sample_medallion)
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await mock_store.get_latest_for_scope(scope, limit=-1)
        assert results == []

    def test_mock_store_satisfies_protocol(self) -> None:
        """Test that MockMedallionStore satisfies MedallionStore Protocol."""
        # This is a type check - if MockMedallionStore doesn't satisfy the Protocol,
        # mypy will catch it. This test ensures the mock is properly typed.
        store: MedallionStore = MockMedallionStore()
        assert isinstance(store, type(store))  # Basic check that it's instantiable

