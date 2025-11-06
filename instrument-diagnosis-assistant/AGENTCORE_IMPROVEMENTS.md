# AgentCore Alignment Improvements

## Overview

This document captures potential improvements to better align the Instrument Diagnosis Assistant with AgentCore best practices and patterns. These are recommendations for future enhancement, not immediate requirements.

**Status**: Recommendations for future implementation  
**Priority**: Enhancement/Optimization  
**Current State**: Project is functional and well-aligned with AgentCore patterns

## Current Alignment Assessment

### ✅ **Strong Alignment Areas**
- **Project Structure**: Follows standard AgentCore layout perfectly
- **Tool Implementation**: Uses proper Strands `@tool` decorators
- **Infrastructure**: Correct CloudFormation templates and deployment scripts
- **UI Components**: Both basic and OAuth Streamlit applications present
- **Configuration Management**: Proper SSM parameters and configuration patterns

### ⚠️ **Areas for Future Enhancement**

## 1. Lambda Gateway Implementation

**Current State**: Basic Lambda function with simple echo functionality  
**Improvement Opportunity**: Implement full MCP-compatible handler

### Current Implementation
```python
def lambda_handler(event, context):
    extended_tool_name = context.client_context.custom["bedrockAgentCoreToolName"]
    resource = extended_tool_name.split("___")[1]
    # Simple echo function only
```

### Recommended Enhancement
```python
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
            
            # Route to diagnosis tools
            if tool_name == 'analyze_logs':
                result = analyze_logs_lambda(**tool_args)
            elif tool_name == 'process_large_files':
                result = process_large_files_lambda(**tool_args)
            elif tool_name == 'multimodal_processing':
                result = process_multimodal_docs_lambda(**tool_args)
            
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

**Benefits**:
- Better scalability for heavy processing tasks
- Proper MCP protocol compliance
- Centralized tool management through gateway

## 2. Tool Distribution Strategy

**Current State**: All tools implemented as local Strands tools  
**Improvement Opportunity**: Strategic distribution between local and gateway tools

### Recommended Distribution

#### Local Tools (Keep in `agent/agent_config/tools/`)
- Configuration management tools
- Simple data processing and validation
- UI interaction helpers
- Quick diagnostic checks

#### Gateway Tools (Move to Lambda)
- `analyze_logs` - Heavy file processing operations
- `process_large_files` - Memory-intensive operations  
- `multimodal_processing_tools` - Nova Canvas integration
- `component_recognition_tools` - Complex NLP processing

**Benefits**:
- Better resource utilization
- Improved scalability for compute-intensive tasks
- Separation of concerns between quick local operations and heavy processing

## 3. Agent Class Specialization

**Current State**: Good implementation extending TemplateAgent  
**Enhancement Opportunity**: More specialized diagnosis-focused agent class

### Recommended Enhancement
```python
class InstrumentDiagnosisAgent(TemplateAgent):
    def __init__(self, bearer_token: str, memory_hook: MemoryHook, config_manager: ConfigManager = None):
        # Initialize configuration manager
        self.config_manager = config_manager or get_config_manager()
        self.config = self.config_manager.get_config()
        
        # Initialize with Nova models
        super().__init__(
            bearer_token=bearer_token,
            memory_hook=memory_hook,
            bedrock_model_id=self.config.models.text_model,
            system_prompt=self._get_diagnosis_system_prompt(),
            tools=self._get_specialized_tools()
        )
        
        # Add multimodal model for document processing
        self.multimodal_model = BedrockModel(
            model_id=self.config.models.multimodal_model,
            temperature=self.config.models.temperature,
            top_p=self.config.models.top_p,
            max_tokens=self.config.models.max_tokens
        )
        
    def _get_diagnosis_system_prompt(self) -> str:
        return """You are an Instrument Diagnosis Assistant specialized in analyzing 
        instrument logs, recognizing system components, and providing troubleshooting 
        guidance using Amazon Nova models. Your core capabilities include:
        
        1. Log Analysis: Compare system logs against gold standards
        2. Component Recognition: Identify hardware/software from documentation
        3. Multi-modal Processing: Analyze guides with text, images, and diagrams
        4. Cross-source Correlation: Correlate information across data sources
        5. Diagnosis Generation: Provide clear pass/fail determinations
        
        Always provide actionable guidance with confidence levels."""
        
    def _get_specialized_tools(self) -> List[callable]:
        return [
            # Local tools for quick operations
            extract_failure_indicators,
            generate_recommendations,
            calculate_confidence_score,
            # Gateway tools added via MCP client
        ]
    
    def get_multimodal_model(self) -> BedrockModel:
        """Access to multimodal model for document processing"""
        return self.multimodal_model
