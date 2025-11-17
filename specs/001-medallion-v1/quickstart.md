# Quickstart: Medallion Library v1

**Date**: 2025-11-17  
**Feature**: Medallion Library v1

## Installation

```bash
# Install Medallion (when published)
pip install medallion

# Or install from source
git clone https://github.com/yourorg/medallion.git
cd medallion
pip install -e .
```

## Basic Usage

### 1. Create a Store

```python
from pathlib import Path
from medallion import SQLiteMedallionStore

# Create a SQLite store (default: medallion.db)
store = SQLiteMedallionStore("my_project.db")

# Use async context manager for automatic cleanup
async with SQLiteMedallionStore("my_project.db") as store:
    # Use store here
    pass
```

### 2. Create a Checkpoint

```python
from medallion import (
    MedallionScope,
    Evidence,
    StubMedallionLLM,
    checkpoint_session
)

# Define scope for this checkpoint
scope = MedallionScope(
    graph_nodes=["repo:muse", "module:cli"],
    tags=["project_state", "refactor_sprint_1"]
)

# Collect evidence from the session
evidence = Evidence(
    session_summary="Explored repository structure, decided to use Python 3.11+",
    transcripts=[
        "User: Let's start refactoring the CLI module",
        "Agent: I'll analyze the current structure first"
    ],
    artefacts={
        "files_analyzed": ["cli/main.py", "cli/utils.py"],
        "decisions_made": ["Use async/await for I/O operations"]
    }
)

# Create checkpoint (stub LLM for now)
llm = StubMedallionLLM()
medallion = checkpoint_session(store, llm, scope, evidence)

print(f"Created medallion: {medallion.meta.medallion_id}")
```

### 3. Load Checkpoints

```python
from medallion import load_medallions_for_scope, MedallionScope

# Load medallions for a scope
scope = MedallionScope(
    graph_nodes=["repo:muse"],
    tags=["project_state"]
)

medallions = load_medallions_for_scope(store, scope, limit=3)

for medallion in medallions:
    print(f"Medallion: {medallion.meta.medallion_id}")
    print(f"  Summary: {medallion.summary.high_level[:100]}...")
    print(f"  Decisions: {len(medallion.decisions)}")
    print(f"  Open Questions: {len(medallion.open_questions)}")
```

### 4. Update a Checkpoint

```python
# Update existing checkpoint with new evidence
new_evidence = Evidence(
    session_summary="Resolved question Q-001: We'll add vector search in v2",
    transcripts=["Agent: Based on performance benchmarks, deferring vector search"],
    artefacts={"resolved_questions": ["Q-001"]}
)

# checkpoint_session automatically detects existing medallion and updates it
updated_medallion = checkpoint_session(store, llm, scope, new_evidence)

print(f"Updated medallion: {updated_medallion.meta.medallion_id}")
print(f"Created at: {updated_medallion.meta.created_at}")
print(f"Updated at: {updated_medallion.meta.updated_at}")
```

### 5. Query by ID

```python
from medallion import MedallionStore

# Get specific medallion by ID
medallion_id = "med-001"
medallion = await store.get_by_id(medallion_id)

if medallion:
    print(f"Found medallion: {medallion.meta.medallion_id}")
    print(f"Status: {medallion.meta.status}")
else:
    print("Medallion not found")
```

## Integration with Agent Frameworks

### LangChain Example

```python
from langchain.agents import AgentExecutor
from medallion import (
    SQLiteMedallionStore,
    load_medallions_for_scope,
    checkpoint_session,
    MedallionScope,
    Evidence
)

# Initialize store and LLM
store = SQLiteMedallionStore("agent_sessions.db")
llm = YourMedallionLLM()  # Your LLM implementation

# Session start: Load medallions
scope = MedallionScope(graph_nodes=["repo:myproject"], tags=["project_state"])
medallions = load_medallions_for_scope(store, scope)

# Inject medallions into agent context
agent_context = "\n".join([
    f"Previous checkpoint: {m.model_dump_json()}"
    for m in medallions
])

# Run agent
agent_executor = AgentExecutor(...)
result = agent_executor.run(agent_context + "\nUser query: ...")

# Session end: Create/update checkpoint
evidence = Evidence(
    session_summary=result["summary"],
    transcripts=result["transcripts"],
    artefacts=result["artefacts"]
)
checkpoint_session(store, llm, scope, evidence)
```

### LangGraph Example

```python
from langgraph.graph import StateGraph
from medallion import (
    SQLiteMedallionStore,
    load_medallions_for_scope,
    checkpoint_session,
    MedallionScope,
    Evidence
)

# Initialize store
store = SQLiteMedallionStore("langgraph_sessions.db")
llm = YourMedallionLLM()

# Define graph with medallion hooks
def on_session_start(state):
    scope = MedallionScope(
        graph_nodes=[state["project_id"]],
        tags=["project_state"]
    )
    medallions = load_medallions_for_scope(store, scope)
    state["medallions"] = medallions
    return state

def on_session_end(state):
    scope = MedallionScope(
        graph_nodes=[state["project_id"]],
        tags=["project_state"]
    )
    evidence = Evidence(
        session_summary=state["summary"],
        transcripts=state.get("transcripts", []),
        artefacts=state.get("artefacts", {})
    )
    checkpoint_session(store, llm, scope, evidence)
    return state

# Build graph
graph = StateGraph(...)
graph.add_node("load_checkpoint", on_session_start)
graph.add_node("process", your_processing_node)
graph.add_node("save_checkpoint", on_session_end)
```

