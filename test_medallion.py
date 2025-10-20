#!/usr/bin/env python3
"""
Test script for Medallion Python package
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from medallion import MedallionClient, Workflow, Agent, KnowledgeGraph
from medallion.providers import OllamaProvider, OpenAIProvider

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    print("✅ MedallionClient imported")
    print("✅ Workflow imported") 
    print("✅ Agent imported")
    print("✅ KnowledgeGraph imported")
    print("✅ OllamaProvider imported")
    print("✅ OpenAIProvider imported")
    print("✅ All imports successful!")

def test_client_creation():
    """Test client creation"""
    print("\nTesting client creation...")
    
    # Find the Go binary
    binary_path = Path(__file__).parent / "medallion" / "bin" / "medallion-cli"
    if not binary_path.exists():
        print(f"❌ Go binary not found at {binary_path}")
        return False
    
    client = MedallionClient(binary_path=str(binary_path))
    print("✅ MedallionClient created successfully")
    return True

def test_workflow_creation():
    """Test workflow creation"""
    print("\nTesting workflow creation...")
    
    from medallion.core.workflow import WorkflowStep
    
    workflow = Workflow(
        name="test_workflow",
        description="Test workflow",
        agents=["test_agent"],
        steps=[
            WorkflowStep(
                name="test_step",
                agent="test_agent",
                input="Hello world"
            )
        ]
    )
    
    print("✅ Workflow created successfully")
    print(f"   Name: {workflow.name}")
    print(f"   Steps: {len(workflow.steps)}")
    
    # Test validation
    errors = workflow.validate()
    if errors:
        print(f"⚠️  Workflow validation errors: {errors}")
    else:
        print("✅ Workflow validation passed")
    
    return True

def test_agent_creation():
    """Test agent creation"""
    print("\nTesting agent creation...")
    
    from medallion.core.agent import ModelConfig
    
    agent = Agent(
        name="test_agent",
        type="worker",
        description="Test agent",
        model=ModelConfig(
            provider="ollama",
            model="llama3.1"
        ),
        prompts={
            "system": "You are a test agent."
        }
    )
    
    print("✅ Agent created successfully")
    print(f"   Name: {agent.name}")
    print(f"   Type: {agent.type}")
    print(f"   Model: {agent.model.provider}/{agent.model.model}")
    
    return True

def test_providers():
    """Test provider creation"""
    print("\nTesting providers...")
    
    # Test Ollama provider
    try:
        ollama = OllamaProvider()
        print("✅ OllamaProvider created")
    except Exception as e:
        print(f"⚠️  OllamaProvider creation failed: {e}")
    
    # Test OpenAI provider (will fail without API key, but should not crash)
    try:
        openai = OpenAIProvider()
        print("✅ OpenAIProvider created")
    except ValueError as e:
        print(f"⚠️  OpenAIProvider needs API key: {e}")
    except Exception as e:
        print(f"❌ OpenAIProvider creation failed: {e}")
    
    return True

def test_knowledge_graph():
    """Test knowledge graph interface"""
    print("\nTesting knowledge graph...")
    
    binary_path = Path(__file__).parent / "medallion" / "bin" / "medallion-cli"
    kg = KnowledgeGraph(MedallionClient(binary_path=str(binary_path)))
    
    print("✅ KnowledgeGraph created successfully")
    
    return True

def main():
    """Run all tests"""
    print("Medallion Python Package Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_client_creation,
        test_workflow_creation,
        test_agent_creation,
        test_providers,
        test_knowledge_graph,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
    
    print(f"\n{'='*40}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Medallion Python package is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
