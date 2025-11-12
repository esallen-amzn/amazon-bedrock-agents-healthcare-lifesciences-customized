# AgentCore Technology Stack & Build System

## Core Technologies

### Amazon Bedrock AgentCore Services
- **AgentCore Runtime**: Managed execution environment for agents with auto-scaling
- **AgentCore Gateway**: Tool integration service supporting Lambda functions and external APIs
- **AgentCore Memory**: Persistent storage for conversations and context
- **AgentCore Identity**: OAuth2 credential management and authentication

### Development Framework
- **Strands**: Multi-agent collaboration framework with tool orchestration
- **Python 3.10+**: Primary development language for agents and tools
- **Streamlit**: Local development UI with OAuth integration
- **MCP (Model Context Protocol)**: Tool integration and communication protocol

### AWS Infrastructure
- **AWS Lambda**: Tool implementations and gateway targets
- **Amazon Cognito**: User pools and OAuth2 authentication
- **AWS Systems Manager**: Parameter storage for configuration
- **Amazon CloudWatch**: Observability, logging, and transaction search
- **AWS Secrets Manager**: Secure credential storage

## Project Structure

### Standard AgentCore Project Layout
```
project-name/
├── agent/                          # Agent configuration and logic
│   ├── agent_config/
│   │   ├── tools/                  # Local tool implementations
│   │   ├── agent.py               # Main agent class
│   │   ├── agent_task.py          # Task orchestration
│   │   └── memory_hook_provider.py # Memory integration
│   └── requirements.txt           # Agent dependencies
├── app_modules/                    # Streamlit UI components (OAuth)
│   ├── auth.py                    # Authentication handling
│   ├── chat.py                    # Chat interface
│   ├── main.py                    # Main UI application
│   └── utils.py                   # UI utilities
├── prerequisite/                   # Infrastructure components
│   ├── lambda/                    # Gateway Lambda functions
│   ├── infrastructure.yaml        # Core infrastructure template
│   ├── cognito.yaml              # Authentication infrastructure
│   └── knowledge_base.py         # Knowledge base setup
├── scripts/                       # Deployment automation
│   ├── prereq.sh                 # Infrastructure deployment
│   ├── agentcore_gateway.py      # Gateway management
│   ├── agentcore_memory.py       # Memory management
│   └── cognito_credentials_provider.py # Auth setup
├── tests/                         # Integration tests
│   ├── test_agent.py             # Agent testing
│   ├── test_gateway.py           # Gateway testing
│   └── test_memory.py            # Memory testing
├── static/                        # UI assets and images
├── app.py                         # Basic Streamlit app (IAM auth)
├── app_oauth.py                   # OAuth Streamlit app
├── main.py                        # AgentCore runtime entry point
└── dev-requirements.txt           # Development dependencies
```

## Agent Implementation Patterns

### Agent Class Structure
```python
class TemplateAgent:
    def __init__(self, bearer_token: str, memory_hook: MemoryHook, 
                 bedrock_model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
        self.model = BedrockModel(model_id=bedrock_model_id)
        self.gateway_client = MCPClient(...)
        self.tools = [retrieve, current_time] + self.gateway_client.list_tools_sync()
        self.agent = Agent(model=self.model, system_prompt=self.system_prompt, 
                          tools=self.tools, hooks=[memory_hook])
    
    async def stream(self, user_query: str):
        async for event in self.agent.stream_async(user_query):
            yield event["data"]
```

### Tool Implementation (Strands)
```python
from strands import tool

@tool(name="analyze_data", description="Analyze data using custom logic")
def analyze_data(data: str, analysis_type: str = "basic") -> Dict[str, Any]:
    # Tool implementation
    return {"result": "analysis_complete", "data": processed_data}
```

### Lambda Gateway Functions
```python
def lambda_handler(event, context):
    # Extract MCP parameters
    method = event.get('method')
    params = event.get('params', {})
    
    # Execute tool logic
    result = execute_tool_function(params)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

## Deployment Commands

### Infrastructure Setup
```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 2. Install dependencies
uv pip install -r dev-requirements.txt