```

**Benefits**:
- Better integration with existing configuration system
- Specialized system prompt for diagnosis tasks
- Direct access to multimodal capabilities
- Cleaner separation of concerns

## 4. Configuration Integration Enhancement

**Current State**: Custom config system with good functionality  
**Enhancement Opportunity**: Better integration with AgentCore SSM parameters

### Recommended Enhancement
```python
def _load_agentcore_config(self) -> DiagnosisConfig:
    """Load configuration from SSM parameters and local config files"""
    try:
        # Load SSM parameters
        ssm_config = {
            'knowledge_base_id': get_ssm_parameter('/app/instrument-diagnosis/knowledge_base/knowledge_base_id'),
            'gateway_url': get_ssm_parameter('/app/instrument-diagnosis/agentcore/gateway_url'),
            'runtime_role': get_ssm_parameter('/app/instrument-diagnosis/agentcore/runtime_iam_role'),
            'cognito_discovery_url': get_ssm_parameter('/app/instrument-diagnosis/agentcore/cognito_discovery_url'),
            'web_client_id': get_ssm_parameter('/app/instrument-diagnosis/agentcore/web_client_id')
        }
        
        # Merge with local configuration
        local_config = self.config_manager.get_config()
        return merge_configs(local_config, ssm_config)
        
    except Exception as e:
        logger.warning(f"Failed to load SSM parameters: {e}. Using local config only.")
        return self.config_manager.get_config()
```

**Benefits**:
- Seamless integration between local and AWS configuration
- Better deployment flexibility
- Consistent configuration management across environments

## 5. Resource Naming Consistency

**Current State**: Uses generic `myapp` prefix in deployment scripts  
**Enhancement Opportunity**: Project-specific naming throughout

### Recommended Changes

#### Update `scripts/prereq.sh`
```bash
# ----- Config -----
BUCKET_NAME=${1:-instrument-diagnosis}
INFRA_STACK_NAME=${2:-InstrumentDiagnosisStackInfra}
COGNITO_STACK_NAME=${3:-InstrumentDiagnosisStackCognito}
```

#### Update SSM Parameter Paths
```bash
/app/instrument-diagnosis/agentcore/gateway_url
/app/instrument-diagnosis/agentcore/runtime_iam_role
/app/instrument-diagnosis/agentcore/cognito_discovery_url
/app/instrument-diagnosis/agentcore/web_client_id
/app/instrument-diagnosis/knowledge_base/knowledge_base_id
/app/instrument-diagnosis/knowledge_base/data_source_id
```

#### Update CloudFormation Templates
- Use `InstrumentDiagnosis` prefix for all resources
- Update IAM role names to be project-specific
- Ensure consistent tagging across all resources

**Benefits**:
- Clearer resource identification in AWS console
- Better organization for multi-project environments
- Reduced naming conflicts

## 6. Testing Enhancement

**Current State**: Basic integration tests present  
**Enhancement Opportunity**: More comprehensive test coverage

### Recommended Additions
- **Gateway Integration Tests**: Test MCP protocol compliance
- **Tool Performance Tests**: Validate large file processing capabilities
- **Configuration Tests**: Verify SSM parameter integration
- **Multi-modal Tests**: Test Nova Canvas integration
- **End-to-end Workflow Tests**: Complete diagnosis workflows

## Implementation Priority

### High Priority (When Ready)
1. **Lambda Gateway Enhancement**: Implement MCP-compatible handler
2. **Tool Distribution**: Move heavy processing to gateway
3. **Resource Naming**: Update to project-specific naming

### Medium Priority
4. **Agent Class Enhancement**: Add multimodal integration
5. **Configuration Integration**: Better SSM parameter handling
6. **Testing Enhancement**: Comprehensive test suite

### Low Priority
7. **Documentation Updates**: Reflect AgentCore patterns in docs
8. **Performance Optimization**: Fine-tune for specific use cases
9. **Monitoring Enhancement**: Add custom metrics and dashboards

## Conclusion

The Instrument Diagnosis Assistant is already well-aligned with AgentCore patterns and functions effectively. These improvements represent optimization opportunities rather than critical fixes. The project demonstrates excellent understanding of the AgentCore framework and implements sophisticated diagnosis capabilities.

**Key Strengths to Preserve**:
- Sophisticated tool functionality and diagnosis logic
- Proper Strands integration with `@tool` decorators
- Complete infrastructure setup with CloudFormation
- Comprehensive configuration management system
- Good documentation and user guides

**Next Steps**: 
- Review these recommendations when planning future enhancements
- Prioritize based on specific performance needs or scaling requirements
- Consider implementing during major version updates or refactoring cycles