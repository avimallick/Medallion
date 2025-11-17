"""
Medallion: A semantic checkpointing layer for LLM agents.

This package provides structured, versioned checkpoints that enable LLM agents
to resume work from previous sessions with consistent state.
"""

__version__ = "0.1.0"

# Core types
# LLM interfaces and implementations
from medallion.llm import MedallionLLM, StubMedallionLLM

# Session helpers
from medallion.session import checkpoint_session, load_medallions_for_scope
from medallion.sqlite_store import SQLiteMedallionStore

# Store interfaces and implementations
from medallion.store import MedallionStore
from medallion.types import (
    Evidence,
    LLMError,
    Medallion,
    MedallionError,
    MedallionScope,
    SchemaValidationError,
    StoreError,
)

__all__ = [
    # Version
    "__version__",
    # Core types
    "Medallion",
    "MedallionScope",
    "Evidence",
    # Store interfaces and implementations
    "MedallionStore",
    "SQLiteMedallionStore",
    # LLM interfaces and implementations
    "MedallionLLM",
    "StubMedallionLLM",
    # Session helpers
    "load_medallions_for_scope",
    "checkpoint_session",
    # Exception classes
    "MedallionError",
    "SchemaValidationError",
    "StoreError",
    "LLMError",
]
