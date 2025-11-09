"""
Fixed invoke_agent_streaming function with boto3 bedrock-agentcore client,
proper SSE parsing, and extended timeouts.
"""

import json
import logging
import uuid
from typing import Iterator
import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


def invoke_agent_streaming(
    prompt: str,
    agent_arn: str,
    runtime_session_id: str,
    region: str = "us-east-1",
    show_tool: bool = True,
) -> Iterator[str]:
    """Invoke agent and yield streaming response chunks using boto3 bedrock-agentcore client"""
    
    try:
        # Use boto3 bedrock-agentcore client with extended timeout for S3 operations
        config = Config(
            read_timeout=300,  # 5 minutes for S3 operations
            connect_timeout=60,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        client = boto3.client('bedrock-agentcore', region_name=region, config=config)
        
        # Log the prompt for debugging
        logger.info(f"Invoking agent via boto3 bedrock-agentcore client")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"Prompt contains 's3://': {('s3://' in prompt)}")
        logger.info(f"First 500 chars: {prompt[:500]}")
        
        # Ensure session ID meets minimum length requirement (33 characters)
        if len(runtime_session_id) < 33:
            runtime_session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {runtime_session_id}")
        
        # Create payload
        payload = {"prompt": prompt}
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        logger.info(f"Payload size: {len(payload_bytes)} bytes")
        
        # Invoke the agent using boto3 bedrock-agentcore client
        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=runtime_session_id,
            payload=payload_bytes,
            contentType='application/json',
            accept='application/json'
        )
        
        logger.info(f"Agent invoked successfully, streaming response...")
        
        # Stream the response chunks
        # The response format is text/event-stream with raw bytes
        event_stream = response.get('response', [])
        
        for event in event_stream:
            # The event is raw bytes in SSE (Server-Sent Events) format
            if isinstance(event, bytes):
                try:
                    # Decode the bytes to text
                    text = event.decode('utf-8', errors='replace')
                    
                    # SSE format: Each chunk may contain multiple "data: <content>\n\n" lines
                    # Split by "data: " to get individual messages
                    lines = text.split('data: ')
                    
                    for line in lines:
                        if not line.strip():
                            continue
                            
                        # Remove trailing newlines
                        content = line.rstrip('\n')
                        
                        # Remove quotes if present (SSE often wraps content in quotes)
                        if content.startswith('"') and content.endswith('"'):
                            content = content[1:-1]
                        
                        # Unescape common escape sequences
                        content = content.replace('\\n', '\n').replace('\\t', '\t')
                        
                        if content:  # Only yield non-empty content
                            yield content
                        
                except Exception as e:
                    logger.error(f"Error decoding event: {e}")
                    continue
                    
            # Handle dict format (fallback for different response types)
            elif isinstance(event, dict):
                if 'chunk' in event:
                    chunk_data = event['chunk']
                    if 'bytes' in chunk_data:
                        text = chunk_data['bytes'].decode('utf-8', errors='replace')
                        yield text
                        
                elif 'trace' in event and show_tool:
                    trace_data = event['trace']
                    trace_text = json.dumps(trace_data, indent=2)
                    logger.debug(f"Trace: {trace_text}")
                    
                elif 'internalServerException' in event:
                    error_msg = event['internalServerException'].get('message', 'Internal server error')
                    logger.error(f"Internal server error: {error_msg}")
                    yield f"\n\n**Error**: {error_msg}\n\n"
                    
                elif 'validationException' in event:
                    error_msg = event['validationException'].get('message', 'Validation error')
                    logger.error(f"Validation error: {error_msg}")
                    yield f"\n\n**Error**: {error_msg}\n\n"
                    
                elif 'throttlingException' in event:
                    error_msg = event['throttlingException'].get('message', 'Request throttled')
                    logger.error(f"Throttling error: {error_msg}")
                    yield f"\n\n**Error**: {error_msg}\n\n"
        
        logger.info("Agent streaming completed successfully")
            
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Exception during agent invocation: {error_type}: {error_msg}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Check for specific error types
        if "ended prematurely" in error_msg.lower():
            yield f"\n\n**Response Incomplete**: The agent's response was cut off. This may be due to:\n"
            yield f"- Large file processing taking too long\n"
            yield f"- Network timeout\n"
            yield f"- Model output limit reached\n\n"
            yield f"Try asking: 'Continue the analysis' or 'Provide summary only'\n\n"
        elif "token" in error_msg.lower() and "exceed" in error_msg.lower():
            yield f"\n\n**Token Limit Exceeded**: The input or output was too large.\n"
            yield f"Try: 'Analyze one file at a time' or 'Provide brief summary'\n\n"
        else:
            yield f"\n\n**Error**: {error_type}: {error_msg}\n\n"
