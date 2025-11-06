from .context import TemplateContext
from .memory_hook_provider import MemoryHook
from .utils import get_ssm_parameter
from .agent import InstrumentDiagnosisAgent, TemplateAgent
from .config_manager import get_config_manager, ConfigurationError
from bedrock_agentcore.memory import MemoryClient
from .tools.sample_tools import get_system_info
from .tools.log_analysis_tools import LOG_ANALYSIS_TOOLS
from .tools.diagnosis_tools import DIAGNOSIS_TOOLS
from .tools.component_recognition_tools import COMPONENT_RECOGNITION_TOOLS
from .tools.multimodal_processing_tools import MULTIMODAL_PROCESSING_TOOLS
from .tools.cross_source_correlation_tools import CROSS_SOURCE_CORRELATION_TOOLS
from .tools.consistency_management_tools import CONSISTENCY_MANAGEMENT_TOOLS
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

memory_client = MemoryClient()


async def agent_task(user_message: str, session_id: str, actor_id: str):
    """
    Execute agent task with configuration management support
    
    Args:
        user_message: User's input message
        session_id: Session identifier
        actor_id: Actor identifier
    """
    agent = TemplateContext.get_agent_ctx()

    response_queue = TemplateContext.get_response_queue_ctx()
    gateway_access_token = TemplateContext.get_gateway_token_ctx()

    if not gateway_access_token:
        logger.warning("Gateway Access token is none - using fallback mode")
        # Set a dummy token for fallback mode
        gateway_access_token = "fallback-mode"
    
    try:
        if agent is None:
            # Load configuration with fallback
            config_manager = None
            config = None
            try:
                config_manager = get_config_manager()
                config = config_manager.get_config()
                logger.info(f"Loaded configuration for environment: {config.deployment.environment}")
                
                # Set debug logging if configured
                if config.deployment.debug_logging:
                    logging.getLogger().setLevel(logging.DEBUG)
                    logger.debug("Debug logging enabled")
                
            except ConfigurationError as e:
                logger.warning(f"Configuration error, using defaults: {e}")
                config_manager = None
                config = None
            except Exception as e:
                logger.warning(f"Error loading configuration, using defaults: {e}")
                config_manager = None
                config = None

            # Create memory hook with fallback
            try:
                memory_id = get_ssm_parameter("/app/myapp/agentcore/memory_id")
                memory_hook = MemoryHook(
                    memory_client=memory_client,
                    memory_id=memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                )
                logger.info(f"Memory hook initialized with ID: {memory_id}")
            except Exception as e:
                logger.warning(f"Error creating memory hook, using fallback: {e}")
                # Use a fallback memory hook or None
                try:
                    # Try to use the known memory ID from agentcore status
                    fallback_memory_id = "instrument_diagnosis_assistant_mem-vtn85A4peW"
                    memory_hook = MemoryHook(
                        memory_client=memory_client,
                        memory_id=fallback_memory_id,
                        actor_id=actor_id,
                        session_id=session_id,
                    )
                    logger.info(f"Using fallback memory ID: {fallback_memory_id}")
                except Exception as fallback_error:
                    logger.warning(f"Fallback memory also failed: {fallback_error}")
                    # Create a minimal memory hook
                    memory_hook = None

            # Create agent with configuration
            try:
                agent = InstrumentDiagnosisAgent(
                    bearer_token=gateway_access_token,
                    memory_hook=memory_hook,
                    config_manager=config_manager,
                    tools=[get_system_info] + LOG_ANALYSIS_TOOLS + DIAGNOSIS_TOOLS + COMPONENT_RECOGNITION_TOOLS + 
                          MULTIMODAL_PROCESSING_TOOLS + CROSS_SOURCE_CORRELATION_TOOLS + CONSISTENCY_MANAGEMENT_TOOLS,
                )
                
                if config:
                    logger.info(f"Initialized Instrument Diagnosis Agent with models: "
                              f"text={config.models.text_model}, multimodal={config.models.multimodal_model}")
                else:
                    logger.info("Initialized Instrument Diagnosis Agent with default configuration")

                TemplateContext.set_agent_ctx(agent)
                
            except Exception as e:
                logger.error(f"Error creating agent: {e}")
                await response_queue.put(f"Error initializing agent: {e}")
                return

        # Execute agent task
        try:
            async for chunk in agent.stream(user_query=user_message):
                await response_queue.put(chunk)
        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            await response_queue.put(f"Error processing request: {e}")

    except Exception as e:
        logger.exception("Agent execution failed.")
        await response_queue.put(f"Error: {str(e)}")
    finally:
        await response_queue.finish()
