"""
Alternative invoke function using AgentCore CLI instead of boto3
This ensures we get the same behavior as the direct CLI invocation
"""

import json
import subprocess
import logging
from typing import Iterator

logger = logging.getLogger(__name__)


def invoke_agent_via_cli(
    prompt: str,
    agent_name: str,
    runtime_session_id: str,
    show_tool: bool = True,
) -> Iterator[str]:
    """
    Invoke agent using the agentcore CLI command and yield streaming response chunks.
    
    This method uses the same CLI that works perfectly in our tests, ensuring
    consistent behavior between direct invocation and Streamlit.
    
    Args:
        prompt: User prompt to send to agent
        agent_name: Name of the configured agent
        runtime_session_id: Session ID for conversation continuity
        show_tool: Whether to show tool usage (currently ignored for CLI)
    
    Yields:
        String chunks of the agent's response
    """
    try:
        # Create payload
        payload = {"prompt": prompt}
        payload_json = json.dumps(payload)
        
        logger.info(f"Invoking agent via CLI: {agent_name}")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"Session ID: {runtime_session_id}")
        
        # Build CLI command
        cmd = [
            "agentcore", "invoke",
            "--agent", agent_name,
            "--session-id", runtime_session_id,
            payload_json
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Stream output line by line
        for line in process.stdout:
            # Skip the CLI's status box and formatting
            if line.strip().startswith(('┌', '│', '└', '─', '╭', '╮', '╰', '╯')):
                continue
            if 'Using tool:' in line or '🔧' in line:
                if show_tool:
                    yield f"\n_[Tool: {line.strip()}]_\n"
                continue
            if '<thinking>' in line or '</thinking>' in line:
                continue
            if 'Logs:' in line or 'GenAI Dashboard:' in line:
                continue
            if 'aws logs tail' in line:
                continue
            
            # Yield actual response content
            if line.strip():
                yield line
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code != 0:
            stderr_output = process.stderr.read()
            logger.error(f"CLI invocation failed with code {return_code}: {stderr_output}")
            yield f"\n\n**Error**: Agent invocation failed. Please check the logs.\n"
        else:
            logger.info("CLI invocation completed successfully")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Exception during CLI invocation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        yield f"\n\n**Error**: {error_msg}\n"
