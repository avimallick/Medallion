"""
Workflow management for Medallion
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import yaml


@dataclass
class WorkflowStep:
    """Represents a step in a workflow"""
    name: str
    agent: str
    input: str
    depends_on: Optional[List[str]] = None
    success_when: Optional[str] = None


@dataclass
class Workflow:
    """Represents a Medallion workflow"""
    name: str
    description: str
    agents: List[str]
    steps: List[WorkflowStep]
    variables: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'Workflow':
        """Create a workflow from YAML content"""
        data = yaml.safe_load(yaml_content)
        
        steps = []
        for step_data in data.get('steps', []):
            step = WorkflowStep(
                name=step_data['name'],
                agent=step_data['agent'],
                input=step_data['input'],
                depends_on=step_data.get('depends_on'),
                success_when=step_data.get('success_when')
            )
            steps.append(step)
        
        return cls(
            name=data['name'],
            description=data['description'],
            agents=data['agents'],
            steps=steps,
            variables=data.get('variables')
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Workflow':
        """Create a workflow from a YAML file"""
        with open(file_path, 'r') as f:
            return cls.from_yaml(f.read())
    
    def to_yaml(self) -> str:
        """Convert workflow to YAML string"""
        data = {
            'name': self.name,
            'description': self.description,
            'agents': self.agents,
            'steps': [asdict(step) for step in self.steps],
        }
        
        if self.variables:
            data['variables'] = self.variables
        
        return yaml.dump(data, default_flow_style=False)
    
    def to_file(self, file_path: str):
        """Save workflow to a YAML file"""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get a step by name"""
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def validate(self) -> List[str]:
        """Validate the workflow and return any errors"""
        errors = []
        
        # Check that all referenced agents exist
        for step in self.steps:
            if step.agent not in self.agents:
                errors.append(f"Step '{step.name}' references unknown agent '{step.agent}'")
        
        # Check dependencies
        step_names = {step.name for step in self.steps}
        for step in self.steps:
            if step.depends_on:
                for dep in step.depends_on:
                    if dep not in step_names:
                        errors.append(f"Step '{step.name}' depends on unknown step '{dep}'")
        
        return errors
