import json
import logging
import re
import sys
import time
import uuid
from typing import Dict, Iterator, List

import boto3
from botocore.config import Config
import streamlit as st

# Configure logger with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure the handler uses UTF-8 encoding
for handler in logger.handlers:
    if hasattr(handler, 'stream') and hasattr(handler.stream, 'reconfigure'):
        try:
            handler.stream.reconfigure(encoding='utf-8')
        except:
            pass

# Page config
st.set_page_config(
    page_title="Instrument Diagnosis Assistant",
    page_icon="static/gen-ai-dark.svg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove Streamlit deployment components
st.markdown(
    """
      <style>
        .stAppDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
      </style>
    """,
    unsafe_allow_html=True,
)

HUMAN_AVATAR = "static/user-profile.svg"
AI_AVATAR = "static/gen-ai-dark.svg"


def safe_clean_text(text):
    """Aggressively clean any Unicode that could cause charmap issues"""
    if not isinstance(text, str):
        return text
    # Remove all non-ASCII characters immediately
    return ''.join(c if ord(c) < 128 else '?' for c in text)

def clean_session_state_unicode():
    """Clean any Unicode characters from session state that might cause issues"""
    if 'messages' in st.session_state:
        for message in st.session_state.messages:
            if 'content' in message and isinstance(message['content'], str):
                # Clean Unicode from message content
                message['content'] = safe_clean_text(message['content'])
    
    if 'diagnosis_results' in st.session_state and st.session_state.diagnosis_results:
        results = st.session_state.diagnosis_results
        for key, value in results.items():
            if isinstance(value, str):
                results[key] = safe_clean_text(value)
            elif isinstance(value, list):
                results[key] = [safe_clean_text(item) if isinstance(item, str) else item for item in value]

def get_log_files_only():
    """Get only log files (gold_logs and failed_logs) from session state"""
    log_files = []
    if 'uploaded_files' in st.session_state:
        # Only include log files, NOT documentation
        for category in ['gold_logs', 'failed_logs']:
            file_list = st.session_state.uploaded_files.get(category, [])
            if file_list:
                log_files.extend(file_list)
    return log_files


def get_documentation_summary():
    """Get a summary of uploaded documentation files (not the content)"""
    if 'uploaded_files' not in st.session_state:
        return ""
    
    doc_files = st.session_state.uploaded_files.get('documentation', [])
    if not doc_files:
        return ""
    
    summary = ["\n--- SUPPLEMENTAL DOCUMENTATION AVAILABLE ---"]
    summary.append(f"The user has uploaded {len(doc_files)} documentation file(s) as supplemental reference:")
    for doc_file in doc_files:
        summary.append(f"  - {doc_file.name} ({doc_file.size / 1024:.1f} KB)")
    summary.append("These are reference documents (NOT logs to analyze).")
    summary.append("Use your Knowledge Base as primary reference, and these as supplemental context if needed.")
    summary.append("-" * 50)
    return "\n".join(summary)


# Import S3 integration functions
from s3_integration import (
    upload_files_to_s3,
    update_session_file_registry,
    get_session_context,
    load_existing_s3_files_for_session,
    process_uploaded_files
)


def clean_response_text(text: str, show_thinking: bool = True) -> str:
    """Clean and format response text for better presentation"""
    if not text:
        return text

    # Handle the consecutive quoted chunks pattern
    # Pattern: "word1" "word2" "word3" -> word1 word2 word3
    text = re.sub(r'"\s*"', "", text)
    text = re.sub(r'^"', "", text)
    text = re.sub(r'"$', "", text)

    # Replace literal \n with actual newlines
    text = text.replace("\\n", "\n")

    # Replace literal \t with actual tabs
    text = text.replace("\\t", "\t")

    # Clean up multiple spaces
    text = re.sub(r" {3,}", " ", text)

    # Fix newlines that got converted to spaces
    text = text.replace(" \n ", "\n")
    text = text.replace("\n ", "\n")
    text = text.replace(" \n", "\n")

    # Handle numbered lists
    text = re.sub(r"\n(\d+)\.\s+", r"\n\1. ", text)
    text = re.sub(r"^(\d+)\.\s+", r"\1. ", text)

    # Handle bullet points
    text = re.sub(r"\n-\s+", r"\n- ", text)
    text = re.sub(r"^-\s+", r"- ", text)

    # Convert ALL markdown headers to bold text (no large fonts)
    # This must be done BEFORE other formatting to prevent headers from rendering
    # Match any line starting with one or more # symbols followed by space and text
    text = re.sub(r"^#{1,6}\s+(.+?)$", r"**\1**", text, flags=re.MULTILINE)
    text = re.sub(r"\n#{1,6}\s+(.+?)$", r"\n**\1**", text, flags=re.MULTILINE)

    # Handle section headers (text followed by colon)
    text = re.sub(r"\n([A-Za-z][A-Za-z\s]{2,30}):\s*\n", r"\n**\1:**\n\n", text)

    # Clean up multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean up thinking

    if not show_thinking:
        text = re.sub(r"<thinking>.*?</thinking>", "", text)

    return text.strip()


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
            read_timeout=600,  # 10 minutes for complex analysis
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



def stream_agent_response(prompt: str, agent_arn: str, runtime_session_id: str, region: str, show_tools: bool, show_thinking: bool):
    """
    Helper function to stream agent response and handle display.
    Returns the full response text.
    """
    message_placeholder = st.empty()
    chunk_buffer = ""
    auto_format = True  # Always format responses
    show_raw = False  # Never show raw

    try:
        # Stream the response
        for chunk in invoke_agent_streaming(prompt, agent_arn, runtime_session_id, region, show_tools):
            # Ensure chunk is a string
            if not isinstance(chunk, str):
                chunk = str(chunk)

            # Add chunk to buffer
            chunk_buffer += chunk

            # Update display periodically
            if len(chunk_buffer) % 3 == 0 or chunk.endswith(" ") or chunk.endswith("\n"):
                cleaned_response = clean_response_text(chunk_buffer, show_thinking)
                message_placeholder.markdown(cleaned_response + " |")
            
            time.sleep(0.01)

        # Final response without cursor
        full_response = clean_response_text(chunk_buffer, show_thinking)
        message_placeholder.markdown(full_response)

        return full_response

    except Exception as e:
        error_msg = f"**Error:** {str(e)}"
        message_placeholder.markdown(error_msg)
        return error_msg


def main():
    # Clean any Unicode characters from session state first
    clean_session_state_unicode()
    
    st.logo("static/agentcore-service-icon.png", size="large")
    st.title("🔧 Instrument Diagnosis Assistant")
    
    # Add file upload section at the top
    st.markdown("**📁 Upload Files for Analysis**")
    
    # Create tabs for different file types
    tab1, tab2 = st.tabs(["📊 Log Files", "📋 Documentation"])
    
    with tab1:
        st.markdown("**Upload instrument log files for analysis**")
        st.markdown("*Gold standard logs are optional - analysis can be performed with problem logs alone*")
        col1, col2 = st.columns(2)
        
        with col1:
            gold_standard_logs = st.file_uploader(
                "Gold Standard Logs (Optional)",
                type=['txt', 'log', 'csv'],
                accept_multiple_files=True,
                key="gold_logs",
                help="Optional: Upload logs from properly functioning instruments for comparison analysis"
            )
        
        with col2:
            failed_unit_logs = st.file_uploader(
                "Problem Unit Logs (Required)",
                type=['txt', 'log', 'csv'],
                accept_multiple_files=True,
                key="failed_logs",
                help="Upload logs from instruments experiencing issues - this is the primary data for analysis"
            )
    
    with tab2:
        st.markdown("**Upload reference documentation (NOT log files)**")
        st.markdown("*Include troubleshooting guides, component specs, system architecture docs, repair procedures, etc.*")
        documentation_files = st.file_uploader(
            "Documentation Files",
            type=['pdf', 'doc', 'docx', 'txt', 'md', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="documentation",
            help="Upload reference documentation - these will be treated as supporting documentation, not as logs to analyze"
        )
    
    # Store uploaded files in session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {
            'gold_logs': [],
            'failed_logs': [],
            'documentation': []
        }
    
    # Update session state with uploaded files
    if gold_standard_logs:
        st.session_state.uploaded_files['gold_logs'] = gold_standard_logs
    if failed_unit_logs:
        st.session_state.uploaded_files['failed_logs'] = failed_unit_logs
    if documentation_files:
        st.session_state.uploaded_files['documentation'] = documentation_files
    
    # Show file summary if files are uploaded
    total_files = sum(len(files) for files in st.session_state.uploaded_files.values())
    if total_files > 0:
        # Calculate total file size and categorize files
        total_size = 0
        large_files = []
        file_categories = []
        
        for category, file_list in st.session_state.uploaded_files.items():
            if file_list:
                category_names = {
                    'gold_logs': 'Gold Standard',
                    'failed_logs': 'Problem Unit', 
                    'documentation': 'Documentation'
                }
                file_categories.append(f"{len(file_list)} {category_names.get(category, category)}")
                
                for file in file_list:
                    total_size += file.size
                    if file.size > 1024 * 1024:  # 1MB
                        large_files.append(f"{file.name} ({file.size // 1024}KB)")
        
        st.success(f"✅ {total_files} files uploaded: {', '.join(file_categories)}")
        
        # Show analysis readiness
        has_problem_logs = bool(st.session_state.uploaded_files.get('failed_logs'))
        has_gold_logs = bool(st.session_state.uploaded_files.get('gold_logs'))
        
        if has_problem_logs:
            if has_gold_logs:
                st.info("🔍 Ready for comparative analysis with gold standard reference")
            else:
                st.info("🔍 Ready for standalone analysis (no gold standard for comparison)")
        
        if large_files:
            st.info(f"Large files detected: {', '.join(large_files)}. Content will be intelligently truncated for optimal processing.")
        
        if total_size > 10 * 1024 * 1024:  # 10MB total
            st.warning("Large total file size detected. Consider uploading smaller files or fewer files at once for better performance.")
    
    st.divider()

    # Configuration - all hardcoded, can be moved to config file
    region = "us-east-1"
    analysis_mode = "Comprehensive Analysis"
    confidence_threshold = 0.75
    include_visual_analysis = True
    max_file_content = 2000
    st.session_state.max_file_content = max_file_content
    auto_format = True
    show_raw = False
    show_tools = True
    show_thinking = False
    
    # Initialize session ID
    if "runtime_session_id" not in st.session_state:
        st.session_state.runtime_session_id = str(uuid.uuid4())
    runtime_session_id = st.session_state.runtime_session_id
    
    # Auto-fetch latest agent
    agent_arn = ""
    agent_name = "Unknown"
    try:
        client = boto3.client("bedrock-agentcore-control", region_name=region)
        response = client.list_agent_runtimes(maxResults=100)
        
        ready_agents = [
            agent for agent in response.get("agentRuntimes", [])
            if agent.get("status") == "READY"
        ]
        ready_agents.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)
        
        if ready_agents:
            latest_agent = ready_agents[0]
            agent_name = latest_agent.get("agentRuntimeName", "Unknown")
            agent_id = latest_agent.get("agentRuntimeId", "")
            
            versions_response = client.list_agent_runtime_versions(agentRuntimeId=agent_id)
            ready_versions = [
                v for v in versions_response.get("agentRuntimes", [])
                if v.get("status") == "READY"
            ]
            ready_versions.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)
            
            if ready_versions:
                latest_version = ready_versions[0]
                agent_arn = latest_version.get("agentRuntimeArn", "")
                version_num = latest_version.get("agentRuntimeVersion", "Unknown")
                agent_name = f"{agent_name} v{version_num}"
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        agent_name = "Error loading agent"
    
    # No sidebar - all configuration is automatic
        
        st.divider()


    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Diagnosis Results Display Section
    if 'diagnosis_results' in st.session_state and st.session_state.diagnosis_results:
        st.markdown("**Latest Diagnosis Results**")
        
        results = st.session_state.diagnosis_results
        
        # Status indicator
        status = results.get('status', 'UNKNOWN')
        confidence = results.get('confidence', 0.0)
        
        if status == 'PASS':
            st.success(f"**INSTRUMENT STATUS: PASS** (Confidence: {confidence:.1%})")
        elif status == 'FAIL':
            st.error(f"**INSTRUMENT STATUS: FAIL** (Confidence: {confidence:.1%})")
        else:
            st.warning(f"**INSTRUMENT STATUS: UNCERTAIN** (Confidence: {confidence:.1%})")
        
        # Results in columns
        col1, col2 = st.columns(2)
        
        with col1:
            if 'failure_indicators' in results and results['failure_indicators']:
                st.markdown("**Failure Indicators:**")
                for indicator in results['failure_indicators']:
                    st.markdown(f"- {indicator}")
        
        with col2:
            if 'recommendations' in results and results['recommendations']:
                st.markdown("**Recommendations:**")
                for rec in results['recommendations']:
                    st.markdown(f"- {rec}")
        
        if 'summary' in results:
            with st.expander("Detailed Analysis Summary"):
                st.markdown(results['summary'])
        
        st.divider()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message["avatar"]):
            # Check if this is a diagnosis result and format it specially
            if message["role"] == "assistant" and "INSTRUMENT STATUS:" in message["content"]:
                # Parse diagnosis results from assistant message
                content = message["content"]
                st.markdown(content)
                
                # Try to extract structured results for display
                if "Status:" in content and "Confidence:" in content:
                    try:
                        # Simple parsing - in a real implementation, you'd want more robust parsing
                        lines = content.split('\n')
                        status_line = next((line for line in lines if "Status:" in line), "")
                        confidence_line = next((line for line in lines if "Confidence:" in line), "")
                        
                        if status_line and confidence_line:
                            # Store results for the diagnosis display section
                            if 'diagnosis_results' not in st.session_state:
                                st.session_state.diagnosis_results = {}
                            
                            # Extract status and confidence (basic parsing)
                            status = "PASS" if "PASS" in status_line.upper() else "FAIL" if "FAIL" in status_line.upper() else "UNCERTAIN"
                            confidence_str = confidence_line.split(":")[-1].strip().replace("%", "")
                            try:
                                confidence = float(confidence_str) / 100.0
                            except:
                                confidence = 0.0
                            
                            st.session_state.diagnosis_results.update({
                                'status': status,
                                'confidence': confidence,
                                'summary': content
                            })
                    except:
                        pass  # If parsing fails, just display normally
            else:
                st.markdown(message["content"])

    # Handle pending prompt from button clicks
    if hasattr(st.session_state, 'pending_prompt') and st.session_state.pending_prompt:
        if not agent_arn:
            st.error("Please select an agent in the sidebar first.")
            st.session_state.pending_prompt = None
        else:
            prompt = st.session_state.pending_prompt
            st.session_state.pending_prompt = None  # Clear the pending prompt
            
            # Display user message
            with st.chat_message("user", avatar=HUMAN_AVATAR):
                st.markdown(prompt)

            # Generate assistant response
            with st.chat_message("assistant", avatar=AI_AVATAR):
                full_response = stream_agent_response(
                    prompt, agent_arn, st.session_state.runtime_session_id, region, show_tools, show_thinking
                )

            # Add assistant response to chat history
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response, "avatar": AI_AVATAR}
            )

    # Quick action buttons
    if st.button("🎯 Run Full Diagnosis"):
        if not agent_arn:
            st.error("Please select an agent in the sidebar first.")
        elif not st.session_state.uploaded_files.get('failed_logs'):
            st.error("Please upload problem unit logs first for diagnosis. Gold standard logs are optional.")
        else:
            # ONLY process LOG files for analysis (not documentation)
            log_files = get_log_files_only()
            log_contents = process_uploaded_files(log_files, st.session_state, st.session_state.get('max_file_content', 2000))
            
            # Get documentation summary (just file names, not content)
            doc_summary = get_documentation_summary()
            
            # Check what types of files we have
            has_gold_logs = bool(st.session_state.uploaded_files.get('gold_logs'))
            has_documentation = bool(st.session_state.uploaded_files.get('documentation'))
            
            # Build context-aware prompt
            comparison_text = " Compare problem logs against gold standard logs where available." if has_gold_logs else " Focus on identifying failure patterns in the problem logs."
            doc_text = " Use your Knowledge Base (user guides, troubleshooting guides, design docs) as the primary reference." + (" The user has also uploaded supplemental documentation files for additional context." if has_documentation else "")
            visual_text = " Include visual analysis of any images in the supplemental documentation." if include_visual_analysis and has_documentation else ""
            
            # Create user-friendly display message
            num_logs = len(log_files)
            log_type = "log file" if num_logs == 1 else "log files"
            display_message = f"Run full diagnosis on {num_logs} uploaded {log_type}"
            if has_gold_logs:
                display_message += " (comparing against gold standard)"
            
            # Create full technical prompt for the agent
            base_prompt = f"Please perform a comprehensive instrument diagnosis. ANALYZE ONLY the LOG FILES below using {analysis_mode.lower()} mode with {confidence_threshold} confidence threshold.{comparison_text}{doc_text}{visual_text} Provide pass/fail determination with detailed analysis and recommendations. IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols. Do NOT use markdown headers (# ## ###) - use bold text (**text**) for emphasis instead."
            prompt = base_prompt + doc_summary + log_contents
            
            # Show user-friendly message in chat, but send full prompt to agent
            st.session_state.messages.append({"role": "user", "content": display_message, "avatar": HUMAN_AVATAR})
            st.session_state.pending_prompt = prompt
            st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about instrument diagnosis, upload files, or request specific analysis..."):
        if not agent_arn:
            st.error("Please select an agent in the sidebar first.")
            return

        # Include ONLY log files for analysis (not documentation)
        log_files = get_log_files_only()
        log_contents = process_uploaded_files(log_files, st.session_state, st.session_state.get('max_file_content', 2000))
        
        # Get documentation summary (just file names, not content)
        doc_summary = get_documentation_summary()
        
        # Add ASCII-only instruction to user prompts
        ascii_instruction = " IMPORTANT: Please respond using only ASCII characters - no emojis or Unicode symbols."
        full_prompt = prompt + ascii_instruction + doc_summary + log_contents
        
        # Add user message to chat history (show only the user's text)
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "avatar": HUMAN_AVATAR}
        )
        st.session_state.pending_prompt = full_prompt
        with st.chat_message("user", avatar=HUMAN_AVATAR):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant", avatar=AI_AVATAR):
            full_response = stream_agent_response(
                prompt, agent_arn, st.session_state.runtime_session_id, region, show_tools, show_thinking
            )

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response, "avatar": AI_AVATAR}
        )


if __name__ == "__main__":
    main()
