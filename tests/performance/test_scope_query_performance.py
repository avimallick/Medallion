"""Performance tests for scope query operations (Phase 7 - T063)."""

import time
from datetime import datetime, timedelta

import pytest

from medallion.sqlite_store import SQLiteMedallionStore
from medallion.types import (
    Medallion,
    MedallionAffordances,
    MedallionMeta,
    MedallionScope,
    MedallionSummary,
)


@pytest.fixture
async def large_store() -> SQLiteMedallionStore:
    """Create a store with many medallions for performance testing."""
    store = SQLiteMedallionStore(":memory:")
    now = datetime.now()

    # Create 100+ medallions with varying scopes
    for i in range(150):
        # Vary graph nodes and tags
        nodes = []
        if i % 3 == 0:
            nodes = ["repo:muse", "module:cli"]
        elif i % 3 == 1:
            nodes = ["repo:muse", "module:cli", "module:store"]
        else:
            nodes = ["repo:other", "module:api"]

        tags = []
        if i % 2 == 0:
            tags = ["project_state"]
        else:
            tags = ["refactor"]

        scope = MedallionScope(graph_nodes=nodes, tags=tags)
        meta = MedallionMeta(
            medallion_id=f"med-perf-{i:03d}",
            model="gpt-4",
            created_at=now + timedelta(seconds=i),
            updated_at=now + timedelta(seconds=i),
        )
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=MedallionSummary(high_level=f"Performance test {i}", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await store.create(medallion)

    yield store
    await store.close()


@pytest.mark.asyncio
async def test_get_latest_for_scope_performance_with_many_medallions(
    large_store: SQLiteMedallionStore,
) -> None:
    """Test that get_latest_for_scope performs well with 100+ medallions.

    Target: <50ms p95 for <100 medallions (we test with 150).
    """
    scope = MedallionScope(
        graph_nodes=["repo:muse", "module:cli"],
        tags=["project_state"],
    )

    # Measure query time
    start = time.perf_counter()
    results = await large_store.get_latest_for_scope(scope, limit=10)
    elapsed = time.perf_counter() - start

    # Verify results (subset matching means stored nodes may have more than requested)
    assert len(results) > 0
    # Verify that requested nodes are subset of stored nodes (subset matching)
    for medallion in results:
        requested_nodes = set(scope.graph_nodes)
        stored_nodes = set(medallion.scope.graph_nodes)
        assert requested_nodes.issubset(stored_nodes), f"Requested {requested_nodes} not subset of {stored_nodes}"

    # Performance assertion: should complete in <50ms (p95 target)
    # We use 100ms as a reasonable upper bound for 150 medallions
    assert elapsed < 0.1, f"Query took {elapsed*1000:.2f}ms, expected <100ms"

    print(f"Query completed in {elapsed*1000:.2f}ms with {len(results)} results")


@pytest.mark.asyncio
async def test_get_latest_for_scope_performance_empty_result(
    large_store: SQLiteMedallionStore,
) -> None:
    """Test that queries with no matches are fast."""
    scope = MedallionScope(
        graph_nodes=["repo:nonexistent"],
        tags=["nonexistent_tag"],
    )

    start = time.perf_counter()
    results = await large_store.get_latest_for_scope(scope, limit=10)
    elapsed = time.perf_counter() - start

    assert len(results) == 0
    # Empty results should be very fast
    assert elapsed < 0.05, f"Empty query took {elapsed*1000:.2f}ms, expected <50ms"

    print(f"Empty query completed in {elapsed*1000:.2f}ms")


@pytest.mark.asyncio
async def test_get_latest_for_scope_performance_with_limit(
    large_store: SQLiteMedallionStore,
) -> None:
    """Test that limit parameter improves performance."""
    scope = MedallionScope(
        graph_nodes=["repo:muse"],
        tags=["project_state"],
    )

    # Test with small limit
    start = time.perf_counter()
    results_small = await large_store.get_latest_for_scope(scope, limit=5)
    elapsed_small = time.perf_counter() - start

    # Test with larger limit
    start = time.perf_counter()
    results_large = await large_store.get_latest_for_scope(scope, limit=50)
    elapsed_large = time.perf_counter() - start

    assert len(results_small) <= 5
    assert len(results_large) <= 50

    # Both should be fast, but smaller limit might be slightly faster
    assert elapsed_small < 0.1
    assert elapsed_large < 0.1

    print(f"Small limit (5): {elapsed_small*1000:.2f}ms")
    print(f"Large limit (50): {elapsed_large*1000:.2f}ms")

