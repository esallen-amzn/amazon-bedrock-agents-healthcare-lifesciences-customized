#!/usr/bin/env python3
"""
Configuration Data Models for AgentCore Applications

This module defines the core configuration data models used throughout
the AgentCore application framework, including agent configuration,
tool definitions, session management, and deployment settings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
import json
import yaml
from pathlib import Path
import re


@dataclass
class AgentConfig:
    """Configuration for an AgentCore agent instance."""
    
    name: str
    model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)  # Tool names/identifiers
    gateway_url: str = ""
    memory_enabled: bool = True
    auth_mode: str = "oauth"  # "oauth" or "iam"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        
        if self.auth_mode not in ["oauth", "iam"]:
            raise ValueError("auth_mode must be 'oauth' or 'iam'")
        
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError("temperature must be between 0.0 and 1.0")
        
        if not (0.0 <= self.top_p <= 1.0):
            raise ValueError("top_p must be between 0.0 and 1.0")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'name': self.name,
            'model_id': self.model_id,
            'system_prompt': self.system_prompt,
            'tools': self.tools,
            'gateway_url': self.gateway_url,
            'memory_enabled': self.memory_enabled,
            'auth_mode': self.auth_mode,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create configuration from dictionary."""
        return cls(**data)


@dataclass
class ToolDefinition:
    """Definition of a custom tool for the agent."""
    
    name: str
    description: str
    function_name: str  # Name of the Python function
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    enabled: bool = True
    category: str = "custom"
    
    def __post_init__(self):
        """Validate tool definition after initialization."""
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        
        if not self.description:
            raise ValueError("Tool description cannot be empty")
        
        if not self.function_name:
            raise ValueError("Tool function_name cannot be empty")
        
        # Validate function name format
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.function_name):
            raise ValueError("function_name must be a valid Python identifier")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool definition to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'function_name': self.function_name,
            'parameters': self.parameters,
            'required_permissions': self.required_permissions,
            'enabled': self.enabled,
            'category': self.category,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolDefinition':
        """Create tool definition from dictionary."""
        return cls(**data)


