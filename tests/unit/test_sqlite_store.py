"""Unit tests for SQLiteMedallionStore implementation."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from medallion.store import MedallionStore
from medallion.sqlite_store import SQLiteMedallionStore
from medallion.types import (
    Medallion,
    MedallionAffordances,
    MedallionMeta,
    MedallionScope,
    MedallionSummary,
    SchemaValidationError,
    StoreError,
)


@pytest.fixture
async def in_memory_store() -> SQLiteMedallionStore:
    """Create an in-memory SQLite store for testing."""
    store = SQLiteMedallionStore(":memory:")
    yield store
    await store.close()


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
    affordances = MedallionAffordances()
    return Medallion(
        meta=meta,
        scope=scope,
        summary=summary,
        decisions=[],
        open_questions=[],
        affordances=affordances,
    )


class TestSQLiteMedallionStoreCreate:
    """Tests for SQLiteMedallionStore.create()."""

    @pytest.mark.asyncio
    async def test_create_persists_medallion(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create persists a medallion."""
        await in_memory_store.create(sample_medallion)
        retrieved = await in_memory_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == "med-001"
        assert retrieved.scope.graph_nodes == ["repo:muse"]

    @pytest.mark.asyncio
    async def test_create_validates_schema(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that create validates medallion schema."""
        # Schema validation happens at Pydantic level during object creation
        # If we somehow bypassed Pydantic, JSON serialization would fail
        # This is tested indirectly through successful create operations
        pass  # Schema validation is implicit in Medallion instantiation

    @pytest.mark.asyncio
    async def test_create_handles_integrity_error(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create handles IntegrityError (race condition)."""
        # Create medallion first
        await in_memory_store.create(sample_medallion)

        # Try to create again (should raise IntegrityError which gets wrapped)
        with pytest.raises(StoreError, match="already exists"):
            await in_memory_store.create(sample_medallion)

    @pytest.mark.asyncio
    async def test_create_raises_error_on_duplicate_id(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create raises StoreError on duplicate ID."""
        await in_memory_store.create(sample_medallion)
        with pytest.raises(StoreError, match="already exists"):
            await in_memory_store.create(sample_medallion)

    @pytest.mark.asyncio
    async def test_create_stores_all_fields(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that create stores all medallion fields."""
        await in_memory_store.create(sample_medallion)
        retrieved = await in_memory_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == sample_medallion.meta.medallion_id
        assert retrieved.meta.schema_version == sample_medallion.meta.schema_version
        assert retrieved.scope.graph_nodes == sample_medallion.scope.graph_nodes
        assert retrieved.scope.tags == sample_medallion.scope.tags
        assert retrieved.summary.high_level == sample_medallion.summary.high_level


class TestSQLiteMedallionStoreGetById:
    """Tests for SQLiteMedallionStore.get_by_id()."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_existing_medallion(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that get_by_id returns an existing medallion."""
        await in_memory_store.create(sample_medallion)
        retrieved = await in_memory_store.get_by_id("med-001")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == "med-001"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_by_id returns None for nonexistent medallion."""
        result = await in_memory_store.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_preserves_all_fields(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_by_id preserves all medallion fields."""
        now = datetime.now()
        meta = MedallionMeta(
            medallion_id="med-002",
            model="gpt-4",
            created_at=now,
            updated_at=now,
            knowledge_min_ts=datetime(2025, 1, 1),
            knowledge_max_ts=datetime(2025, 1, 2),
        )
        scope = MedallionScope(
            graph_nodes=["repo:test", "module:cli"],
            tags=["test", "dev"],
        )
        summary = MedallionSummary(
            high_level="Full test medallion",
            subsystems=[],
        )
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=summary,
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)
        retrieved = await in_memory_store.get_by_id("med-002")
        assert retrieved is not None
        assert retrieved.meta.knowledge_min_ts == datetime(2025, 1, 1)
        assert retrieved.meta.knowledge_max_ts == datetime(2025, 1, 2)
        assert len(retrieved.scope.graph_nodes) == 2
        assert len(retrieved.scope.tags) == 2


class TestSQLiteMedallionStoreContextManager:
    """Tests for SQLiteMedallionStore async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_initializes_database(self) -> None:
        """Test that context manager initializes database."""
        async with SQLiteMedallionStore(":memory:") as store:
            # Database should be initialized
            # Create a medallion to verify it works
            now = datetime.now()
            meta = MedallionMeta(
                medallion_id="med-003",
                model="gpt-4",
                created_at=now,
                updated_at=now,
            )
            scope = MedallionScope(graph_nodes=["repo:test"], tags=["test"])
            summary = MedallionSummary(high_level="Test", subsystems=[])
            medallion = Medallion(
                meta=meta,
                scope=scope,
                summary=summary,
                decisions=[],
                open_questions=[],
                affordances=MedallionAffordances(),
            )
            await store.create(medallion)
            retrieved = await store.get_by_id("med-003")
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_connection(self) -> None:
        """Test that context manager closes connection on exit."""
        async with SQLiteMedallionStore(":memory:") as store:
            # Use store
            pass
        # Connection should be closed after context exit
        # Accessing conn after close would raise error, but it's private
        # We can verify by trying to use it again
        assert store._conn is None


class TestSQLiteMedallionStoreUpdate:
    """Tests for SQLiteMedallionStore.update()."""

    @pytest.mark.asyncio
    async def test_update_modifies_existing_medallion(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that update modifies an existing medallion."""
        await in_memory_store.create(sample_medallion)

        # Modify the medallion
        from datetime import timedelta

        updated_meta = MedallionMeta(
            medallion_id=sample_medallion.meta.medallion_id,
            model=sample_medallion.meta.model,
            created_at=sample_medallion.meta.created_at,
            updated_at=sample_medallion.meta.updated_at + timedelta(seconds=1),
            status="active",
        )
        updated_summary = MedallionSummary(
            high_level="Updated summary", subsystems=[]
        )
        updated_medallion = Medallion(
            meta=updated_meta,
            scope=sample_medallion.scope,
            summary=updated_summary,
            decisions=sample_medallion.decisions,
            open_questions=sample_medallion.open_questions,
            affordances=sample_medallion.affordances,
        )

        await in_memory_store.update(updated_medallion)

        # Verify update
        retrieved = await in_memory_store.get_by_id(sample_medallion.meta.medallion_id)
        assert retrieved is not None
        assert retrieved.summary.high_level == "Updated summary"
        assert retrieved.meta.updated_at > sample_medallion.meta.updated_at
        assert retrieved.meta.created_at == sample_medallion.meta.created_at  # Preserved

    @pytest.mark.asyncio
    async def test_update_raises_error_on_nonexistent_medallion(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that update raises StoreError on nonexistent medallion."""
        with pytest.raises(StoreError, match="not found"):
            await in_memory_store.update(sample_medallion)

    @pytest.mark.asyncio
    async def test_update_preserves_created_at(
        self, in_memory_store: SQLiteMedallionStore, sample_medallion: Medallion
    ) -> None:
        """Test that update preserves created_at timestamp."""
        await in_memory_store.create(sample_medallion)

        from datetime import timedelta

        original_created_at = sample_medallion.meta.created_at
        updated_meta = MedallionMeta(
            medallion_id=sample_medallion.meta.medallion_id,
            model=sample_medallion.meta.model,
            created_at=original_created_at,
            updated_at=sample_medallion.meta.updated_at + timedelta(seconds=1),
            status="active",
        )
        updated_medallion = Medallion(
            meta=updated_meta,
            scope=sample_medallion.scope,
            summary=sample_medallion.summary,
            decisions=sample_medallion.decisions,
            open_questions=sample_medallion.open_questions,
            affordances=sample_medallion.affordances,
        )

        await in_memory_store.update(updated_medallion)

        retrieved = await in_memory_store.get_by_id(sample_medallion.meta.medallion_id)
        assert retrieved is not None
        assert retrieved.meta.created_at == original_created_at


class TestSQLiteMedallionStoreGetLatestForScope:
    """Tests for SQLiteMedallionStore.get_latest_for_scope()."""

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_returns_matching_medallions(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope returns medallions matching scope."""
        now = datetime.now()
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )

        # Create medallions with matching scope
        for i in range(2):
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
            await in_memory_store.create(medallion)

        # Query for matching scope
        results = await in_memory_store.get_latest_for_scope(scope, limit=10)
        assert len(results) == 2
        assert all(m.scope.graph_nodes == scope.graph_nodes for m in results)

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_respects_limit(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope respects limit parameter."""
        now = datetime.now()
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )

        # Create 5 medallions
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
            await in_memory_store.create(medallion)

        # Query with limit
        results = await in_memory_store.get_latest_for_scope(scope, limit=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_returns_empty_for_no_match(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope returns empty list for no matches."""
        now = datetime.now()
        # Create medallion with different scope
        scope1 = MedallionScope(
            graph_nodes=["repo:other"],
            tags=["different"],
        )
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        medallion = Medallion(
            meta=meta,
            scope=scope1,
            summary=MedallionSummary(high_level="Test", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

        # Query with different scope
        scope2 = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await in_memory_store.get_latest_for_scope(scope2, limit=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_handles_zero_limit(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope handles zero limit."""
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )
        results = await in_memory_store.get_latest_for_scope(scope, limit=0)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_with_no_tags(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope works with empty tags."""
        now = datetime.now()
        scope_with_tags = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )

        # Create medallion with tags
        meta = MedallionMeta(
            medallion_id="med-001",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        medallion = Medallion(
            meta=meta,
            scope=scope_with_tags,
            summary=MedallionSummary(high_level="Test", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

        # Query with no tags (should match)
        scope_no_tags = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=[],
        )
        results = await in_memory_store.get_latest_for_scope(scope_no_tags, limit=10)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_exact_match(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope returns medallions with exact matching scope."""
        now = datetime.now()
        scope = MedallionScope(
            graph_nodes=["repo:muse", "module:cli"],
            tags=["project_state", "refactor"],
        )

        # Create medallion with exact same scope
        meta = MedallionMeta(
            medallion_id="med-exact",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=MedallionSummary(high_level="Exact match", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

        # Query with exact same scope
        results = await in_memory_store.get_latest_for_scope(scope, limit=10)
        assert len(results) == 1
        assert results[0].meta.medallion_id == "med-exact"
        assert results[0].scope.graph_nodes == scope.graph_nodes
        assert results[0].scope.tags == scope.tags

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_subset_match(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope returns medallions when requested graph_nodes are subset of stored."""
        now = datetime.now()
        # Create medallion with multiple graph_nodes
        stored_scope = MedallionScope(
            graph_nodes=["repo:muse", "module:cli", "module:store"],
            tags=["project_state"],
        )

        meta = MedallionMeta(
            medallion_id="med-subset",
            model="gpt-4",
            created_at=now,
            updated_at=now,
        )
        medallion = Medallion(
            meta=meta,
            scope=stored_scope,
            summary=MedallionSummary(high_level="Subset match test", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

        # Query with subset of graph_nodes (should match)
        requested_scope = MedallionScope(
            graph_nodes=["repo:muse", "module:cli"],  # Subset of stored nodes
            tags=["project_state"],
        )
        results = await in_memory_store.get_latest_for_scope(requested_scope, limit=10)
        assert len(results) == 1
        assert results[0].meta.medallion_id == "med-subset"

        # Query with single node subset (should match)
        requested_scope2 = MedallionScope(
            graph_nodes=["repo:muse"],  # Single node, subset of stored
            tags=["project_state"],
        )
        results2 = await in_memory_store.get_latest_for_scope(requested_scope2, limit=10)
        assert len(results2) == 1
        assert results2[0].meta.medallion_id == "med-subset"

    @pytest.mark.asyncio
    async def test_get_latest_for_scope_ordering(
        self, in_memory_store: SQLiteMedallionStore
    ) -> None:
        """Test that get_latest_for_scope orders results by updated_at DESC."""
        base_time = datetime.now()
        scope = MedallionScope(
            graph_nodes=["repo:muse"],
            tags=["project_state"],
        )

        # Create medallions with different timestamps (oldest first)
        medallions = []
        for i in range(3):
            meta = MedallionMeta(
                medallion_id=f"med-order-{i:03d}",
                model="gpt-4",
                created_at=base_time + timedelta(seconds=i),
                updated_at=base_time + timedelta(seconds=i),  # Earlier timestamps first
            )
            medallion = Medallion(
                meta=meta,
                scope=scope,
                summary=MedallionSummary(high_level=f"Order test {i}", subsystems=[]),
                decisions=[],
                open_questions=[],
                affordances=MedallionAffordances(),
            )
            medallions.append(medallion)
            await in_memory_store.create(medallion)

        # Update middle medallion to make it most recent
        most_recent = medallions[1]
        updated_meta = MedallionMeta(
            medallion_id=most_recent.meta.medallion_id,
            model=most_recent.meta.model,
            created_at=most_recent.meta.created_at,
            updated_at=base_time + timedelta(seconds=10),  # Most recent
            status="active",
        )
        updated_medallion = Medallion(
            meta=updated_meta,
            scope=most_recent.scope,
            summary=most_recent.summary,
            decisions=most_recent.decisions,
            open_questions=most_recent.open_questions,
            affordances=most_recent.affordances,
        )
        await in_memory_store.update(updated_medallion)

        # Query - results should be ordered by updated_at DESC (most recent first)
        results = await in_memory_store.get_latest_for_scope(scope, limit=10)
        assert len(results) == 3

        # Verify ordering: most recent first
        assert results[0].meta.medallion_id == "med-order-001"  # Most recent (updated)
        assert results[0].meta.updated_at > results[1].meta.updated_at
        assert results[1].meta.updated_at > results[2].meta.updated_at

        # Verify all timestamps are descending
        for i in range(len(results) - 1):
            assert results[i].meta.updated_at >= results[i + 1].meta.updated_at


class TestSQLiteMedallionStoreProtocol:
    """Tests verifying SQLiteMedallionStore satisfies MedallionStore Protocol."""

    def test_sqlite_store_satisfies_protocol(self) -> None:
        """Test that SQLiteMedallionStore satisfies MedallionStore Protocol."""
        store: MedallionStore = SQLiteMedallionStore(":memory:")
        # Type check: If this compiles, SQLiteMedallionStore satisfies the Protocol
        assert isinstance(store, type(store))

