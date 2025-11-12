# AgentCore Product Overview

## Amazon Bedrock AgentCore with Strands Framework

A modern template for creating AI agents using Amazon Bedrock AgentCore framework with Strands. This approach provides enhanced capabilities for building agents with memory, observability, gateway integration, and local development tools.

### Core Components

- **AgentCore Runtime**: Managed agent execution environment with built-in observability and scaling
- **AgentCore Gateway**: Tool integration layer supporting Lambda functions and external APIs
- **AgentCore Memory**: Persistent conversation and context storage across sessions
- **Cognito Identity**: OAuth2 authentication and user management
- **Strands Framework**: Multi-agent collaboration and tool orchestration
- **Streamlit UI**: Local development interface with OAuth integration

### Key Advantages Over Traditional Bedrock Agents

- **Enhanced Memory**: Persistent context and conversation history
- **Better Observability**: Built-in CloudWatch integration and transaction search
- **Flexible Authentication**: OAuth2 and IAM authentication options
- **Local Development**: Streamlit UI for rapid prototyping and testing
- **Tool Gateway**: Centralized tool management with Lambda integration
- **Multi-Agent Support**: Native support for agent collaboration via Strands

### Target Use Cases

- **Healthcare Applications**: Specialized medical analysis with persistent context
- **Research Workflows**: Multi-step analysis with memory and tool chaining
- **Customer Service**: Conversational agents with session persistence
- **Data Analysis**: Complex analytical workflows requiring tool integration
- **Collaborative AI**: Multi-agent systems working together on complex tasks

### Deployment Model

- **Infrastructure as Code**: CloudFormation templates for all components
- **Modular Architecture**: Separate gateway, memory, identity, and runtime components
- **Scalable**: Managed runtime with automatic scaling and load balancing
- **Secure**: OAuth2 authentication with fine-grained access control
- **Observable**: Built-in monitoring, logging, and transaction tracking

This framework represents the next generation of AI agent development, providing enterprise-grade capabilities for complex, stateful AI applications in healthcare and life sciences.