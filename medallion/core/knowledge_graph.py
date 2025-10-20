"""
Knowledge Graph interface for Medallion
"""

from typing import Dict, Any, List, Optional
from .client import MedallionClient


class KnowledgeGraph:
    """High-level interface to the Medallion knowledge graph"""
    
    def __init__(self, client: Optional[MedallionClient] = None):
        """Initialize the knowledge graph interface
        
        Args:
            client: Medallion client instance (creates new one if None)
        """
        self.client = client or MedallionClient()
    
    def query(self, query: str, format: str = "table") -> Dict[str, Any]:
        """Execute a Cypher-like query
        
        Args:
            query: Cypher-like query string
            format: Output format (table, json, csv)
            
        Returns:
            Query results
        """
        return self.client.query_knowledge_graph(query, format)
    
    def inspect(self) -> Dict[str, Any]:
        """Inspect the knowledge graph schema and statistics
        
        Returns:
            Schema and statistics information
        """
        return self.client.inspect_knowledge_graph()
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from the knowledge graph
        
        Returns:
            List of agent dictionaries
        """
        result = self.query("MATCH (n:Agent) RETURN n")
        return result.get('agents', [])
    
    def get_claims(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get claims from the knowledge graph
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of claim dictionaries
        """
        if agent_id:
            query = f"MATCH (n:Claim) WHERE n.agent_id = '{agent_id}' RETURN n"
        else:
            query = "MATCH (n:Claim) RETURN n"
        
        result = self.query(query)
        return result.get('claims', [])
    
    def get_runs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflow runs from the knowledge graph
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of run dictionaries
        """
        if status:
            query = f"MATCH (n:Run) WHERE n.status = '{status}' RETURN n"
        else:
            query = "MATCH (n:Run) RETURN n"
        
        result = self.query(query)
        return result.get('runs', [])
    
    def get_artifacts(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get artifacts from the knowledge graph
        
        Args:
            run_id: Optional run ID to filter by
            
        Returns:
            List of artifact dictionaries
        """
        if run_id:
            query = f"MATCH (n:Artifact) WHERE n.run_id = '{run_id}' RETURN n"
        else:
            query = "MATCH (n:Artifact) RETURN n"
        
        result = self.query(query)
        return result.get('artifacts', [])
    
    def get_statistics(self) -> Dict[str, int]:
        """Get basic statistics about the knowledge graph
        
        Returns:
            Dictionary with counts of different entity types
        """
        stats = {}
        
        # Count agents
        result = self.query("MATCH (n:Agent) RETURN COUNT(n) as count")
        stats['agents'] = result.get('count', 0)
        
        # Count claims
        result = self.query("MATCH (n:Claim) RETURN COUNT(n) as count")
        stats['claims'] = result.get('count', 0)
        
        # Count runs
        result = self.query("MATCH (n:Run) RETURN COUNT(n) as count")
        stats['runs'] = result.get('count', 0)
        
        # Count artifacts
        result = self.query("MATCH (n:Artifact) RETURN COUNT(n) as count")
        stats['artifacts'] = result.get('count', 0)
        
        return stats
