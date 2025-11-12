# Design Document

## Overview

The custom AgentCore application will be built as a modular, configurable AI agent system following the Amazon Bedrock AgentCore framework. The design leverages the proven agentcore_template structure while providing flexibility for domain-specific customization. The application consists of five main components: the Agent Runtime, Gateway integration, Memory system, Authentication layer, and Streamlit UI.

## Architecture

The application follows a microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│  Agent Runtime  │────│   AgentCore     │
│                 │    │                 │    │   Gateway       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cognito Auth  │    │  AgentCore      │    │  External APIs  │
│                 │    │  Memory         │    │  & Tools        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **Agent Runtime**: The main execution environment using Strands framework
2. **Gateway Integration**: MCP client for external tool access
3. **Memory System**: Persistent conversation context and user preferences
4. **Authentication**: Cognito-based OAuth or IAM authentication
5. **User Interface**: Streamlit-based web application

## Components and Interfaces

### 1. Project Structure Generator

**Purpose**: Creates the initial project structure based on the agentcore_template

**Key Files**:
- `main.py`: AgentCore application entrypoint
- `app.py` / `app_oauth.py`: Streamlit UI applications
- `agent/agent_config/`: Agent configuration and tools
- `scripts/`: Deployment and management scripts
- `dev-requirements.txt`: Python dependencies

**Interface**: Command-line tool that accepts project name and configuration options

### 2. Agent Configuration System

**Purpose**: Manages agent behavior, tools, and system prompts

**Components**:
- `agent.py`: Core agent class with Strands integration
- `tools/`: Custom tool implementations
- `context.py`: Application context management
- `memory_hook_provider.py`: Memory integration hooks

**Interface**: Configuration files and Python classes for customization

### 3. Deployment Scripts

**Purpose**: Automates AWS infrastructure setup and configuration

**Scripts**:
- `prereq.sh`: Initial infrastructure setup
- `agentcore_gateway.py`: Gateway deployment
- `cognito_credentials_provider.py`: Authentication setup
- `agentcore_memory.py`: Memory system deployment
- `cleanup.sh`: Resource cleanup

**Interface**: Command-line scripts with parameter support

### 4. Streamlit User Interface

**Purpose**: Provides web-based chat interface for agent interaction

**Features**:
- Agent selection and version management
- Session management with unique IDs
- Real-time streaming responses
- Authentication integration (OAuth/IAM)
- Response formatting and display options

**Interface**: Web application accessible via browser

### 5. Tool Integration Framework

**Purpose**: Enables custom tool development and external API integration

**Components**:
- MCP client for gateway communication
- Strands tool decorators for custom functions
- Sample tools as implementation examples
- Bearer token authentication for secure access

**Interface**: Python decorators and classes for tool development

## Data Models

### Agent Configuration Model

```python
@dataclass
class AgentConfig:
    name: str
    model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    system_prompt: str = ""
    tools: List[callable] = field(default_factory=list)
    gateway_url: str = ""
    memory_enabled: bool = True
    auth_mode: str = "oauth"  # "oauth" or "iam"
```

### Tool Definition Model

```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    function: callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
```

### Session Model

```python
@dataclass
class SessionContext:
    session_id: str
    user_id: str
    agent_arn: str
    created_at: datetime
    last_activity: datetime
    conversation_history: List[Dict] = field(default_factory=list)
```

### Deployment Configuration Model

```python
@dataclass
class DeploymentConfig:
    project_name: str
    aws_region: str = "us-east-1"
    prefix: str = ""
    oauth_enabled: bool = True
    gateway_name: str = ""
    memory_name: str = ""
    cognito_provider_name: str = ""
```

## Error Handling

### Agent Runtime Errors

- **Connection Failures**: Graceful degradation when gateway is unavailable
- **Tool Execution Errors**: Proper error messages without exposing internal details
- **Authentication Failures**: Clear user feedback and retry mechanisms
- **Memory Access Errors**: Fallback to stateless operation

### Deployment Errors

- **AWS Permission Issues**: Clear error messages with required permissions
- **Resource Conflicts**: Detection and resolution of naming conflicts
- **Configuration Errors**: Validation and helpful error messages
- **Cleanup Failures**: Partial cleanup with manual intervention guidance

### UI Error Handling

- **Agent Selection Errors**: Fallback to manual ARN input
- **Streaming Failures**: Graceful fallback to non-streaming responses
- **Session Management**: Automatic session recovery and regeneration
- **Authentication Errors**: Clear login prompts and error messages

## Testing Strategy

### Unit Testing

- **Agent Configuration**: Test agent initialization and tool loading
- **Tool Functions**: Validate custom tool implementations
- **Deployment Scripts**: Mock AWS calls and test script logic
- **UI Components**: Test Streamlit component behavior

### Integration Testing

- **End-to-End Flows**: Complete user interaction scenarios
- **AWS Integration**: Test actual deployment and cleanup processes
- **Authentication Flows**: Validate OAuth and IAM authentication
- **Memory Persistence**: Test conversation context retention

### Performance Testing

- **Response Times**: Measure agent response latency
- **Concurrent Users**: Test multiple simultaneous sessions
- **Resource Usage**: Monitor AWS resource consumption
- **Streaming Performance**: Validate real-time response streaming

### Security Testing

- **Authentication**: Verify proper access controls
- **Token Management**: Test bearer token security
- **Input Validation**: Prevent injection attacks
- **Error Information**: Ensure no sensitive data leakage

## Configuration Management

### Environment Variables

- AWS credentials and region configuration
- AgentCore service endpoints
- Authentication provider settings
- Feature flags for optional components

### SSM Parameters

- Gateway URLs and authentication tokens
- Memory system configuration
- Cognito provider details
- Agent runtime settings

### Configuration Files

- `dev-requirements.txt`: Python dependencies
- `.agentcore.yaml`: AgentCore runtime configuration
- Environment-specific configuration overrides
- Tool-specific configuration files

## Deployment Architecture

### AWS Resources

1. **AgentCore Gateway**: Lambda functions for external tool access
2. **AgentCore Memory**: DynamoDB tables for conversation storage
3. **Cognito User Pool**: Authentication and user management
4. **IAM Roles**: Service permissions and access control
5. **SSM Parameters**: Configuration storage and retrieval

### Local Development

- Python virtual environment setup
- Local Streamlit development server
- Mock AWS services for testing
- Configuration validation tools

### Production Deployment

- Automated infrastructure provisioning
- Environment-specific configuration
- Monitoring and observability setup
- Backup and disaster recovery procedures