# 3. Deploy infrastructure (with prefix)
chmod +x scripts/prereq.sh
./scripts/prereq.sh myapp

# 4. List SSM parameters
./scripts/list_ssm_parameters.sh
```

### AgentCore Component Setup
```bash
# 1. Create Gateway
python scripts/agentcore_gateway.py create --name myapp-gw

# 2. Setup Identity/Authentication
python scripts/cognito_credentials_provider.py create --name myapp-cp

# 3. Create Memory
python scripts/agentcore_memory.py create --name myapp

# 4. Test components
python tests/test_gateway.py --prompt "Hello, can you help me?"
python tests/test_memory.py load-conversation
```

### Agent Runtime Deployment
```bash
# Configure agent runtime
agentcore configure --entrypoint main.py \
  -rf agent/requirements.txt \
  -er arn:aws:iam::<Account-Id>:role/<Role> \
  --name myapp<AgentName>

# Deploy agent
rm .agentcore.yaml  # Clean previous config
agentcore launch

# Test deployment
agentcore invoke '{"prompt": "Hello"}'  # IAM auth
python tests/test_agent.py myapp<AgentName> -p "Hi"  # OAuth auth
```

### Local Development
```bash
# Basic Streamlit app (IAM authentication)
streamlit run app.py --server.port 8501

# OAuth Streamlit app (OAuth authentication)
streamlit run app_oauth.py --server.port 8501 -- --agent=myapp<AgentName>
```

## Configuration Management

### SSM Parameter Patterns
- `/app/{prefix}/agentcore/gateway_url` - Gateway endpoint URL
- `/app/{prefix}/agentcore/runtime_iam_role` - Runtime IAM role ARN
- `/app/{prefix}/agentcore/cognito_discovery_url` - OAuth discovery URL
- `/app/{prefix}/agentcore/web_client_id` - OAuth client ID
- `/app/{prefix}/knowledge_base/knowledge_base_id` - Knowledge base ID

### Environment Variables
```python
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "true"
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"
os.environ["KNOWLEDGE_BASE_ID"] = get_ssm_parameter("/app/myapp/knowledge_base/knowledge_base_id")
```

## Security & Authentication

### OAuth2 Flow
- **M2M Authentication**: Gateway uses machine-to-machine authentication
- **User Authentication**: Streamlit UI supports OAuth2 user authentication
- **Token Management**: Automatic token refresh and credential management
- **Fine-grained Access**: Resource-specific permissions via IAM roles

### IAM Role Patterns
- **Runtime Role**: Permissions for agent execution, model invocation, memory access
- **Gateway Role**: Permissions for Lambda invocation and tool execution
- **Lambda Role**: Minimal permissions for specific tool functionality

## Observability & Monitoring

### Built-in Observability
- **Transaction Search**: CloudWatch transaction tracking for agent interactions
- **Metrics**: Custom CloudWatch metrics for agent performance
- **Logging**: Structured logging with correlation IDs
- **Tracing**: X-Ray integration for distributed tracing

### Monitoring Setup
```bash
# Enable CloudWatch Transaction Search
# https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html

# View AgentCore Observability Dashboard
# https://aws.amazon.com/blogs/machine-learning/build-trustworthy-ai-agents-with-amazon-bedrock-agentcore-observability/
```

## Cleanup Commands

```bash
# Cleanup all resources
chmod +x scripts/cleanup.sh
./scripts/cleanup.sh

# Individual component cleanup
python scripts/cognito_credentials_provider.py delete
python scripts/agentcore_memory.py delete
python scripts/agentcore_gateway.py delete
python scripts/agentcore_agent_runtime.py myapp<AgentName>

# Clean configuration files
rm .agentcore.yaml
rm .bedrock_agentcore.yaml
```