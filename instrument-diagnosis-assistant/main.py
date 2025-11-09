from agent.agent_config.context import TemplateContext
from agent.agent_config.agent_task import agent_task
from agent.agent_config.streaming_queue import StreamingQueue
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import asyncio
import logging
import os
import yaml

# Environment flags
os.environ["STRANDS_OTEL_ENABLE_CONSOLE_EXPORT"] = "true"
os.environ["STRANDS_TOOL_CONSOLE_MODE"] = "enabled"

# Logging setup (must be before config loading)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Knowledge Base ID from config file instead of SSM
try:
    # Try multiple config file locations
    config_paths = ['/app/config.yaml', './config.yaml', 'config.yaml']
    config = None
    
    for config_path in config_paths:
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from: {config_path}")
                break
        except FileNotFoundError:
            continue
    
    if config:
        kb_id = config.get('knowledge_base', {}).get('kb_id', 'E9DAYQSO7C')
        os.environ["KNOWLEDGE_BASE_ID"] = kb_id
        logger.info(f"Set KNOWLEDGE_BASE_ID to: {kb_id}")
    else:
        raise FileNotFoundError("No config file found")
        
except Exception as e:
    # Fallback to the existing KB ID
    logger.warning(f"Config loading failed: {e}, using fallback KB ID")
    os.environ["KNOWLEDGE_BASE_ID"] = "E9DAYQSO7C"


# Bedrock app and global agent instance
app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    if not TemplateContext.get_response_queue_ctx():
        TemplateContext.set_response_queue_ctx(StreamingQueue())

    # Set fallback gateway token for basic functionality
    if not TemplateContext.get_gateway_token_ctx():
        TemplateContext.set_gateway_token_ctx("fallback-mode")

    user_message = payload["prompt"]
    actor_id = "a"

    session_id = context.session_id

    # DEBUG: Log what we actually received
    logger.info(f"=== MAIN.PY RECEIVED PAYLOAD ===")
    logger.info(f"Payload keys: {list(payload.keys())}")
    logger.info(f"Prompt length: {len(user_message)} characters")
    logger.info(f"Prompt contains 's3://': {('s3://' in user_message)}")
    logger.info(f"First 500 chars of prompt: {user_message[:500]}")
    logger.info(f"Last 100 chars of prompt: {user_message[-100:]}")
    logger.info(f"=== END PAYLOAD DEBUG ===")

    if not session_id:
        raise Exception("Context session_id is not set")

    task = asyncio.create_task(
        agent_task(
            user_message=user_message,
            session_id=session_id,
            actor_id=actor_id,
        )
    )

    response_queue = TemplateContext.get_response_queue_ctx()

    async def stream_output():
        
        async for event in response_queue.stream():
                print(event)
                
                logging.info(event)
                yield event
                 
        await task  # Ensure task completion

    return stream_output() 


if __name__ == "__main__":
    print('running')
    app.run()