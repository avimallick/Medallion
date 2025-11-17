# Medallion

A semantic checkpointing layer for LLM agents that enables structured, versioned state management across sessions.

## Overview

Medallion provides a framework-agnostic way to create, persist, and retrieve semantic checkpoints of LLM agent reasoning state. It treats reasoning state as a first-class artifact, allowing agents to resume work from previous sessions with full context.

## Features

- **Structured Checkpoints**: Versioned JSON-based medallion schema with meta, scope, summary, decisions, and open questions
- **Framework Agnostic**: Works with LangChain, LangGraph, custom agents, and any Python LLM framework
- **SQLite Backend**: Local file-based storage with efficient scope-based queries
- **Scope-Based Retrieval**: Query medallions by graph nodes and tags with subset matching
- **Update Support**: Update existing medallions with new evidence without duplication

## Installation

```bash
pip install medallion
```

Or install from source:

```bash
git clone https://github.com/yourusername/medallion.git
cd medallion
pip install -e .
```

### Requirements

- Python 3.11 or higher
- pydantic>=2.0
- aiosqlite>=0.19.0

## Quick Start

### Basic Usage

```python
from medallion import (
    SQLiteMedallionStore,
    StubMedallionLLM,
    MedallionScope,
    Evidence,
    checkpoint_session,
    load_medallions_for_scope,
)

# Initialize store and LLM
store = SQLiteMedallionStore("medallions.db")
llm = StubMedallionLLM()

# Define scope for this checkpoint
scope = MedallionScope(
    graph_nodes=["repo:muse", "module:cli"],
    tags=["project_state", "refactor"],
)

# Create checkpoint at session end
evidence = Evidence(
    session_summary="Implemented CLI module with command routing",
    transcripts=["User requested help command", "System showed help menu"],
    artefacts={"commands": ["help", "start", "stop"]},
)

medallion = checkpoint_session(store, llm, scope, evidence)
print(f"Created medallion: {medallion.meta.medallion_id}")

# Load checkpoints for scope
medallions = load_medallions_for_scope(store, scope, limit=10)
print(f"Found {len(medallions)} medallions for scope")
```

### Loading Previous Checkpoints

```python
# Load most recent checkpoints for a scope
scope = MedallionScope(
    graph_nodes=["repo:muse"],
    tags=["project_state"],
)

medallions = load_medallions_for_scope(store, scope, limit=5)

for medallion in medallions:
    print(f"{medallion.meta.medallion_id}: {medallion.summary.high_level}")
    if medallion.decisions:
        print(f"  Decisions: {len(medallion.decisions)}")
    if medallion.open_questions:
        print(f"  Open questions: {len(medallion.open_questions)}")
```

### Updating Checkpoints

```python
# Subsequent checkpoint with same scope updates existing medallion
new_evidence = Evidence(
    session_summary="Added error handling to CLI module",
    transcripts=["User triggered error", "System handled gracefully"],
    artefacts={"error_rate": 0.01},
)

# This will update the existing medallion, not create a new one
updated_medallion = checkpoint_session(store, llm, scope, new_evidence)
print(f"Updated medallion: {updated_medallion.meta.medallion_id}")
print(f"Created: {updated_medallion.meta.created_at}")
print(f"Updated: {updated_medallion.meta.updated_at}")
```

## Core Concepts

### Medallion

A medallion is a structured checkpoint containing:

- **Meta**: ID, timestamps, schema version, model info
- **Scope**: Graph nodes and tags for querying
- **Summary**: High-level summary and subsystem breakdown
- **Decisions**: Key decisions made during reasoning
- **Open Questions**: Unresolved questions or blockers
- **Affordances**: Recommended entry points, things to avoid, invariants

### Scope Matching

Medallions are queried by scope using:

- **Graph Nodes**: Subset matching (requested nodes must be subset of stored nodes)
- **Tags**: Intersection matching (any tag overlap returns match)

Example:
```python
# Stored medallion has: graph_nodes=["repo:muse", "module:cli", "module:store"]
# Query with: graph_nodes=["repo:muse", "module:cli"]
# ✅ Matches (requested nodes are subset of stored nodes)

# Stored medallion has: tags=["project_state", "refactor"]
# Query with: tags=["refactor"]
# ✅ Matches (tag overlap)
```

### Evidence

Evidence is the input data for checkpoint creation:

- **session_summary**: High-level summary of the session
- **transcripts**: List of conversation or action transcripts
- **artefacts**: Dictionary of relevant artefacts (file paths, IDs, etc.)

## Integration Examples

### With LangChain

```python
from langchain.agents import AgentExecutor
from medallion import SQLiteMedallionStore, StubMedallionLLM, checkpoint_session

store = SQLiteMedallionStore("langchain_sessions.db")
llm = StubMedallionLLM()

# At session start: Load previous checkpoints
scope = MedallionScope(graph_nodes=["project:my-agent"], tags=["session"])
medallions = load_medallions_for_scope(store, scope)

# Inject context into agent
context = "\n".join([m.summary.high_level for m in medallions])

# Run agent
agent = AgentExecutor(...)
result = agent.run(context + "\nUser query: ...")

# At session end: Create checkpoint
evidence = Evidence(
    session_summary=result["summary"],
    transcripts=result["transcripts"],
    artefacts=result["artefacts"],
)
checkpoint_session(store, llm, scope, evidence)
```

### With LangGraph

