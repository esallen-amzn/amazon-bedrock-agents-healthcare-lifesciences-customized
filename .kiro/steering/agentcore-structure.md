# AgentCore Project Organization & Structure

## Repository Layout for AgentCore Projects

### Standard AgentCore Project Structure
```
project-name/
├── agent/                          # Core agent implementation
│   ├── agent_config/
│   │   ├── tools/                  # Local Strands tools
│   │   │   ├── __init__.py
│   │   │   └── sample_tools.py     # Example tool implementations
│   │   ├── __init__.py
│   │   ├── agent.py               # Main agent class with Strands integration
│   │   ├── agent_task.py          # Task orchestration and execution
│   │   ├── access_token.py        # Gateway authentication
│   │   ├── context.py             # Shared context management
│   │   ├── memory_hook_provider.py # Memory integration hooks
│   │   ├── streaming_queue.py     # Response streaming management
│   │   └── utils.py               # Utility functions
│   └── requirements.txt           # Agent-specific dependencies
├── app_modules/                    # Streamlit UI components (OAuth version)
│   ├── __init__.py
│   ├── auth.py                    # OAuth authentication handling
│   ├── chat.py                    # Chat interface components
│   ├── main.py                    # Main OAuth UI application
│   ├── styles.py                  # UI styling and themes
│   └── utils.py                   # UI utility functions
├── prerequisite/                   # Infrastructure and setup
│   ├── docs-rag/                  # Knowledge base documents
│   ├── lambda/                    # Gateway Lambda functions
│   │   └── python/                # Lambda source code
│   │       ├── lambda_function.py # Main Lambda handler
│   │       └── requirements.txt   # Lambda dependencies
│   ├── __init__.py
│   ├── cognito.yaml              # Cognito/OAuth infrastructure
│   ├── infrastructure.yaml        # Core AWS infrastructure
│   ├── knowledge_base.py         # Knowledge base setup script
│   └── prereqs_config.yaml       # Configuration for prerequisites
├── scripts/                       # Deployment and management scripts
│   ├── __init__.py
│   ├── agentcore_agent_runtime.py # Agent runtime management
│   ├── agentcore_gateway.py      # Gateway creation and management
│   ├── agentcore_memory.py       # Memory service management
│   ├── cleanup.sh                # Resource cleanup script
│   ├── cognito_credentials_provider.py # OAuth setup
│   ├── list_ssm_parameters.sh    # Parameter discovery
│   ├── prereq.sh                 # Infrastructure deployment
│   └── utils.py                  # Script utilities
├── static/                        # UI assets and resources
│   ├── agentcore-service-icon.png
│   ├── gen-ai-dark.svg           # AI assistant avatar
│   ├── user-profile.svg          # User avatar
│   └── [fonts and other assets]
├── tests/                         # Integration and component tests
│   ├── __init__.py
│   ├── test_agent.py             # Agent functionality tests
│   ├── test_gateway.py           # Gateway integration tests
│   └── test_memory.py            # Memory service tests
├── app.py                         # Basic Streamlit app (IAM auth)
├── app_oauth.py                   # OAuth Streamlit app entry point
├── dev-requirements.txt           # Development dependencies
├── main.py                        # AgentCore runtime entry point
├── README.md                      # Project documentation
└── [optional: .agentcore.yaml]    # Runtime configuration (generated)
```

## Naming Conventions

### Project and Resource Naming
- **Project Names**: Use kebab-case for project directories (e.g., `medical-diagnosis-assistant`)
- **Resource Prefix**: Use consistent prefix across all AWS resources (e.g., `myapp`, `medassist`)
- **Agent Names**: Combine prefix with descriptive name (e.g., `myapp-diagnosis-agent`)

### File and Directory Conventions
- **Python Modules**: Use snake_case for Python files and modules
- **Configuration Files**: Use kebab-case for YAML/JSON config files
- **Scripts**: Use kebab-case with `.sh` extension for shell scripts
- **Static Assets**: Use kebab-case for asset files

### AWS Resource Naming
- **SSM Parameters**: `/app/{prefix}/agentcore/{component}/{parameter}`
- **CloudFormation Stacks**: `{Prefix}Stack{Component}` (e.g., `MyAppStackInfra`)
- **Lambda Functions**: `{Prefix}{Component}Lambda` (e.g., `MyAppGatewayLambda`)
- **IAM Roles**: `{Component}AgentCoreRole` (e.g., `RuntimeAgentCoreRole`)

## Component Architecture

### Agent Implementation Layer
```
agent/agent_config/
├── agent.py                       # Main TemplateAgent class
│   ├── __init__(bearer_token, memory_hook, model_id, system_prompt, tools)
│   ├── invoke(user_query) -> str
│   └── stream(user_query) -> AsyncIterator[str]
├── agent_task.py                  # Task orchestration
│   └── agent_task(user_message, session_id, actor_id)
├── tools/                         # Local Strands tools
│   └── sample_tools.py           # @tool decorated functions
└── [context, memory, streaming management]
```

### Infrastructure Layer
```
prerequisite/
├── infrastructure.yaml            # Core AWS resources
│   ├── RuntimeAgentCoreRole      # Agent execution permissions
│   ├── GatewayAgentCoreRole      # Gateway permissions
│   ├── MyAppLambda               # Gateway target function
│   └── SSM Parameters            # Configuration storage
├── cognito.yaml                  # OAuth2 authentication
│   ├── UserPool                  # User management
│   ├── ResourceServer            # OAuth2 scopes
│   └── UserPoolClient            # Application client
└── lambda/python/                # Gateway Lambda implementation
    ├── lambda_function.py        # MCP-compatible handler
    └── requirements.txt          # Lambda dependencies
```

