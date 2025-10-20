"""
Medallion Python Examples

This module contains examples demonstrating how to use Medallion as a Python package.
"""

from medallion import MedallionClient, Workflow, Agent, KnowledgeGraph
from medallion.providers import OllamaProvider, OpenAIProvider


def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Medallion Usage ===")
    
    # Create a client
    client = MedallionClient()
    
    # Build a project
    result = client.build_project("1+4", "my-ai-app")
    print(f"Built project: {result}")
    
    # Query the knowledge graph
    kg = KnowledgeGraph(client)
    stats = kg.get_statistics()
    print(f"Knowledge graph stats: {stats}")


def example_workflow_creation():
    """Example of creating and running a workflow"""
    print("\n=== Workflow Creation Example ===")
    
    # Create a workflow programmatically
    from medallion.core.workflow import Workflow, WorkflowStep
    
    workflow = Workflow(
        name="simple_qa",
        description="Simple question answering workflow",
        agents=["researcher", "writer"],
        steps=[
            WorkflowStep(
                name="research",
                agent="researcher",
                input="{{.question}}"
            ),
            WorkflowStep(
                name="write_answer",
                agent="writer",
                input="{{.research.output}}",
                depends_on=["research"]
            )
        ]
    )
    
    # Save workflow to file
    workflow.to_file("simple_qa.yaml")
    print("Created workflow: simple_qa.yaml")
    
    # Run the workflow
    client = MedallionClient()
    result = client.run_workflow("simple_qa.yaml", {"question": "What is Python?"})
    print(f"Workflow result: {result}")


def example_agent_creation():
    """Example of creating agents"""
    print("\n=== Agent Creation Example ===")
    
    # Create an agent programmatically
    from medallion.core.agent import Agent, ModelConfig
    
    agent = Agent(
        name="researcher",
        type="worker",
        description="Research agent that finds information",
        model=ModelConfig(
            provider="ollama",
            model="llama3.1",
            temperature=0.7
        ),
        prompts={
            "system": "You are a research agent. Find relevant information about the given topic."
        },
        tools=["web_search", "document_retrieval"]
    )
    
    # Save agent to file
    agent.to_file("researcher.yaml")
    print("Created agent: researcher.yaml")
    
    # Create agent via client
    client = MedallionClient()
    result = client.create_agent(agent.__dict__)
    print(f"Agent created: {result}")


def example_provider_usage():
    """Example of using providers directly"""
    print("\n=== Provider Usage Example ===")
    
    # Use Ollama provider
    ollama = OllamaProvider()
    try:
        result = ollama.generate("What is artificial intelligence?", "llama3.1")
        print(f"Ollama response: {result['text'][:100]}...")
    except Exception as e:
        print(f"Ollama not available: {e}")
    
    # Use OpenAI provider (if API key is set)
    try:
        openai = OpenAIProvider()
        result = openai.generate("What is machine learning?", "gpt-3.5-turbo")
        print(f"OpenAI response: {result['text'][:100]}...")
    except Exception as e:
        print(f"OpenAI not available: {e}")


def example_knowledge_graph_queries():
    """Example of knowledge graph queries"""
    print("\n=== Knowledge Graph Queries ===")
    
    kg = KnowledgeGraph()
    
    # Get statistics
    stats = kg.get_statistics()
    print(f"Knowledge graph statistics: {stats}")
    
    # Query agents
    agents = kg.get_agents()
    print(f"Found {len(agents)} agents")
    
    # Query claims
    claims = kg.get_claims()
    print(f"Found {len(claims)} claims")
    
    # Custom query
    result = kg.query("MATCH (n:Agent) RETURN n.name, n.type")
    print(f"Custom query result: {result}")


def example_research_workflow():
    """Example of the research and answer workflow"""
    print("\n=== Research and Answer Workflow ===")
    
    # Load the example workflow
    workflow = Workflow.from_file("examples/research_and_answer/workflow.yaml")
    
    print(f"Loaded workflow: {workflow.name}")
    print(f"Description: {workflow.description}")
    print(f"Agents: {workflow.agents}")
    print(f"Steps: {len(workflow.steps)}")
    
    # Validate the workflow
    errors = workflow.validate()
    if errors:
        print(f"Workflow validation errors: {errors}")
    else:
        print("Workflow is valid!")
    
    # Run the workflow
    client = MedallionClient()
    result = client.run_workflow(
        "examples/research_and_answer/workflow.yaml",
        {"question": "What are the benefits of using Python for AI development?"}
    )
    print(f"Research workflow started: {result}")


if __name__ == "__main__":
    """Run all examples"""
    print("Medallion Python Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_workflow_creation()
        example_agent_creation()
        example_provider_usage()
        example_knowledge_graph_queries()
        example_research_workflow()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