```python
from langgraph.graph import StateGraph
from medallion import SQLiteMedallionStore, checkpoint_session, load_medallions_for_scope

store = SQLiteMedallionStore("langgraph_sessions.db")
llm = StubMedallionLLM()

def on_session_start(state):
    scope = MedallionScope(
        graph_nodes=[state["project_id"]],
        tags=["project_state"],
    )
    medallions = load_medallions_for_scope(store, scope)
    state["medallions"] = medallions
    return state

def on_session_end(state):
    scope = MedallionScope(
        graph_nodes=[state["project_id"]],
        tags=["project_state"],
    )
    evidence = Evidence(
        session_summary=state["summary"],
        transcripts=state.get("transcripts", []),
        artefacts=state.get("artefacts", {}),
    )
    checkpoint_session(store, llm, scope, evidence)
    return state

# Build graph
graph = StateGraph(...)
graph.add_node("load_checkpoint", on_session_start)
graph.add_node("process", your_processing_node)
graph.add_node("save_checkpoint", on_session_end)
```

### Custom Agent

```python
from medallion import (
    SQLiteMedallionStore,
    MedallionLLM,
    load_medallions_for_scope,
    checkpoint_session,
    MedallionScope,
    Evidence,
)

class MyAgent:
    def __init__(self, store: SQLiteMedallionStore, llm: MedallionLLM):
        self.store = store
        self.llm = llm

    async def start_session(self, project_id: str):
        """Load medallions at session start."""
        scope = MedallionScope(
            graph_nodes=[f"repo:{project_id}"],
            tags=["project_state"],
        )
        medallions = load_medallions_for_scope(self.store, scope)
        
        # Inject medallion context into agent
        context = self._format_medallions(medallions)
        return context

    async def end_session(
        self,
        project_id: str,
        summary: str,
        transcripts: list[str],
        artefacts: dict,
    ):
        """Save checkpoint at session end."""
        scope = MedallionScope(
            graph_nodes=[f"repo:{project_id}"],
            tags=["project_state"],
        )
        evidence = Evidence(
            session_summary=summary,
            transcripts=transcripts,
            artefacts=artefacts,
        )
        return checkpoint_session(self.store, self.llm, scope, evidence)

    def _format_medallions(self, medallions: list[Medallion]) -> str:
        """Format medallions for agent context."""
        if not medallions:
            return "No previous checkpoints found."
        
        lines = ["Previous checkpoints:"]
        for m in medallions:
            lines.append(f"- {m.meta.medallion_id}: {m.summary.high_level}")
            if m.decisions:
                lines.append(f"  Decisions: {', '.join(d.statement for d in m.decisions)}")
            if m.open_questions:
                lines.append(f"  Open: {', '.join(q.question for q in m.open_questions)}")
        
        return "\n".join(lines)
```

## API Reference

### Core Types

- `Medallion`: Main checkpoint data structure
- `MedallionScope`: Query scope with graph nodes and tags
- `Evidence`: Input data for checkpoint creation

### Store

- `MedallionStore`: Abstract interface for storage
- `SQLiteMedallionStore`: SQLite implementation

### LLM

- `MedallionLLM`: Abstract interface for LLM operations
- `StubMedallionLLM`: Stub implementation for testing

### Session Helpers

- `checkpoint_session(store, llm, scope, evidence)`: Create or update checkpoint
- `load_medallions_for_scope(store, scope, limit=10)`: Load checkpoints for scope

### Exceptions

- `MedallionError`: Base exception
- `SchemaValidationError`: Schema validation failures
- `StoreError`: Storage operation failures
- `LLMError`: LLM operation failures

## Advanced Usage

### Async API

For async frameworks, use the async versions directly:

```python
from medallion.session import _checkpoint_session_async, _load_medallions_for_scope_async

# Async checkpoint creation
medallion = await _checkpoint_session_async(store, llm, scope, evidence)

# Async loading
medallions = await _load_medallions_for_scope_async(store, scope, limit=10)
```

### Custom LLM Implementation

Implement the `MedallionLLM` protocol to integrate with your LLM:

```python
from medallion.llm import MedallionLLM
from medallion.types import Medallion, MedallionScope, Evidence

class MyMedallionLLM:
    async def generate(self, scope: MedallionScope, evidence: Evidence) -> Medallion:
        # Call your LLM API
        # Parse response into Medallion
        # Return medallion
        pass

    async def update(self, existing: Medallion, new_evidence: Evidence) -> Medallion:
        # Call your LLM API to merge evidence
        # Update existing medallion
        # Return updated medallion
        pass
```

### Context Manager Usage

```python
async with SQLiteMedallionStore("medallions.db") as store:
    llm = StubMedallionLLM()
    
    scope = MedallionScope(graph_nodes=["repo:muse"], tags=["test"])
    evidence = Evidence(session_summary="Test session")
    
    medallion = await _checkpoint_session_async(store, llm, scope, evidence)
    # Database connection automatically closed on exit
```

## Development

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=medallion --cov-report=html
```

### Type Checking

```bash
mypy medallion
```

### Linting

```bash
ruff check medallion
black medallion
```

## Documentation

- [Full Documentation](docs/)
- [Product Requirements](docs/medallion_prd.md)
- [Technical Specification](specs/001-medallion-v1/spec.md)
- [Quick Start Guide](specs/001-medallion-v1/quickstart.md)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

