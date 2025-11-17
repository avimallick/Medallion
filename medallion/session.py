"""
Session helper functions for medallion checkpointing.

This module provides convenience functions for common medallion operations
like creating/updating checkpoints and loading medallions for a scope.
"""

import asyncio
from typing import List

from medallion.llm import MedallionLLM
from medallion.store import MedallionStore
from medallion.types import (
    Evidence,
    LLMError,
    Medallion,
    MedallionScope,
    SchemaValidationError,
    StoreError,
)


async def _checkpoint_session_async(
    store: MedallionStore,
    llm: MedallionLLM,
    scope: MedallionScope,
    evidence: Evidence,
) -> Medallion:
    """
    Create or update a medallion for a session (async implementation).

    Behavior:
    1. Check if active medallion exists for scope (via get_latest_for_scope)
    2. If none exists: call llm.generate() → store.create()
    3. If exists: call llm.update(existing, evidence) → store.update()
    4. Return the created/updated medallion

    Args:
        store: The medallion store instance
        llm: The LLM helper instance
        scope: The scope for this checkpoint
        evidence: Evidence data from the session

    Returns:
        The created or updated medallion

    Raises:
        StoreError: If store operations fail
        LLMError: If LLM operations fail
        SchemaValidationError: If medallion validation fails
    """
    try:
        # Check for existing active medallion
        existing_medallions = await store.get_latest_for_scope(scope, limit=1)

        if not existing_medallions:
            # No existing medallion - create new one
            try:
                new_medallion = await llm.generate(scope, evidence)
                await store.create(new_medallion)
                return new_medallion
            except LLMError as e:
                raise LLMError(
                    f"Failed to generate medallion for scope {scope}: {e}"
                ) from e
            except StoreError as e:
                raise StoreError(
                    f"Failed to create medallion in store: {e}"
                ) from e
            except SchemaValidationError as e:
                raise SchemaValidationError(
                    f"Generated medallion schema validation failed: {e}"
                ) from e
        else:
            # Existing medallion found - update it
            existing_medallion = existing_medallions[0]  # Use most recent
            try:
                updated_medallion = await llm.update(existing_medallion, evidence)
                await store.update(updated_medallion)
                return updated_medallion
            except LLMError as e:
                raise LLMError(
                    f"Failed to update medallion {existing_medallion.meta.medallion_id}: {e}"
                ) from e
            except StoreError as e:
                raise StoreError(
                    f"Failed to update medallion in store: {e}"
                ) from e
            except SchemaValidationError as e:
                raise SchemaValidationError(
                    f"Updated medallion schema validation failed: {e}"
                ) from e
    except (StoreError, LLMError, SchemaValidationError):
        # Re-raise our custom errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise StoreError(
            f"Unexpected error during checkpoint_session: {e}"
        ) from e


def checkpoint_session(
    store: MedallionStore,
    llm: MedallionLLM,
    scope: MedallionScope,
    evidence: Evidence,
) -> Medallion:
    """
    Create or update a medallion for a session (sync wrapper).

    This is a sync wrapper around the async implementation. For async frameworks,
    use _checkpoint_session_async directly.

    Args:
        store: The medallion store instance
        llm: The LLM helper instance
        scope: The scope for this checkpoint
        evidence: Evidence data from the session

    Returns:
        The created or updated medallion

    Raises:
        StoreError: If store operations fail
        LLMError: If LLM operations fail
        SchemaValidationError: If medallion validation fails

    Note:
        This function uses asyncio.run() internally. If called from an async
        context (e.g., inside an async function), use _checkpoint_session_async
        directly instead.
    """
    return asyncio.run(_checkpoint_session_async(store, llm, scope, evidence))


async def _load_medallions_for_scope_async(
    store: MedallionStore,
    scope: MedallionScope,
    limit: int = 10,
) -> List[Medallion]:
    """
    Load medallions matching a scope (async implementation).

    Args:
        store: The medallion store instance
        scope: The scope to match against
        limit: Maximum number of medallions to return (default: 10)

    Returns:
        List of matching medallions, ordered by updated_at DESC

    Raises:
        StoreError: If store operations fail
    """
    try:
        return await store.get_latest_for_scope(scope, limit=limit)
    except StoreError:
        raise
    except Exception as e:
        raise StoreError(
            f"Unexpected error loading medallions for scope: {e}"
        ) from e


def load_medallions_for_scope(
    store: MedallionStore,
    scope: MedallionScope,
    limit: int = 10,
) -> List[Medallion]:
    """
    Load medallions matching a scope (sync wrapper).

    This is a sync wrapper around the async implementation. For async frameworks,
    use _load_medallions_for_scope_async directly.

    Args:
        store: The medallion store instance
        scope: The scope to match against
        limit: Maximum number of medallions to return (default: 10)

    Returns:
        List of matching medallions, ordered by updated_at DESC

    Raises:
        StoreError: If store operations fail

    Note:
        This function uses asyncio.run() internally. If called from an async
        context (e.g., inside an async function), use _load_medallions_for_scope_async
        directly instead.
    """
    return asyncio.run(_load_medallions_for_scope_async(store, scope, limit))

