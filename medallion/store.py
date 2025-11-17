"""
MedallionStore interface definition.

This module defines the abstract Protocol for medallion storage operations.
Concrete implementations (e.g., SQLiteMedallionStore) must satisfy this interface.
"""

from typing import Protocol

from medallion.types import Medallion, MedallionScope


class MedallionStore(Protocol):
    """Abstract interface for medallion storage operations."""

    async def create(self, medallion: Medallion) -> None:  # pragma: no cover
        """
        Persist a new medallion.

        Args:
            medallion: The medallion to persist

        Raises:
            StoreError: If medallion already exists (by ID) or persistence fails
            SchemaValidationError: If medallion schema validation fails
        """
        ...

    async def update(self, medallion: Medallion) -> None:  # pragma: no cover
        """
        Update an existing medallion.

        Args:
            medallion: The medallion to update (must have existing ID)

        Raises:
            StoreError: If medallion doesn't exist or update fails
            SchemaValidationError: If medallion schema validation fails
        """
        ...

    async def get_by_id(self, medallion_id: str) -> Medallion | None:  # pragma: no cover
        """
        Fetch a medallion by its ID.

        Args:
            medallion_id: The unique identifier of the medallion

        Returns:
            The medallion if found, None otherwise

        Raises:
            StoreError: If database query fails
        """
        ...

    async def get_latest_for_scope(
        self,
        scope: MedallionScope,
        limit: int = 10,
    ) -> list[Medallion]:  # pragma: no cover
        """
        Fetch the latest medallions matching the given scope.

        Scope matching rules:
        - graph_nodes: Requested nodes must be a subset of stored nodes (subset match)
        - tags: Exact match or intersection (implementation decision)
        - Results ordered by updated_at DESC (latest first)

        Args:
            scope: The scope to match against
            limit: Maximum number of medallions to return (default: 10)

        Returns:
            List of matching medallions, ordered by updated_at DESC

        Raises:
            StoreError: If database query fails

        Edge cases:
        - Empty scope (no graph_nodes, no tags): Returns empty list
        - No matches: Returns empty list (not an error)
        - Limit 0 or negative: Returns empty list
        """
        ...

