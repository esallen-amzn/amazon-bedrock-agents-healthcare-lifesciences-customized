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

# Load Knowledge Base ID from config file instead of SSM
try:
    with open('/app/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    os.environ["KNOWLEDGE_BASE_ID"] = config.get('knowledge_base', {}).get('kb_id', 'E9DAYQSO7C')
except Exception as e:
    # Fallback to the existing KB ID
    os.environ["KNOWLEDGE_BASE_ID"] = "E9DAYQSO7C"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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