### Custom Agent Example

```python
from medallion import (
    SQLiteMedallionStore,
    load_medallions_for_scope,
    checkpoint_session,
    MedallionScope,
    Evidence,
    Medallion
)

class MyAgent:
    def __init__(self, store: SQLiteMedallionStore, llm: MedallionLLM):
        self.store = store
        self.llm = llm
    
    async def start_session(self, project_id: str):
        """Load medallions at session start."""
        scope = MedallionScope(
            graph_nodes=[f"repo:{project_id}"],
            tags=["project_state"]
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
        artefacts: dict
    ):
        """Save checkpoint at session end."""
        scope = MedallionScope(
            graph_nodes=[f"repo:{project_id}"],
            tags=["project_state"]
        )
        evidence = Evidence(
            session_summary=summary,
            transcripts=transcripts,
            artefacts=artefacts
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

# Usage
async with SQLiteMedallionStore("agent.db") as store:
    llm = YourMedallionLLM()
    agent = MyAgent(store, llm)
    
    # Session start
    context = await agent.start_session("myproject")
    
    # ... run agent ...
    
    # Session end
    await agent.end_session(
        "myproject",
        "Session summary...",
        ["transcript 1", "transcript 2"],
        {"artefacts": "data"}
    )
```

## Advanced Usage

### Custom LLM Implementation

```python
from medallion import MedallionLLM, Medallion, MedallionScope, Evidence
import openai  # or your LLM client

class OpenAIMedallionLLM:
    """OpenAI-based implementation of MedallionLLM."""
    
    def __init__(self, client: openai.AsyncOpenAI):
        self.client = client
    
    async def generate(
        self,
        scope: MedallionScope,
        evidence: Evidence
    ) -> Medallion:
        """Generate medallion using OpenAI."""
        prompt = self._build_generate_prompt(scope, evidence)
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a strict state summarizer..."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        json_str = response.choices[0].message.content
        return Medallion.model_validate_json(json_str)
    
    async def update(
        self,
        existing: Medallion,
        new_evidence: Evidence
    ) -> Medallion:
        """Update medallion using OpenAI."""
        prompt = self._build_update_prompt(existing, new_evidence)
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are updating an existing medallion..."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        json_str = response.choices[0].message.content
        return Medallion.model_validate_json(json_str)
    
    def _build_generate_prompt(self, scope: MedallionScope, evidence: Evidence) -> str:
        """Build prompt for medallion generation."""
        # Implementation details...
        pass
    
    def _build_update_prompt(self, existing: Medallion, new_evidence: Evidence) -> str:
        """Build prompt for medallion update."""
        # Implementation details...
        pass

# Usage
import openai
client = openai.AsyncOpenAI(api_key="...")
llm = OpenAIMedallionLLM(client)
```

### Error Handling

```python
from medallion import (
    MedallionError,
    SchemaValidationError,
    StoreError,
    LLMError
)

try:
    medallion = checkpoint_session(store, llm, scope, evidence)
except SchemaValidationError as e:
    print(f"Schema validation failed: {e}")
    # Handle validation error
except StoreError as e:
    print(f"Store operation failed: {e}")
    # Handle store error
except LLMError as e:
    print(f"LLM operation failed: {e}")
    # Handle LLM error
except MedallionError as e:
    print(f"Medallion error: {e}")
    # Handle general error
```

## Testing

```python
import pytest
from medallion import (
    SQLiteMedallionStore,
    StubMedallionLLM,
    MedallionScope,
    Evidence,
    checkpoint_session,
    load_medallions_for_scope
)

@pytest.fixture
async def store():
    """Fixture for in-memory test store."""
    store = SQLiteMedallionStore(":memory:")
    yield store
    await store.close()

@pytest.fixture
def llm():
    """Fixture for stub LLM."""
    return StubMedallionLLM()

@pytest.mark.asyncio
async def test_create_checkpoint(store, llm):
    """Test creating a checkpoint."""
    scope = MedallionScope(graph_nodes=["repo:test"], tags=["test"])
    evidence = Evidence(session_summary="Test session")
    
    medallion = checkpoint_session(store, llm, scope, evidence)
    
    assert medallion.meta.medallion_id
    assert medallion.meta.status == "active"
    assert medallion.scope == scope

@pytest.mark.asyncio
async def test_load_checkpoint(store, llm):
    """Test loading checkpoints."""
    scope = MedallionScope(graph_nodes=["repo:test"], tags=["test"])
    evidence = Evidence(session_summary="Test session")
    
    # Create checkpoint
    created = checkpoint_session(store, llm, scope, evidence)
    
    # Load checkpoint
    loaded = load_medallions_for_scope(store, scope)
    
    assert len(loaded) == 1
    assert loaded[0].meta.medallion_id == created.meta.medallion_id
```

## Next Steps

- See [data-model.md](./data-model.md) for detailed schema definitions
- See [contracts/api.md](./contracts/api.md) for API reference
- See [spec.md](./spec.md) for feature requirements

