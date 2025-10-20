"""
Core Medallion client that interfaces with the Go backend
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import time


class MedallionClient:
    """Main client for interacting with Medallion"""
    
    def __init__(self, config_file: Optional[str] = None, binary_path: Optional[str] = None):
        """Initialize the Medallion client
        
        Args:
            config_file: Path to configuration file
            binary_path: Path to the Go binary (defaults to bundled binary)
        """
        self.config_file = config_file
        self.binary_path = binary_path or self._find_binary()
        self.temp_dir = tempfile.mkdtemp(prefix="medallion_")
        
    def _find_binary(self) -> str:
        """Find the Medallion Go binary"""
        # Look for binary in package directory
        package_dir = Path(__file__).parent
        binary_path = package_dir / "bin" / "medallion-cli"
        
        if binary_path.exists():
            return str(binary_path)
        
        # Fallback to system PATH
        return "medallion-cli"
    
    def _run_command(self, args: List[str], input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Run a command against the Go binary"""
        cmd = [self.binary_path] + args
        
        if self.config_file:
            cmd.extend(["--config", self.config_file])
        
        try:
            result = subprocess.run(
                cmd,
                input=json.dumps(input_data) if input_data else None,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Command failed: {result.stderr}")
            
            # Try to parse JSON output, fallback to text
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout.strip()}
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Command timed out")
        except FileNotFoundError:
            raise RuntimeError(f"Medallion binary not found at {self.binary_path}")
    
    def build_project(self, template: str, app_name: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Build a new project scaffold
        
        Args:
            template: Template to use (1+4, research, chat)
            app_name: Name of the application
            output_dir: Output directory (defaults to app_name)
            
        Returns:
            Dictionary with build results
        """
        args = ["build", template, app_name]
        if output_dir:
            args.extend(["--output", output_dir])
        
        return self._run_command(args)
    
    def run_workflow(self, workflow_file: str, variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Run a workflow
        
        Args:
            workflow_file: Path to workflow YAML file
            variables: Variables to pass to the workflow
            
        Returns:
            Dictionary with run results
        """
        args = ["run", workflow_file]
        
        if variables:
            for key, value in variables.items():
                args.extend(["--var", f"{key}={value}"])
        
        return self._run_command(args)
    
    def query_knowledge_graph(self, query: str, format: str = "table") -> Dict[str, Any]:
        """Query the knowledge graph
        
        Args:
            query: Cypher-like query string
            format: Output format (table, json, csv)
            
        Returns:
            Dictionary with query results
        """
        args = ["kg", "query", query, "--format", format]
        return self._run_command(args)
    
    def inspect_knowledge_graph(self) -> Dict[str, Any]:
        """Inspect the knowledge graph schema and statistics
        
        Returns:
            Dictionary with schema information
        """
        args = ["kg", "inspect"]
        return self._run_command(args)
    
    def trace_run(self, run_id: str, format: str = "table", details: bool = False) -> Dict[str, Any]:
        """Get execution trace for a run
        
        Args:
            run_id: ID of the run to trace
            format: Output format (table, json)
            details: Show detailed span information
            
        Returns:
            Dictionary with trace information
        """
        args = ["trace", "--run-id", run_id, "--format", format]
        if details:
            args.append("--details")
        
        return self._run_command(args)
    
    def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            Dictionary with agent creation results
        """
        # Write agent config to temporary file
        agent_file = os.path.join(self.temp_dir, f"agent_{int(time.time())}.yaml")
        with open(agent_file, 'w') as f:
            json.dump(agent_config, f, indent=2)
        
        args = ["agent", "create", agent_file]
        return self._run_command(args)
    
    def list_agents(self) -> Dict[str, Any]:
        """List all agents
        
        Returns:
            Dictionary with list of agents
        """
        args = ["agent", "list"]
        return self._run_command(args)
    
    def close(self):
        """Clean up temporary resources"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience functions
def build_project(template: str, app_name: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Build a project using a temporary client"""
    with MedallionClient() as client:
        return client.build_project(template, app_name, output_dir)


def run_workflow(workflow_file: str, variables: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Run a workflow using a temporary client"""
    with MedallionClient() as client:
        return client.run_workflow(workflow_file, variables)


def query_knowledge_graph(query: str, format: str = "table") -> Dict[str, Any]:
    """Query the knowledge graph using a temporary client"""
    with MedallionClient() as client:
        return client.query_knowledge_graph(query, format)
