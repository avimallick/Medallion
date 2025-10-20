"""
Agent management for Medallion
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import yaml


@dataclass
class ModelConfig:
    """Model configuration for an agent"""
    provider: str
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@dataclass
class Agent:
    """Represents a Medallion agent"""
    name: str
    type: str
    description: str
    model: ModelConfig
    prompts: Dict[str, str]
    tools: Optional[List[str]] = None
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'Agent':
        """Create an agent from YAML content"""
        data = yaml.safe_load(yaml_content)
        
        model_data = data['model']
        model = ModelConfig(
            provider=model_data['provider'],
            model=model_data['model'],
            temperature=model_data.get('temperature'),
            max_tokens=model_data.get('max_tokens')
        )
        
        return cls(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            model=model,
            prompts=data['prompts'],
            tools=data.get('tools', [])
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Agent':
        """Create an agent from a YAML file"""
        with open(file_path, 'r') as f:
            return cls.from_yaml(f.read())
    
    def to_yaml(self) -> str:
        """Convert agent to YAML string"""
        data = {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'model': asdict(self.model),
            'prompts': self.prompts,
        }
        
        if self.tools:
            data['tools'] = self.tools
        
        return yaml.dump(data, default_flow_style=False)
    
    def to_file(self, file_path: str):
        """Save agent to a YAML file"""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    def get_system_prompt(self) -> Optional[str]:
        """Get the system prompt"""
        return self.prompts.get('system')
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt"""
        self.prompts['system'] = prompt
    
    def add_tool(self, tool: str):
        """Add a tool to the agent"""
        if not self.tools:
            self.tools = []
        if tool not in self.tools:
            self.tools.append(tool)
    
    def remove_tool(self, tool: str):
        """Remove a tool from the agent"""
        if self.tools and tool in self.tools:
            self.tools.remove(tool)