### UI Layer
```
app_modules/                       # OAuth-enabled UI
├── main.py                       # Main Streamlit application
├── auth.py                       # OAuth2 authentication flow
├── chat.py                       # Chat interface components
└── utils.py                      # UI utilities

app.py                            # Basic UI (IAM authentication)
app_oauth.py                      # OAuth UI entry point
```

## Development Patterns

### Tool Development (Strands Pattern)
```python
from strands import tool
from typing import Dict, Any, List

@tool(
    name="analyze_medical_data",
    description="Analyze medical data using specialized algorithms"
)
def analyze_medical_data(
    data: str,
    analysis_type: str = "basic",
    include_confidence: bool = True
) -> Dict[str, Any]:
    """
    Analyze medical data and return structured results.
    
    Args:
        data: Raw medical data to analyze
        analysis_type: Type of analysis to perform
        include_confidence: Whether to include confidence scores
    
    Returns:
        Dictionary containing analysis results
    """
    # Implementation logic
    return {
        "status": "completed",
        "results": analysis_results,
        "confidence": confidence_score if include_confidence else None
    }
```

### Agent Configuration Pattern
```python
class MedicalDiagnosisAgent(TemplateAgent):
    def __init__(self, bearer_token: str, memory_hook: MemoryHook):
        super().__init__(
            bearer_token=bearer_token,
            memory_hook=memory_hook,
            bedrock_model_id="us.amazon.nova-pro-v1:0",
            system_prompt=self._get_medical_system_prompt(),
            tools=[medical_analysis_tool, diagnosis_tool]
        )
    
    def _get_medical_system_prompt(self) -> str:
        return """You are a medical diagnosis assistant specialized in..."""
```

### Lambda Gateway Pattern
```python
import json
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """MCP-compatible Lambda handler for AgentCore Gateway"""
    try:
        # Extract MCP method and parameters
        method = event.get('method')
        params = event.get('params', {})
        
        # Route to appropriate tool function
        if method == 'tools/call':
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            
            # Execute tool logic
            result = execute_tool(tool_name, tool_args)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'content': [{'type': 'text', 'text': json.dumps(result)}]
                })
            }
        
        return {'statusCode': 400, 'body': 'Invalid method'}
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

## Configuration Management

### SSM Parameter Organization
```
/app/{prefix}/agentcore/
├── gateway_url                    # Gateway MCP endpoint
├── gateway_iam_role              # Gateway IAM role ARN
├── runtime_iam_role              # Runtime IAM role ARN
├── cognito_discovery_url         # OAuth2 discovery endpoint
├── web_client_id                 # OAuth2 client ID
└── lambda_arn                    # Gateway Lambda function ARN

/app/{prefix}/knowledge_base/
├── knowledge_base_id             # Bedrock Knowledge Base ID
└── data_source_id                # Knowledge Base data source ID
```

### Environment-Specific Configuration
- **Development**: Local Streamlit with IAM authentication
- **Testing**: OAuth integration with test user pools
- **Production**: Full OAuth2 flow with production credentials

## Deployment Workflow

### Standard Deployment Sequence
1. **Infrastructure Setup**: Deploy CloudFormation templates
2. **Gateway Creation**: Create AgentCore Gateway with Lambda targets
3. **Identity Setup**: Configure Cognito OAuth2 authentication
4. **Memory Creation**: Set up AgentCore Memory service
5. **Agent Runtime**: Deploy and configure agent runtime
6. **UI Deployment**: Launch Streamlit interface

### Resource Dependencies
```
Infrastructure (CloudFormation)
    ↓
Gateway (AgentCore Gateway)
    ↓
Identity (Cognito OAuth2)
    ↓
Memory (AgentCore Memory)
    ↓
Runtime (AgentCore Agent)
    ↓
UI (Streamlit Application)
```

## Testing Patterns

### Component Testing
```python
# Test gateway integration
python tests/test_gateway.py --prompt "Hello, can you help me?"

# Test memory functionality
python tests/test_memory.py load-conversation
python tests/test_memory.py load-prompt "My preferred response format"
python tests/test_memory.py list-memory

# Test agent runtime
python tests/test_agent.py myapp-agent -p "Test query"
```

### Integration Testing
- **End-to-end**: Full workflow from UI to agent response
- **Component**: Individual service testing (gateway, memory, runtime)
- **Authentication**: OAuth2 flow and token management
- **Tool Integration**: Lambda function and MCP protocol testing

## Best Practices

### Code Organization
- Keep agent logic separate from infrastructure code
- Use consistent naming conventions across all components
- Implement proper error handling and logging
- Follow Strands patterns for tool development

### Security
- Use least-privilege IAM roles for all components
- Implement proper OAuth2 scopes and permissions
- Store sensitive configuration in SSM Parameter Store
- Enable CloudWatch logging and monitoring

### Scalability
- Design tools to be stateless and idempotent
- Use AgentCore's built-in scaling capabilities
- Implement proper resource cleanup and management
- Monitor performance and adjust configurations as needed