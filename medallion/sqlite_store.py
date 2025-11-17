"""
SQLite-backed implementation of MedallionStore.

This module provides a concrete SQLite implementation of the MedallionStore
interface for persisting and retrieving medallions.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite

from medallion.types import (
    Medallion,
    MedallionScope,
    SchemaValidationError,
    StoreError,
)


class SQLiteMedallionStore:
    """SQLite-backed implementation of MedallionStore.

    This class provides a concrete SQLite implementation of the MedallionStore
    protocol. It stores medallions in a SQLite database with efficient indexing
    for scope-based queries.

    Example:
        ```python
        from medallion import SQLiteMedallionStore, Medallion

        # Create store with default database file
        store = SQLiteMedallionStore("medallions.db")

        # Use async context manager for automatic cleanup
        async with SQLiteMedallionStore("medallions.db") as store:
            # Create medallion
            await store.create(medallion)

            # Load by ID
            retrieved = await store.get_by_id("med-001")

            # Query by scope
            medallions = await store.get_latest_for_scope(scope, limit=10)
        ```
    """

    def __init__(self, db_path: Path | str = "medallion.db") -> None:
        """
        Initialize SQLite store.

        Args:
            db_path: Path to SQLite database file (default: "medallion.db")
                    Use ":memory:" for in-memory database (useful for testing)

        Raises:
            StoreError: If database initialization fails
        """
        self.db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def _ensure_initialized(self) -> None:
        """Ensure database connection is open and schema is created."""
        if self._conn is None:
            try:
                self._conn = await aiosqlite.connect(self.db_path)
                await self._conn.execute("PRAGMA foreign_keys = ON")
                await self._create_schema()
                await self._conn.commit()
            except sqlite3.Error as e:
                raise StoreError(f"Failed to initialize database: {e}") from e

    async def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        assert self._conn is not None, "Connection must be initialized"

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS medallions (
            id TEXT PRIMARY KEY,
            content_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT NOT NULL,
            scope_graph_nodes TEXT NOT NULL,
            scope_tags TEXT NOT NULL,
            knowledge_min_ts TEXT,
            knowledge_max_ts TEXT,
            schema_version TEXT NOT NULL DEFAULT 'medallion.v1'
        )
        """
        await self._conn.execute(create_table_sql)

        # Create indexes for efficient queries
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_medallions_status ON medallions(status)",
            "CREATE INDEX IF NOT EXISTS idx_medallions_updated_at ON medallions(updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_medallions_scope_nodes ON medallions(scope_graph_nodes)",
            "CREATE INDEX IF NOT EXISTS idx_medallions_scope_tags ON medallions(scope_tags)",
        ]

        for index_sql in indexes:
            await self._conn.execute(index_sql)

    async def create(self, medallion: Medallion) -> None:
        """
        Persist a new medallion.

        Args:
            medallion: The medallion to persist

        Raises:
            StoreError: If medallion already exists (by ID) or persistence fails
            SchemaValidationError: If medallion schema validation fails
        """
        await self._ensure_initialized()
        assert self._conn is not None, "Connection must be initialized"

        # Validate medallion schema (Pydantic does this on instantiation, but double-check)
        try:
            # Serialize to validate JSON serialization works
            json_str = medallion.model_dump_json()
        except Exception as e:
            raise SchemaValidationError(
                f"Medallion schema validation failed: {e}"
            ) from e

        # Check if medallion already exists
        existing = await self.get_by_id(medallion.meta.medallion_id)
        if existing is not None:
            raise StoreError(
                f"Medallion with ID {medallion.meta.medallion_id} already exists"
            )

        # Serialize scope fields for indexing
        try:
            scope_nodes_json = json.dumps(medallion.scope.graph_nodes)
            scope_tags_json = json.dumps(medallion.scope.tags)
        except (TypeError, ValueError) as e:
            raise SchemaValidationError(
                f"Failed to serialize scope fields to JSON: {e}"
            ) from e

        # Format timestamps as ISO 8601 strings
        created_at_str = medallion.meta.created_at.isoformat()
        updated_at_str = medallion.meta.updated_at.isoformat()
        knowledge_min_str = (
            medallion.meta.knowledge_min_ts.isoformat()
            if medallion.meta.knowledge_min_ts
            else None
        )
        knowledge_max_str = (
            medallion.meta.knowledge_max_ts.isoformat()
            if medallion.meta.knowledge_max_ts
            else None
        )

        try:
            insert_sql = """
            INSERT INTO medallions (
                id, content_json, created_at, updated_at, status,
                scope_graph_nodes, scope_tags, knowledge_min_ts, knowledge_max_ts,
                schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            await self._conn.execute(
                insert_sql,
                (
                    medallion.meta.medallion_id,
                    json_str,
                    created_at_str,
                    updated_at_str,
                    medallion.meta.status,
                    scope_nodes_json,
                    scope_tags_json,
                    knowledge_min_str,
                    knowledge_max_str,
                    medallion.meta.schema_version,
                ),
            )
            await self._conn.commit()
        except sqlite3.IntegrityError as e:
            # Handle race condition if medallion was created between check and insert
            raise StoreError(
                f"Medallion with ID {medallion.meta.medallion_id} already exists"
            ) from e
        except sqlite3.Error as e:
            raise StoreError(f"Failed to create medallion: {e}") from e

    async def update(self, medallion: Medallion) -> None:
        """
        Update an existing medallion.

        Args:
            medallion: The medallion to update (must have existing ID)

        Raises:
            StoreError: If medallion doesn't exist or update fails
            SchemaValidationError: If medallion schema validation fails
        """
        await self._ensure_initialized()
        assert self._conn is not None, "Connection must be initialized"

        # Validate medallion schema
        try:
            json_str = medallion.model_dump_json()
        except Exception as e:
            raise SchemaValidationError(
                f"Medallion schema validation failed: {e}"
            ) from e

        # Check if medallion exists
        existing = await self.get_by_id(medallion.meta.medallion_id)
        if existing is None:
            raise StoreError(
                f"Medallion with ID {medallion.meta.medallion_id} not found"
            )

        # Serialize scope fields
        try:
            scope_nodes_json = json.dumps(medallion.scope.graph_nodes)
            scope_tags_json = json.dumps(medallion.scope.tags)
        except (TypeError, ValueError) as e:
            raise SchemaValidationError(
                f"Failed to serialize scope fields to JSON: {e}"
            ) from e

        # Format timestamps (created_at is preserved, not updated)
        updated_at_str = medallion.meta.updated_at.isoformat()
        knowledge_min_str = (
            medallion.meta.knowledge_min_ts.isoformat()
            if medallion.meta.knowledge_min_ts
            else None
        )
        knowledge_max_str = (
            medallion.meta.knowledge_max_ts.isoformat()
            if medallion.meta.knowledge_max_ts
            else None
        )

        try:
            update_sql = """
            UPDATE medallions SET
                content_json = ?,
                updated_at = ?,
                status = ?,
                scope_graph_nodes = ?,
                scope_tags = ?,
                knowledge_min_ts = ?,
                knowledge_max_ts = ?
            WHERE id = ?
            """
            await self._conn.execute(
                update_sql,
                (
                    json_str,
                    updated_at_str,
                    medallion.meta.status,
                    scope_nodes_json,
                    scope_tags_json,
                    knowledge_min_str,
                    knowledge_max_str,
                    medallion.meta.medallion_id,
                ),
            )
            await self._conn.commit()
        except sqlite3.Error as e:
            raise StoreError(f"Failed to update medallion: {e}") from e

    async def get_by_id(self, medallion_id: str) -> Medallion | None:
        """
        Fetch a medallion by its ID.

        Args:
            medallion_id: The unique identifier of the medallion

        Returns:
            The medallion if found, None otherwise

        Raises:
            StoreError: If database query fails
        """
        await self._ensure_initialized()
        assert self._conn is not None, "Connection must be initialized"

        try:
            select_sql = "SELECT content_json FROM medallions WHERE id = ?"
            async with self._conn.execute(select_sql, (medallion_id,)) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None

                json_str = row[0]
                return Medallion.model_validate_json(json_str)
        except sqlite3.Error as e:
            raise StoreError(f"Failed to get medallion by ID: {e}") from e
        except Exception as e:
            raise SchemaValidationError(
                f"Failed to deserialize medallion from JSON: {e}"
            ) from e

    async def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10,
    ) -> list[Medallion]:
        """
        Fetch the latest medallions matching the given scope.

        Scope matching rules:
        - graph_nodes: Requested nodes must be a subset of stored nodes (subset match)
        - tags: Intersection matching (any tag overlap)
        - Results ordered by updated_at DESC (latest first)

        Args:
            scope: The scope to match against
            limit: Maximum number of medallions to return (default: 10)

        Returns:
            List of matching medallions, ordered by updated_at DESC

        Raises:
            StoreError: If database query fails
        """
        await self._ensure_initialized()
        assert self._conn is not None, "Connection must be initialized"

        # Handle edge cases
        if limit <= 0:
            return []

        # For v1, use Python-side filtering for subset matching (simpler than SQLite JSON1)
        # Load all medallions with matching tags, then filter by graph_nodes subset
        requested_nodes = set(scope.graph_nodes)
        requested_tags = set(scope.tags)

        try:
            # Query by tags first (if tags provided), then filter by graph_nodes
            if requested_tags:
                # Use JSON LIKE for tag matching (simple intersection)
                # This is a basic implementation - can be optimized later
                select_sql = """
                SELECT content_json, scope_graph_nodes
                FROM medallions
                WHERE status = 'active'
                ORDER BY updated_at DESC
                LIMIT ?
                """
                async with self._conn.execute(select_sql, (limit * 5,)) as cursor:
                    rows = await cursor.fetchall()
            else:
                # No tags specified, get all active medallions
                select_sql = """
                SELECT content_json, scope_graph_nodes
                FROM medallions
                WHERE status = 'active'
                ORDER BY updated_at DESC
                LIMIT ?
                """
                async with self._conn.execute(select_sql, (limit * 5,)) as cursor:
                    rows = await cursor.fetchall()

            # Filter by scope matching (subset match for graph_nodes, intersection for tags)
            results: list[Medallion] = []
            for row in rows:
                try:
                    medallion = Medallion.model_validate_json(row[0])
                    stored_nodes = set(medallion.scope.graph_nodes)
                    stored_tags = set(medallion.scope.tags)

                    # Subset matching for graph_nodes
                    nodes_match = (
                        not requested_nodes
                        or requested_nodes.issubset(stored_nodes)
                    )
                    # Intersection matching for tags
                    tags_match = (
                        not requested_tags or bool(requested_tags & stored_tags)
                    )

                    if nodes_match and tags_match:
                        results.append(medallion)
                        if len(results) >= limit:
                            break
                except Exception:
                    # Skip invalid medallions
                    continue

            return results
        except sqlite3.Error as e:
            raise StoreError(f"Failed to get medallions for scope: {e}") from e

    async def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self) -> "SQLiteMedallionStore":
        """Async context manager entry."""
        await self._ensure_initialized()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Async context manager exit (calls close)."""
        await self.close()

