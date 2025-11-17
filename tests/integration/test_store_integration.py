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

