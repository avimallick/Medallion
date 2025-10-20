"""
Medallion - A Python-first agentic AI framework with Go backend

Medallion is a Python package that provides an agentic AI framework where a Knowledge Graph (KG) 
is the source of truth. It uses Go as the backend engine for performance while providing a 
clean Python API for easy integration.
"""

__version__ = "1.0.0"
__author__ = "Medallion Team"
__email__ = "team@medallion.ai"

from .core.client import MedallionClient
from .core.workflow import Workflow
from .core.agent import Agent
from .core.knowledge_graph import KnowledgeGraph
from .providers.ollama import OllamaProvider
from .providers.openai import OpenAIProvider

__all__ = [
    "MedallionClient",
    "Workflow", 
    "Agent",
    "KnowledgeGraph",
    "OllamaProvider",
    "OpenAIProvider",
]