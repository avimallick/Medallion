"""Integration tests for SQLiteMedallionStore create/get round-trip."""

from datetime import datetime, timedelta

import pytest

from medallion.sqlite_store import SQLiteMedallionStore
from medallion.types import (
    Evidence,
    Medallion,
    MedallionAffordances,
    MedallionDecision,
    MedallionMeta,
    MedallionOpenQuestion,
    MedallionScope,
    MedallionSummary,
)


@pytest.fixture
async def in_memory_store() -> SQLiteMedallionStore:
    """Create an in-memory SQLite store for testing."""
    store = SQLiteMedallionStore(":memory:")
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_create_and_get_round_trip(
    in_memory_store: SQLiteMedallionStore,
) -> None:
    """Test creating a medallion and retrieving it end-to-end."""
    now = datetime.now()
    meta = MedallionMeta(
        medallion_id="med-integration-001",
        model="gpt-4",
        created_at=now,
        updated_at=now,
    )
    scope = MedallionScope(
        graph_nodes=["repo:muse", "module:cli"],
        tags=["project_state", "refactor_sprint_1"],
    )
    summary = MedallionSummary(
        high_level="Integration test summary",
        subsystems=[
            {
                "name": "Store",
                "status": "stable",
                "notes": "SQLite backend implemented",
            }
        ],
    )
    decisions = [
        {
            "id": "D-001",
            "statement": "Use Python 3.11+",
            "rationale": "Modern type hints",
            "confidence": 0.9,
        }
    ]
    open_questions = [
        {
            "id": "Q-001",
            "question": "Should we add vector search?",
            "blocked_on": ["benchmark"],
            "priority": "medium",
        }
    ]
    affordances = MedallionAffordances(
        recommended_entry_points=["Start here"],
        avoid_repeating=["Don't do this"],
        invariants=["Always validate"],
    )

    medallion = Medallion(
        meta=meta,
        scope=scope,
        summary=summary,
        decisions=[MedallionDecision(**d) for d in decisions],
        open_questions=[MedallionOpenQuestion(**q) for q in open_questions],
        affordances=affordances,
    )

    # Create medallion
    await in_memory_store.create(medallion)

    # Retrieve medallion
    retrieved = await in_memory_store.get_by_id("med-integration-001")
    assert retrieved is not None

    # Verify all fields are preserved
    assert retrieved.meta.medallion_id == "med-integration-001"
    assert retrieved.meta.schema_version == "medallion.v1"
    assert retrieved.scope.graph_nodes == ["repo:muse", "module:cli"]
    assert retrieved.scope.tags == ["project_state", "refactor_sprint_1"]
    assert retrieved.summary.high_level == "Integration test summary"
    assert len(retrieved.summary.subsystems) == 1
    assert retrieved.summary.subsystems[0].name == "Store"
    assert len(retrieved.decisions) == 1
    assert retrieved.decisions[0].id == "D-001"
    assert retrieved.decisions[0].confidence == 0.9
    assert len(retrieved.open_questions) == 1
    assert retrieved.open_questions[0].id == "Q-001"
    assert retrieved.open_questions[0].priority == "medium"
    assert len(retrieved.affordances.recommended_entry_points) == 1
    assert retrieved.affordances.invariants is not None
    assert len(retrieved.affordances.invariants) == 1

    # Verify JSON round-trip works
    json_str = retrieved.model_dump_json()
    deserialized = Medallion.model_validate_json(json_str)
    assert deserialized.meta.medallion_id == retrieved.meta.medallion_id


