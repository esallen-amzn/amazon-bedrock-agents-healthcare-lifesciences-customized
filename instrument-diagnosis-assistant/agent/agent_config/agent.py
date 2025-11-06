from .utils import get_ssm_parameter
from .memory_hook_provider import MemoryHook
from .config_manager import get_config_manager, ConfigManager, DiagnosisConfig
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands_tools import current_time, retrieve
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from typing import List, Optional
import logging

# Import local tools
try:
    from .tools.diagnosis_tools import generate_diagnosis, calculate_confidence_score, generate_recommendations
    from .tools.log_analysis_tools import analyze_logs, process_large_files, extract_failure_indicators
    from .tools.component_recognition_tools import extract_components, map_functions, build_inventory, resolve_naming, correlate_components, search_components
    LOCAL_TOOLS_AVAILABLE = True
except ImportError as e:
    # Logger might not be defined yet, so use print for now
    print(f"Local tools not available: {e}")
    LOCAL_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)


class InstrumentDiagnosisAgent:
    """
    Instrument Diagnosis Assistant Agent
    
    AI agent specialized in analyzing instrument logs, recognizing system components,
    and providing troubleshooting guidance using Amazon Nova models.
    """
    
    def __init__(
        self,
        bearer_token: str,
        memory_hook: MemoryHook,
        config_manager: Optional[ConfigManager] = None,
        tools: List[callable] = None,
    ):
        # Initialize configuration manager with fallback
        try:
            self.config_manager = config_manager or get_config_manager()
            self.config = self.config_manager.get_config()
            
            # Set up model configuration
            model_config = self.config.models
            self.model_id = model_config.text_model
            self.multimodal_model_id = model_config.multimodal_model
            temperature = model_config.temperature
            top_p = model_config.top_p
            max_tokens = model_config.max_tokens
        except Exception as e:
            logger.warning(f"Configuration error, using defaults: {e}")
            # Use default values if config fails
            self.model_id = "us.amazon.nova-pro-v1:0"
            self.multimodal_model_id = "us.amazon.nova-canvas-v1:0"
            temperature = 0.3
            top_p = 0.9
            max_tokens = 4096
        
        # Create primary model for text analysis
        self.model = BedrockModel(
            model_id=self.model_id,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        
        # Create multimodal model for document processing
        self.multimodal_model = BedrockModel(
            model_id=self.multimodal_model_id,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        
        # Set up system prompt for instrument diagnosis
        self.system_prompt = self._get_system_prompt()
        
        logger.info(f"Initialized Instrument Diagnosis Agent with models: {self.model_id}, {self.multimodal_model_id}")

        # Initialize gateway client (optional)
        self.gateway_client = None
        gateway_tools = []
        
        try:
            gateway_url = get_ssm_parameter("/app/myapp/agentcore/gateway_url")
            logger.info(f"Gateway Endpoint - MCP URL: {gateway_url}")

            self.gateway_client = MCPClient(
                lambda: streamablehttp_client(
                    gateway_url,
                    headers={"Authorization": f"Bearer {bearer_token}"},
                )
            )

            self.gateway_client.start()
            gateway_tools = self.gateway_client.list_tools_sync()
            logger.info(f"Loaded {len(gateway_tools)} gateway tools")
        except Exception as e:
            logger.warning(f"Gateway not available, continuing without gateway tools: {str(e)}")

        # Set up tools
        base_tools = [retrieve, current_time]
        
        # Add local tools if available
        local_tools = []
        if LOCAL_TOOLS_AVAILABLE:
            try:
                local_tools = [
                    generate_diagnosis,
                    calculate_confidence_score,
                    generate_recommendations,
                    analyze_logs,
                    process_large_files,
                    extract_failure_indicators,
                    extract_components,
                    map_functions,
                    build_inventory,
                    resolve_naming,
                    correlate_components,
                    search_components,
                ]
                logger.info(f"Loaded {len(local_tools)} local tools")
            except Exception as e:
                logger.warning(f"Failed to load local tools: {e}")
                local_tools = []
        
        self.tools = (
            base_tools
            + local_tools
            + gateway_tools
            + (tools or [])
        )

        self.memory_hook = memory_hook

        # Create the main agent
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
            hooks=[self.memory_hook],
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the instrument diagnosis assistant"""
        return """You are an Instrument Diagnosis Assistant, an AI expert specialized in analyzing instrument logs, 
recognizing system components, and providing troubleshooting guidance. You help technicians diagnose instrument 
failures by comparing logs against gold standards, identifying components from documentation, and correlating 
information across multiple data sources.

Your core capabilities include:

1. **Log Analysis**: Compare system logs and PC logs from failed units against gold standard patterns to identify 
   failure indicators and make pass/fail determinations with confidence levels.

2. **Component Recognition**: Identify hardware and software components from engineering documentation, maintain 
   comprehensive inventories, and handle variations in component naming conventions.

3. **Multi-modal Document Processing**: Process troubleshooting guides containing text, images, and diagrams 
   using advanced vision capabilities to provide contextual guidance.

4. **Cross-source Correlation**: Correlate component references across log files and documentation, associate 
   failure patterns with relevant troubleshooting procedures, and provide unified analysis.

Guidelines for your responses:
- Always provide clear, actionable guidance for technicians
- Include confidence levels for your diagnoses and recommendations
- Reference specific log patterns, components, or documentation when making assessments
- Maintain professional technical language appropriate for instrument technicians
- When analyzing large files, process them efficiently in chunks while maintaining accuracy
- Correlate findings across multiple data sources to provide comprehensive analysis
- Focus on practical troubleshooting steps and component-specific guidance

You have access to specialized tools for log processing, component recognition, document analysis, and 
cross-source correlation. Use these tools effectively to provide thorough and accurate instrument diagnosis."""
    
    def get_config(self) -> DiagnosisConfig:
        """Get the current configuration"""
        return self.config
    
    def get_multimodal_model(self) -> BedrockModel:
        """Get the multimodal model for document processing"""
        return self.multimodal_model
    
    def reload_config(self) -> None:
        """Reload configuration and update models if needed"""
        self.config_manager.reload_config()
        self.config = self.config_manager.get_config()
        
        # Update models if configuration changed
        model_config = self.config.models
        if self.model_id != model_config.text_model:
            self.model_id = model_config.text_model
            self.model = BedrockModel(
                model_id=self.model_id,
                temperature=model_config.temperature,
                top_p=model_config.top_p,
                max_tokens=model_config.max_tokens,
            )
            logger.info(f"Updated text model to: {self.model_id}")
        
        if self.multimodal_model_id != model_config.multimodal_model:
            self.multimodal_model_id = model_config.multimodal_model
            self.multimodal_model = BedrockModel(
                model_id=self.multimodal_model_id,
                temperature=model_config.temperature,
                top_p=model_config.top_p,
                max_tokens=model_config.max_tokens,
            )
            logger.info(f"Updated multimodal model to: {self.multimodal_model_id}")
    
    def invoke(self, user_query: str):
        """Invoke the agent with a user query and return the response"""
        try:
            response = str(self.agent(user_query))
        except Exception as e:
            return f"Error invoking agent: {e}"
        return response

    async def stream(self, user_query: str):
        """Stream the agent response for a user query"""
        try:
            async for event in self.agent.stream_async(user_query):
                if "current_tool_use" in event:
                    tool_name = event["current_tool_use"]["name"]
                    yield f"🔧 Using tool: {tool_name}\n"
                elif "data" in event:
                    yield event["data"]
        except Exception as e:
            yield f"Error during streaming: {e}"


# Maintain backward compatibility
class TemplateAgent(InstrumentDiagnosisAgent):
    """Backward compatibility alias for the original TemplateAgent"""
    
    def __init__(
        self,
        bearer_token: str,
        memory_hook: MemoryHook,
        bedrock_model_id: str = None,  # Deprecated parameter
        system_prompt: str = None,     # Deprecated parameter
        tools: List[callable] = None,
    ):
        # Log deprecation warning if old parameters are used
        if bedrock_model_id is not None:
            logger.warning("bedrock_model_id parameter is deprecated. Use config.yaml to set model configuration.")
        if system_prompt is not None:
            logger.warning("system_prompt parameter is deprecated. The agent uses a specialized system prompt.")
        
        super().__init__(bearer_token, memory_hook, tools=tools)

    def invoke(self, user_query: str):
        try:
            response = str(self.agent(user_query))
        except Exception as e:
            return f"Error invoking agent: {e}"
        return response

    async def stream(self, user_query: str):
        try:

            tool_name = None
            async for event in self.agent.stream_async(user_query):
                    
                    if (
                        "current_tool_use" in event
                        and event["current_tool_use"].get("name") != tool_name
                    ):
                        tool_name = event["current_tool_use"]["name"]
                        yield f"\n\n🔧 Using tool: {tool_name}\n\n"
                    elif "message" in event and "content" in event["message"]:
                        for obj in event["message"]["content"]:
                            if "toolResult" in obj:
                                tool_result = obj["toolResult"]["content"][0]["text"]
                                yield f"\n\n🔧 Tool result: {tool_result}\n\n"

                    if "data" in event:
                        tool_name = None
                        yield event["data"] 

        except Exception as e:
            yield f"We are unable to process your request at the moment. Error: {e}"