@dataclass
class SessionContext:
    """Context information for a user session."""
    
    session_id: str
    user_id: str
    agent_arn: str
    created_at: datetime
    last_activity: datetime
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate session context after initialization."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        
        if not self.agent_arn:
            raise ValueError("agent_arn cannot be empty")
    
    def add_message(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """Add a message to the conversation history."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp.isoformat(),
        }
        
        self.conversation_history.append(message)
        self.last_activity = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session context to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'agent_arn': self.agent_arn,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'conversation_history': self.conversation_history,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """Create session context from dictionary."""
        # Convert ISO format strings back to datetime objects
        created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        last_activity = datetime.fromisoformat(data['last_activity'].replace('Z', '+00:00'))
        
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            agent_arn=data['agent_arn'],
            created_at=created_at,
            last_activity=last_activity,
            conversation_history=data.get('conversation_history', []),
            metadata=data.get('metadata', {}),
        )


@dataclass
class DeploymentConfig:
    """Configuration for AWS deployment settings."""
    
    project_name: str
    aws_region: str = "us-east-1"
    prefix: str = ""
    oauth_enabled: bool = True
    gateway_name: str = ""
    memory_name: str = ""
    cognito_provider_name: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate deployment configuration after initialization."""
        if not self.project_name:
            raise ValueError("project_name cannot be empty")
        
        # Validate AWS region format
        if not re.match(r'^[a-z]{2}-[a-z]+-\d+$', self.aws_region):
            raise ValueError("aws_region must be in format like 'us-east-1'")
        
        # Set default names if not provided
        if not self.prefix:
            self.prefix = self.project_name
        
        if not self.gateway_name:
            self.gateway_name = f"{self.prefix}-gateway"
        
        if not self.memory_name:
            self.memory_name = f"{self.prefix}-memory"
        
        if not self.cognito_provider_name:
            self.cognito_provider_name = f"{self.prefix}-auth"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deployment configuration to dictionary."""
        return {
            'project_name': self.project_name,
            'aws_region': self.aws_region,
            'prefix': self.prefix,
            'oauth_enabled': self.oauth_enabled,
            'gateway_name': self.gateway_name,
            'memory_name': self.memory_name,
            'cognito_provider_name': self.cognito_provider_name,
            'tags': self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeploymentConfig':
        """Create deployment configuration from dictionary."""
        return cls(**data)


@dataclass
class ProjectConfig:
    """Complete project configuration combining all components."""
    
    agent: AgentConfig
    deployment: DeploymentConfig
    tools: List[ToolDefinition] = field(default_factory=list)
    version: str = "1.0.0"
    description: str = ""
    
    def __post_init__(self):
        """Validate project configuration after initialization."""
        if not isinstance(self.agent, AgentConfig):
            raise ValueError("agent must be an AgentConfig instance")
        
        if not isinstance(self.deployment, DeploymentConfig):
            raise ValueError("deployment must be a DeploymentConfig instance")
        
        # Validate tools list
        for tool in self.tools:
            if not isinstance(tool, ToolDefinition):
                raise ValueError("All tools must be ToolDefinition instances")
    
    def add_tool(self, tool: ToolDefinition):
        """Add a tool to the configuration."""
        if not isinstance(tool, ToolDefinition):
            raise ValueError("tool must be a ToolDefinition instance")
        
        # Check for duplicate tool names
        existing_names = [t.name for t in self.tools]
        if tool.name in existing_names:
            raise ValueError(f"Tool with name '{tool.name}' already exists")
        
        self.tools.append(tool)
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool by name. Returns True if removed, False if not found."""
        for i, tool in enumerate(self.tools):
            if tool.name == tool_name:
                del self.tools[i]
                return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project configuration to dictionary."""
        return {
            'version': self.version,
            'description': self.description,
            'agent': self.agent.to_dict(),
            'deployment': self.deployment.to_dict(),
            'tools': [tool.to_dict() for tool in self.tools],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create project configuration from dictionary."""
        agent = AgentConfig.from_dict(data['agent'])
        deployment = DeploymentConfig.from_dict(data['deployment'])
        tools = [ToolDefinition.from_dict(tool_data) for tool_data in data.get('tools', [])]
        
        return cls(
            agent=agent,
            deployment=deployment,
            tools=tools,
            version=data.get('version', '1.0.0'),
            description=data.get('description', ''),
        )


class ConfigurationManager:
    """Manages loading and saving of configuration files."""
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> ProjectConfig:
        """
        Load configuration from a file (JSON or YAML).
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            ProjectConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return ProjectConfig.from_dict(data)
    
    @staticmethod
    def save_to_file(config: ProjectConfig, file_path: Union[str, Path], format: str = 'yaml'):
        """
        Save configuration to a file.
        
        Args:
            config: ProjectConfig instance to save
            file_path: Path where to save the file
            format: File format ('yaml' or 'json')
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = config.to_dict()
        
        with open(path, 'w', encoding='utf-8') as f:
            if format.lower() == 'yaml':
                yaml.dump(data, f, default_flow_style=False, indent=2, sort_keys=False)
            elif format.lower() == 'json':
                json.dump(data, f, indent=2, sort_keys=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def create_default_config(project_name: str, **kwargs) -> ProjectConfig:
        """
        Create a default configuration for a new project.
        
        Args:
            project_name: Name of the project
            **kwargs: Additional configuration options
            
        Returns:
            ProjectConfig with default settings
        """
        agent_config = AgentConfig(
            name=project_name,
            model_id=kwargs.get('model_id', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'),
            system_prompt=kwargs.get('system_prompt', ''),
            auth_mode=kwargs.get('auth_mode', 'oauth'),
            memory_enabled=kwargs.get('memory_enabled', True),
        )
        
        deployment_config = DeploymentConfig(
            project_name=project_name,
            aws_region=kwargs.get('aws_region', 'us-east-1'),
            oauth_enabled=kwargs.get('oauth_enabled', True),
        )
        
        return ProjectConfig(
            agent=agent_config,
            deployment=deployment_config,
            version=kwargs.get('version', '1.0.0'),
            description=kwargs.get('description', f'Custom AgentCore application: {project_name}'),
        )


# Example usage and validation functions
def validate_configuration(config: ProjectConfig) -> List[str]:
    """
    Validate a complete project configuration.
    
    Args:
        config: ProjectConfig to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    try:
        # Validate agent configuration
        if not config.agent.name:
            errors.append("Agent name is required")
        
        if not config.agent.model_id:
            errors.append("Agent model_id is required")
        
        # Validate deployment configuration
        if not config.deployment.project_name:
            errors.append("Deployment project_name is required")
        
        # Validate tools
        tool_names = set()
        for i, tool in enumerate(config.tools):
            if tool.name in tool_names:
                errors.append(f"Duplicate tool name: {tool.name}")
            tool_names.add(tool.name)
            
            if not tool.function_name:
                errors.append(f"Tool {tool.name} missing function_name")
    
    except Exception as e:
        errors.append(f"Configuration validation error: {str(e)}")
    
    return errors


if __name__ == '__main__':
    # Example usage
    print("Creating example configuration...")
    
    # Create a sample configuration
    config = ConfigurationManager.create_default_config(
        project_name="healthcare-agent",
        description="A healthcare AI agent for medical research",
        auth_mode="oauth",
        aws_region="us-east-1"
    )
    
    # Add a sample tool
    sample_tool = ToolDefinition(
        name="medical_search",
        description="Search medical literature and databases",
        function_name="search_medical_literature",
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "database": {"type": "string", "description": "Database to search"}
        },
        category="medical"
    )
    
    config.add_tool(sample_tool)
    
    # Validate configuration
    errors = validate_configuration(config)
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid!")
    
    # Save to file
    ConfigurationManager.save_to_file(config, "example_config.yaml")
    print("📁 Configuration saved to example_config.yaml")
    
    # Load from file
    loaded_config = ConfigurationManager.load_from_file("example_config.yaml")
    print("📖 Configuration loaded successfully!")
    
    print(f"Project: {loaded_config.agent.name}")
    print(f"Tools: {len(loaded_config.tools)}")
    print(f"Region: {loaded_config.deployment.aws_region}")