@pytest.mark.asyncio
async def test_multiple_medallions_create_and_retrieve(
    in_memory_store: SQLiteMedallionStore,
) -> None:
    """Test creating and retrieving multiple medallions."""
    now = datetime.now()
    medallions = []

    for i in range(3):
        meta = MedallionMeta(
            medallion_id=f"med-multi-{i:03d}",
            model="gpt-4",
            created_at=now + timedelta(seconds=i),
            updated_at=now + timedelta(seconds=i),
        )
        scope = MedallionScope(
            graph_nodes=[f"repo:test{i}"],
            tags=["test"],
        )
        summary = MedallionSummary(
            high_level=f"Summary {i}",
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
        medallions.append(medallion)
        await in_memory_store.create(medallion)

    # Retrieve all medallions
    for i, medallion in enumerate(medallions):
        retrieved = await in_memory_store.get_by_id(f"med-multi-{i:03d}")
        assert retrieved is not None
        assert retrieved.meta.medallion_id == medallion.meta.medallion_id
        assert retrieved.scope.graph_nodes == medallion.scope.graph_nodes


@pytest.mark.asyncio
async def test_create_preserves_timestamps(
    in_memory_store: SQLiteMedallionStore,
) -> None:
    """Test that create preserves exact timestamps."""
    created = datetime(2025, 1, 1, 12, 0, 0)
    updated = datetime(2025, 1, 1, 13, 0, 0)
    meta = MedallionMeta(
        medallion_id="med-timestamp",
        model="gpt-4",
        created_at=created,
        updated_at=updated,
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

    await in_memory_store.create(medallion)
    retrieved = await in_memory_store.get_by_id("med-timestamp")
    assert retrieved is not None
    # Verify timestamps are preserved (within second precision)
    assert retrieved.meta.created_at.replace(microsecond=0) == created.replace(
        microsecond=0
    )
    assert retrieved.meta.updated_at.replace(microsecond=0) == updated.replace(
        microsecond=0
    )


@pytest.mark.asyncio
async def test_checkpoint_session_end_to_end(in_memory_store: SQLiteMedallionStore) -> None:
    """Test checkpoint_session end-to-end with real SQLite store and stub LLM."""
    from medallion.llm import StubMedallionLLM
    from medallion.session import _checkpoint_session_async

    scope = MedallionScope(
        graph_nodes=["repo:muse"],
        tags=["project_state"],
    )
    evidence = Evidence(
        session_summary="Integration test session",
        transcripts=["transcript 1"],
        artefacts={"test": "data"},
    )

    llm = StubMedallionLLM()

    # First call - creates new medallion
    medallion1 = await _checkpoint_session_async(in_memory_store, llm, scope, evidence)
    assert medallion1.meta.medallion_id.startswith("med-")
    assert medallion1.meta.status == "active"
    assert medallion1.summary.high_level == "Integration test session"

    # Verify it was persisted
    retrieved = await in_memory_store.get_by_id(medallion1.meta.medallion_id)
    assert retrieved is not None
    assert retrieved.meta.medallion_id == medallion1.meta.medallion_id

    # Second call with same scope - updates existing medallion
    new_evidence = Evidence(
        session_summary="Updated session summary",
        transcripts=["transcript 2"],
        artefacts={"updated": "data"},
    )
    medallion2 = await _checkpoint_session_async(in_memory_store, llm, scope, new_evidence)
    assert medallion2.meta.medallion_id == medallion1.meta.medallion_id
    assert medallion2.meta.created_at == medallion1.meta.created_at
    assert medallion2.meta.updated_at > medallion1.meta.updated_at

    # Verify only one medallion exists
    all_medallions = await in_memory_store.get_latest_for_scope(scope, limit=10)
    assert len(all_medallions) == 1
    assert all_medallions[0].meta.medallion_id == medallion1.meta.medallion_id


@pytest.mark.asyncio
async def test_checkpoint_session_update_flow_no_duplication(in_memory_store: SQLiteMedallionStore) -> None:
    """Test checkpoint_session update flow ensures no duplication (Phase 6 - US3).

    This test specifically verifies that:
    1. Creating a medallion, then calling checkpoint_session with same scope updates it (not duplicates)
    2. Multiple updates preserve created_at and update updated_at
    3. Only one medallion exists for the scope after updates
    """
    from medallion.llm import StubMedallionLLM
    from medallion.session import _checkpoint_session_async

    scope = MedallionScope(
        graph_nodes=["repo:muse", "module:cli"],
        tags=["project_state", "refactor"],
    )

    llm = StubMedallionLLM()

    # Initial checkpoint - creates new medallion
    evidence1 = Evidence(
        session_summary="Initial checkpoint",
        transcripts=["transcript 1"],
        artefacts={"initial": "data"},
    )
    medallion1 = await _checkpoint_session_async(in_memory_store, llm, scope, evidence1)
    original_id = medallion1.meta.medallion_id
    original_created_at = medallion1.meta.created_at
    original_updated_at = medallion1.meta.updated_at

    # Verify initial state - one medallion exists
    all_medallions = await in_memory_store.get_latest_for_scope(scope, limit=10)
    assert len(all_medallions) == 1
    assert all_medallions[0].meta.medallion_id == original_id

    # Second checkpoint with same scope - should UPDATE, not create new
    evidence2 = Evidence(
        session_summary="Second checkpoint - should update",
        transcripts=["transcript 2"],
        artefacts={"updated": "data"},
    )
    medallion2 = await _checkpoint_session_async(in_memory_store, llm, scope, evidence2)

    # Verify: Same ID (not duplicated)
    assert medallion2.meta.medallion_id == original_id

    # Verify: created_at preserved, updated_at changed
    assert medallion2.meta.created_at == original_created_at
    assert medallion2.meta.updated_at > original_updated_at

    # Verify: Still only one medallion exists (no duplication)
    all_medallions_after_update = await in_memory_store.get_latest_for_scope(scope, limit=10)
    assert len(all_medallions_after_update) == 1
    assert all_medallions_after_update[0].meta.medallion_id == original_id

    # Third checkpoint - should update again
    evidence3 = Evidence(
        session_summary="Third checkpoint - should update again",
        transcripts=["transcript 3"],
        artefacts={"updated_again": "data"},
    )
    medallion3 = await _checkpoint_session_async(in_memory_store, llm, scope, evidence3)

    # Verify: Same ID still
    assert medallion3.meta.medallion_id == original_id

    # Verify: created_at still preserved, updated_at increased again
    assert medallion3.meta.created_at == original_created_at
    assert medallion3.meta.updated_at > medallion2.meta.updated_at

    # Verify: Still only one medallion (definitely no duplication after multiple updates)
    all_medallions_final = await in_memory_store.get_latest_for_scope(scope, limit=10)
    assert len(all_medallions_final) == 1
    assert all_medallions_final[0].meta.medallion_id == original_id

    # Verify: Timestamps are correct (created_at < updated_at)
    final_retrieved = await in_memory_store.get_by_id(original_id)
    assert final_retrieved is not None
    assert final_retrieved.meta.created_at < final_retrieved.meta.updated_at
    assert final_retrieved.meta.created_at == original_created_at


@pytest.mark.asyncio
async def test_load_medallions_for_scope_end_to_end(in_memory_store: SQLiteMedallionStore) -> None:
    """Test load_medallions_for_scope end-to-end with real SQLite store."""
    from medallion.session import _load_medallions_for_scope_async

    scope = MedallionScope(
        graph_nodes=["repo:muse"],
        tags=["project_state"],
    )
    now = datetime.now()

    # Create medallions with matching scope
    for i in range(3):
        meta = MedallionMeta(
            medallion_id=f"med-load-{i:03d}",
            model="gpt-4",
            created_at=now + timedelta(seconds=i),
            updated_at=now + timedelta(seconds=i),
        )
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=MedallionSummary(high_level=f"Load test {i}", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

    # Load medallions using async helper (from async test)
    results = await _load_medallions_for_scope_async(in_memory_store, scope, limit=10)

    # Verify results
    assert len(results) == 3
    assert all(m.scope.graph_nodes == scope.graph_nodes for m in results)
    assert all(m.scope.tags == scope.tags for m in results)
    assert all(m.meta.status == "active" for m in results)

    # Verify ordering (should be DESC by updated_at)
    for i in range(len(results) - 1):
        assert results[i].meta.updated_at >= results[i + 1].meta.updated_at

    # Test with limit
    limited_results = await _load_medallions_for_scope_async(in_memory_store, scope, limit=2)
    assert len(limited_results) == 2

    # Test with non-matching scope
    non_matching_scope = MedallionScope(
        graph_nodes=["repo:other"],
        tags=["different"],
    )
    empty_results = await _load_medallions_for_scope_async(in_memory_store, non_matching_scope, limit=10)
    assert empty_results == []


@pytest.mark.asyncio
async def test_graph_anchored_queries_complex_scenarios(in_memory_store: SQLiteMedallionStore) -> None:
    """Test graph-anchored queries with complex scenarios (Phase 7 - US4).

    Creates multiple medallions with different scopes and verifies subset queries
    return only relevant medallions.
    """
    from medallion.session import _load_medallions_for_scope_async

    now = datetime.now()

    # Create medallions with different graph node combinations
    medallions_config = [
        {
            "id": "med-graph-1",
            "nodes": ["repo:muse", "module:cli"],
            "tags": ["project_state"],
        },
        {
            "id": "med-graph-2",
            "nodes": ["repo:muse", "module:cli", "module:store"],
            "tags": ["project_state", "refactor"],
        },
        {
            "id": "med-graph-3",
            "nodes": ["repo:other", "module:api"],
            "tags": ["project_state"],
        },
        {
            "id": "med-graph-4",
            "nodes": ["repo:muse"],
            "tags": ["project_state"],
        },
        {
            "id": "med-graph-5",
            "nodes": ["repo:muse", "module:cli", "module:store", "module:api"],
            "tags": ["refactor"],
        },
    ]

    for i, config in enumerate(medallions_config):
        scope = MedallionScope(
            graph_nodes=config["nodes"],
            tags=config["tags"],
        )
        meta = MedallionMeta(
            medallion_id=config["id"],
            model="gpt-4",
            created_at=now + timedelta(seconds=i),
            updated_at=now + timedelta(seconds=i),
        )
        medallion = Medallion(
            meta=meta,
            scope=scope,
            summary=MedallionSummary(high_level=f"Graph test {i}", subsystems=[]),
            decisions=[],
            open_questions=[],
            affordances=MedallionAffordances(),
        )
        await in_memory_store.create(medallion)

    # Scenario 1: Query for repo:muse only (should match 1, 2, 4, 5)
    query1 = MedallionScope(
        graph_nodes=["repo:muse"],
        tags=["project_state"],
    )
    results1 = await _load_medallions_for_scope_async(in_memory_store, query1, limit=10)
    ids1 = {m.meta.medallion_id for m in results1}
    assert "med-graph-1" in ids1
    assert "med-graph-2" in ids1
    assert "med-graph-4" in ids1
    assert "med-graph-3" not in ids1  # Different repo
    assert "med-graph-5" not in ids1  # Different tag

    # Scenario 2: Query for repo:muse + module:cli (should match 1, 2)
    query2 = MedallionScope(
        graph_nodes=["repo:muse", "module:cli"],
        tags=["project_state"],
    )
    results2 = await _load_medallions_for_scope_async(in_memory_store, query2, limit=10)
    ids2 = {m.meta.medallion_id for m in results2}
    assert "med-graph-1" in ids2
    assert "med-graph-2" in ids2
    assert "med-graph-4" not in ids2  # Missing module:cli
    assert "med-graph-3" not in ids2  # Different repo

    # Scenario 3: Query for tag-only (refactor) - should match 2, 5
    query3 = MedallionScope(
        graph_nodes=[],  # Empty nodes
        tags=["refactor"],
    )
    results3 = await _load_medallions_for_scope_async(in_memory_store, query3, limit=10)
    ids3 = {m.meta.medallion_id for m in results3}
    assert "med-graph-2" in ids3
    assert "med-graph-5" in ids3
    assert len(ids3) == 2

    # Scenario 4: Query for complex subset (repo:muse + module:cli + module:store)
    # Should match med-graph-2 (has all three) and med-graph-5 (has all three)
    query4 = MedallionScope(
        graph_nodes=["repo:muse", "module:cli", "module:store"],
        tags=["project_state"],
    )
    results4 = await _load_medallions_for_scope_async(in_memory_store, query4, limit=10)
    ids4 = {m.meta.medallion_id for m in results4}
    assert "med-graph-2" in ids4
    assert "med-graph-1" not in ids4  # Missing module:store
    assert "med-graph-4" not in ids4  # Missing module:cli and module:store

    # Scenario 5: Query with no matching nodes (should return empty)
    query5 = MedallionScope(
        graph_nodes=["repo:nonexistent"],
        tags=["project_state"],
    )
    results5 = await _load_medallions_for_scope_async(in_memory_store, query5, limit=10)
    assert len(results5) == 0

