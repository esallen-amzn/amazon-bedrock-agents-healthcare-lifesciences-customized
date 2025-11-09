import json
import logging
import os
import re
import subprocess
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
    initial_sidebar_state="expanded",
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

def get_all_uploaded_files():
    """Get all uploaded files from session state as a single list"""
    all_files = []
    if 'uploaded_files' in st.session_state:
        for file_list in st.session_state.uploaded_files.values():
            if file_list:
                all_files.extend(file_list)
    return all_files


def process_uploaded_files(uploaded_files, max_content_length: int = 2000) -> str:
    """Process uploaded files and return their contents as text, with smart truncation for large files"""
    if not uploaded_files:
        return ""
    
    def clean_unicode_text(text):
        """Properly clean Unicode characters from text to prevent encoding issues"""
        if isinstance(text, str):
            try:
                # Direct character-by-character approach
                cleaned = ''.join(char if ord(char) < 128 else '?' for char in text)
                return cleaned
            except (UnicodeError, ValueError):
                # Fallback approach
                return text.encode('ascii', 'replace').decode('ascii')
        return text
    
    file_contents = []
    file_contents.append(f"\n=== UPLOADED FILES ({len(uploaded_files)} files) ===")
    
    for file in uploaded_files:
        # Clean filename to avoid Unicode issues
        clean_filename = clean_unicode_text(file.name)
        file_contents.append(f"\n--- FILE: {clean_filename} ({file.size} bytes) ---")
        
        try:
            # Read file content based on type
            if file.type == "text/plain" or file.name.endswith(('.txt', '.log', '.csv')):
                # Text files - with smart truncation
                content = file.read().decode('utf-8')
                # Clean Unicode characters from file content
                content = clean_unicode_text(content)
                
                if len(content) > max_content_length:
                    # For large files, provide a summary approach
                    lines = content.split('\n')
                    total_lines = len(lines)
                    
                    if total_lines > 50:
                        # Include first 15 lines and last 15 lines only
                        first_part = '\n'.join(lines[:15])
                        last_part = '\n'.join(lines[-15:])
                        
                        # Try to extract key information from the middle
                        error_lines = [line for line in lines if any(keyword in line.lower() 
                                     for keyword in ['error', 'fail', 'exception', 'warning', 'critical'])]
                        
                        summary_info = f"File Statistics: {total_lines} total lines, {len(content)} characters"
                        if error_lines:
                            summary_info += f", {len(error_lines)} lines with errors/warnings"
                            # Include up to 5 error lines as examples
                            error_sample = '\n'.join(error_lines[:5])
                            if len(error_lines) > 5:
                                error_sample += f"\n[... and {len(error_lines) - 5} more error lines]"
                        
                        truncated_content = f"{first_part}\n\n[SUMMARY: {summary_info}]\n"
                        if error_lines:
                            truncated_content += f"\n[KEY ERROR SAMPLES]:\n{error_sample}\n"
                        truncated_content += f"\n[TRUNCATED: {total_lines - 30} middle lines omitted]\n\n{last_part}"
                        
                        file_contents.append(f"LOG CONTENT (intelligently truncated):\n{truncated_content}")
                    else:
                        # For smaller files, just truncate the content
                        truncated_content = content[:max_content_length] + f"\n\n[TRUNCATED: {len(content) - max_content_length} characters omitted]"
                        file_contents.append(f"LOG CONTENT (truncated):\n{truncated_content}")
                else:
                    file_contents.append(f"LOG CONTENT:\n{content}")
                    
            elif file.type == "application/json" or file.name.endswith('.json'):
                # JSON files - with truncation
                content = file.read().decode('utf-8')
                # Clean Unicode characters from JSON content
                content = clean_unicode_text(content)
                if len(content) > max_content_length:
                    truncated_content = content[:max_content_length] + f"\n[TRUNCATED: {len(content) - max_content_length} characters omitted]"
                    file_contents.append(f"JSON Content (truncated):\n{truncated_content}")
                else:
                    file_contents.append(f"JSON Content:\n{content}")
                    
            elif file.type.startswith('image/'):
                # Image files - just note that they're uploaded
                file_contents.append(f"[IMAGE FILE: {file.name} - {file.size} bytes - Available for visual analysis]")
            else:
                # Other files - try to read as text with truncation
                try:
                    content = file.read().decode('utf-8')
                    # Clean Unicode characters from content
                    content = clean_unicode_text(content)
                    if len(content) > max_content_length:
                        truncated_content = content[:max_content_length] + f"\n[TRUNCATED: {len(content) - max_content_length} characters omitted]"
                        file_contents.append(f"CONTENT (truncated):\n{truncated_content}")
                    else:
                        file_contents.append(f"CONTENT:\n{content}")
                except UnicodeDecodeError:
                    file_contents.append(f"[BINARY FILE: {file.name} - {file.size} bytes - Cannot display content]")
        except Exception as e:
            file_contents.append(f"[ERROR reading {file.name}: {str(e)}]")
        
        # Reset file pointer for potential re-reading
        file.seek(0)
    
    file_contents.append("\n=== END OF UPLOADED FILES ===\n")
    result = "\n".join(file_contents)
    # Final cleaning of the entire file contents string
    return clean_unicode_text(result)


def fetch_agent_runtimes(region: str = "us-east-1") -> List[Dict]:
    """Fetch available agent runtimes from bedrock-agentcore-control"""
    try:
        client = boto3.client(
            "bedrock-agentcore-control", 
            region_name=region,
            config=boto3.session.Config(
                read_timeout=60,
                connect_timeout=30,
                retries={'max_attempts': 3}
            )
        )
        response = client.list_agent_runtimes(maxResults=100)

        # Filter only READY agents and sort by name
        ready_agents = [
            agent
            for agent in response.get("agentRuntimes", [])
            if agent.get("status") == "READY"
        ]

        # Sort by most recent update time (newest first)
        ready_agents.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)

        return ready_agents
    except Exception as e:
        st.error(f"Error fetching agent runtimes: {e}")
        return []


def fetch_agent_runtime_versions(
    agent_runtime_id: str, region: str = "us-east-1"
) -> List[Dict]:
    """Fetch versions for a specific agent runtime"""
    try:
        client = boto3.client(
            "bedrock-agentcore-control", 
            region_name=region,
            config=boto3.session.Config(
                read_timeout=60,
                connect_timeout=30,
                retries={'max_attempts': 3}
            )
        )
        response = client.list_agent_runtime_versions(agentRuntimeId=agent_runtime_id)

        # Filter only READY versions
        ready_versions = [
            version
            for version in response.get("agentRuntimes", [])
            if version.get("status") == "READY"
        ]

        # Sort by most recent update time (newest first)
        ready_versions.sort(key=lambda x: x.get("lastUpdatedAt", ""), reverse=True)

        return ready_versions
    except Exception as e:
        st.error(f"Error fetching agent runtime versions: {e}")
        return []


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

    # Handle section headers
    text = re.sub(r"\n([A-Za-z][A-Za-z\s]{2,30}):\s*\n", r"\n**\1:**\n\n", text)

    # Clean up multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean up thinking

    if not show_thinking:
        text = re.sub(r"<thinking>.*?</thinking>", "", text)

    return text.strip()


def extract_text_from_response(data) -> str:
    """Extract text content from response data in various formats"""
    if isinstance(data, dict):
        # Handle format: {'role': 'assistant', 'content': [{'text': 'Hello!'}]}
        if "role" in data and "content" in data:
            content = data["content"]
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    return str(content[0]["text"])
                else:
                    return str(content[0])
            elif isinstance(content, str):
                return content
            else:
                return str(content)

        # Handle other common formats
        if "text" in data:
            return str(data["text"])
        elif "content" in data:
            content = data["content"]
            if isinstance(content, str):
                return content
            else:
                return str(content)
        elif "message" in data:
            return str(data["message"])
        elif "response" in data:
            return str(data["response"])
        elif "result" in data:
            return str(data["result"])

    return str(data)


def parse_streaming_chunk(chunk: str) -> str:
    """Parse individual streaming chunk and extract meaningful content"""
    logger.debug(f"parse_streaming_chunk: received chunk: {chunk}")
    logger.debug(f"parse_streaming_chunk: chunk type: {type(chunk)}")

    try:
        # Try to parse as JSON first
        if chunk.strip().startswith("{"):
            logger.debug("parse_streaming_chunk: Attempting JSON parse")
            data = json.loads(chunk)
            logger.debug(f"parse_streaming_chunk: Successfully parsed JSON: {data}")

            # Handle the specific format: {'role': 'assistant', 'content': [{'text': '...'}]}
            if isinstance(data, dict) and "role" in data and "content" in data:
                content = data["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_item = content[0]
                    if isinstance(first_item, dict) and "text" in first_item:
                        extracted_text = first_item["text"]
                        logger.debug(
                            f"parse_streaming_chunk: Extracted text: {extracted_text}"
                        )
                        return extracted_text
                    else:
                        return str(first_item)
                else:
                    return str(content)
            else:
                # Use the general extraction function for other formats
                return extract_text_from_response(data)

        # If not JSON, return the chunk as-is
        logger.debug("parse_streaming_chunk: Not JSON, returning as-is")
        return chunk
    except json.JSONDecodeError as e:
        logger.error(f"parse_streaming_chunk: JSON decode error: {e}")

        # Try to handle Python dict string representation (with single quotes)
        if chunk.strip().startswith("{") and "'" in chunk:
            logger.debug(
                "parse_streaming_chunk: Attempting to handle Python dict string"
            )
            try:
                # Try to convert single quotes to double quotes for JSON parsing
                # This is a simple approach - might need refinement for complex cases
                json_chunk = chunk.replace("'", '"')
                data = json.loads(json_chunk)
                logger.debug(
                    f"parse_streaming_chunk: Successfully converted and parsed: {data}"
                )

                # Handle the specific format
                if isinstance(data, dict) and "role" in data and "content" in data:
                    content = data["content"]
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict) and "text" in first_item:
                            extracted_text = first_item["text"]
                            logger.debug(
                                f"parse_streaming_chunk: Extracted text from converted dict: {extracted_text}"
                            )
                            return extracted_text
                        else:
                            return str(first_item)
                    else:
                        return str(content)
                else:
                    return extract_text_from_response(data)
            except json.JSONDecodeError:
                logger.debug(
                    "parse_streaming_chunk: Failed to convert Python dict string"
                )
                pass

        # If all parsing fails, return the chunk as-is
        logger.debug("parse_streaming_chunk: All parsing failed, returning chunk as-is")
        return chunk


def main():
    # Clean any Unicode characters from session state first
    clean_session_state_unicode()
    
    st.logo("static/agentcore-service-icon.png", size="large")
    st.title("🔧 Instrument Diagnosis Assistant")
    
    # Add file upload section at the top
    st.markdown("### 📁 Upload Files for Analysis")
    
    # Create tabs for different file types
    tab1, tab2, tab3 = st.tabs(["📊 Log Files", "📋 Documentation", "🔍 Troubleshooting Guides"])
    
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
        st.markdown("**Upload engineering documentation and component specifications**")
        engineering_docs = st.file_uploader(
            "Engineering Documents",
            type=['pdf', 'doc', 'docx', 'txt', 'md'],
            accept_multiple_files=True,
            key="eng_docs",
            help="Upload component specifications, system architecture docs, etc."
        )
    
    with tab3:
        st.markdown("**Upload troubleshooting guides with images and diagrams**")
        troubleshooting_guides = st.file_uploader(
            "Troubleshooting Guides",
            type=['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="trouble_guides",
            help="Upload multi-modal troubleshooting documentation"
        )
    
    # Store uploaded files in session state
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {
            'gold_logs': [],
            'failed_logs': [],
            'eng_docs': [],
            'trouble_guides': []
        }
    
    # Update session state with uploaded files
    if gold_standard_logs:
        st.session_state.uploaded_files['gold_logs'] = gold_standard_logs
    if failed_unit_logs:
        st.session_state.uploaded_files['failed_logs'] = failed_unit_logs
    if engineering_docs:
        st.session_state.uploaded_files['eng_docs'] = engineering_docs
    if troubleshooting_guides:
        st.session_state.uploaded_files['trouble_guides'] = troubleshooting_guides
    
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
                    'eng_docs': 'Engineering Docs',
                    'trouble_guides': 'Troubleshooting Guides'
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

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")

        # Region selection (moved up since it affects agent fetching)
        region = st.selectbox(
            "AWS Region",
            ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            index=0,
        )

        # Agent selection
        st.subheader("Agent Selection")

        # Fetch available agents
        with st.spinner("Loading available agents..."):
            available_agents = fetch_agent_runtimes(region)

        if available_agents:
            # Get unique agent names and their runtime IDs
            unique_agents = {}
            for agent in available_agents:
                name = agent.get("agentRuntimeName", "Unknown")
                runtime_id = agent.get("agentRuntimeId", "")
                if name not in unique_agents:
                    unique_agents[name] = runtime_id

            # Create agent name options
            agent_names = list(unique_agents.keys())

            # Agent name selection dropdown
            col1, col2 = st.columns([2, 1])

            with col1:
                selected_agent_name = st.selectbox(
                    "Agent Name",
                    options=agent_names,
                    help="Choose an agent to chat with",
                )

            # Get versions for the selected agent using the specific API
            if selected_agent_name and selected_agent_name in unique_agents:
                agent_runtime_id = unique_agents[selected_agent_name]

                with st.spinner("Loading versions..."):
                    agent_versions = fetch_agent_runtime_versions(
                        agent_runtime_id, region
                    )

                if agent_versions:
                    version_options = []
                    version_arn_map = {}

                    for version in agent_versions:
                        version_num = version.get("agentRuntimeVersion", "Unknown")
                        arn = version.get("agentRuntimeArn", "")
                        updated = version.get("lastUpdatedAt", "")
                        description = version.get("description", "")

                        # Format version display with update time
                        version_display = f"v{version_num}"
                        if updated:
                            try:
                                if hasattr(updated, "strftime"):
                                    updated_str = updated.strftime("%m/%d %H:%M")
                                    version_display += f" ({updated_str})"
                            except:
                                pass

                        version_options.append(version_display)
                        version_arn_map[version_display] = {
                            "arn": arn,
                            "description": description,
                        }

                    with col2:
                        selected_version = st.selectbox(
                            "Version",
                            options=version_options,
                            help="Choose the version to use",
                        )

                    # Get the ARN for the selected agent and version
                    version_info = version_arn_map.get(selected_version, {})
                    agent_arn = version_info.get("arn", "")
                    description = version_info.get("description", "")

                    # Show selected agent info
                    if agent_arn:
                        st.info(f"Selected: {selected_agent_name} {selected_version}")
                        if description:
                            st.caption(f"Description: {description}")
                        with st.expander("View ARN"):
                            st.code(agent_arn)
                else:
                    st.warning(f"No versions found for {selected_agent_name}")
                    agent_arn = ""
            else:
                agent_arn = ""
        else:
            st.error("No agent runtimes found or error loading agents")
            agent_arn = ""

            # Fallback manual input
            st.subheader("Manual ARN Input")
            agent_arn = st.text_input(
                "Agent ARN", value="", help="Enter your Bedrock AgentCore ARN manually"
            )
        if st.button("Refresh", key="refresh_agents", help="Refresh agent list"):
            st.rerun()

        # Runtime Session ID
        st.subheader("Session Configuration")

        # Initialize session ID in session state if not exists
        if "runtime_session_id" not in st.session_state:
            st.session_state.runtime_session_id = str(uuid.uuid4())

        # Session ID input with generate button
        runtime_session_id = st.text_input(
            "Runtime Session ID",
            value=st.session_state.runtime_session_id,
            help="Unique identifier for this runtime session",
        )

        if st.button("Refresh", help="Generate new session ID and clear chat"):
            st.session_state.runtime_session_id = str(uuid.uuid4())
            st.session_state.messages = []  # Clear chat messages when resetting session
            st.rerun()

        # Update session state if user manually changed the ID
        if runtime_session_id != st.session_state.runtime_session_id:
            st.session_state.runtime_session_id = runtime_session_id

        # Diagnosis-specific options
        st.subheader("🔧 Diagnosis Options")
        
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Comprehensive Analysis", "Quick Diagnosis", "Component Focus", "Log Comparison Only"],
            help="Choose the type of analysis to perform"
        )
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.5,
            max_value=0.95,
            value=0.75,
            step=0.05,
            help="Minimum confidence level for diagnosis decisions"
        )
        
        include_visual_analysis = st.checkbox(
            "Include Visual Analysis",
            value=True,
            help="Analyze images and diagrams in troubleshooting guides"
        )
        
        # File processing options
        st.subheader("📁 File Processing")
        
        file_processing_mode = st.selectbox(
            "File Processing Mode",
            ["Smart Truncation (Recommended)", "Minimal Content", "Summary Only"],
            help="How to handle large files to prevent processing issues"
        )
        
        # Set max content length based on mode
        if file_processing_mode == "Smart Truncation (Recommended)":
            max_file_content = 2000
        elif file_processing_mode == "Minimal Content":
            max_file_content = 1000
        else:  # Summary Only
            max_file_content = 500
    
        # Store max_file_content in session state for use throughout the app
        st.session_state.max_file_content = max_file_content
        
        # Response formatting options
        st.subheader("Display Options")
        auto_format = st.checkbox(
            "Auto-format responses",
            value=True,
            help="Automatically clean and format responses",
        )
        show_raw = st.checkbox(
            "Show raw response",
            value=False,
            help="Display the raw unprocessed response",
        )
        show_tools = st.checkbox(
            "Show tools",
            value=True,
            help="Display tools used",
        )
        show_thinking = st.checkbox(
            "Show thinking",
            value=False,
            help="Display the AI thinking text",
        )

        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

        # Connection status
        st.divider()
        if agent_arn:
            st.success("✅ Agent selected")
            
            # Check agent status
            if st.button("Check Agent Status"):
                with st.spinner("Checking agent status..."):
                    try:
                        status_result = subprocess.run(
                            ["agentcore", "status"],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            encoding='utf-8',
                            errors='replace',
                            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                        )
                        
                        if status_result.returncode == 0:
                            status_output = status_result.stdout
                            if "Deploying" in status_output:
                                st.warning("Agent is still deploying. Please wait a few minutes.")
                            elif "ExpiredTokenException" in status_output or "ExpiredToken" in status_output:
                                st.error("AWS credentials expired. Please refresh your credentials.")
                            elif "Unknown" in status_output and "Endpoint" in status_output:
                                st.warning("Agent endpoint not ready. Deployment may still be in progress.")
                            elif "READY" in status_output or "ready" in status_output.lower():
                                st.success("✅ Agent is ready and available!")
                            else:
                                st.info("Agent status unclear. Check the debug info below.")
                        else:
                            st.error(f"Could not check agent status (exit code: {status_result.returncode})")
                            
                    except Exception as e:
                        st.error(f"Error checking agent status: {str(e)}")
        else:
            st.error("Please select an agent")
        
        # Debug section
        if st.checkbox("Show Debug Info", value=False):
            st.subheader("Debug Information")
            st.write(f"**Agent ARN:** {agent_arn}")
            st.write(f"**Session ID:** {runtime_session_id}")
            st.write(f"**Region:** {region}")
            
            # Show recent log messages
            if st.button("Show Recent Logs"):
                import logging
                # This is a simple way to show logs - in production you'd want a proper log viewer
                st.text("Check the console/terminal for detailed logs")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Diagnosis Results Display Section
    if 'diagnosis_results' in st.session_state and st.session_state.diagnosis_results:
        st.markdown("### Latest Diagnosis Results")
        
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
                message_placeholder = st.empty()
                chunk_buffer = ""

                try:
                    # Stream the response
                    for chunk in invoke_agent_streaming(
                        prompt,
                        agent_arn,
                        st.session_state.runtime_session_id,
                        region,
                        show_tools,
                    ):
                        # Let's see what we get
                        logger.debug(f"MAIN LOOP: chunk type: {type(chunk)}")
                        logger.debug(f"MAIN LOOP: chunk content: {chunk}")

                        # Ensure chunk is a string before concatenating
                        if not isinstance(chunk, str):
                            logger.debug(
                                f"MAIN LOOP: Converting non-string chunk to string"
                            )
                            chunk = str(chunk)

                        # Add chunk to buffer
                        chunk_buffer += chunk

                        # Only update display every few chunks or when we hit certain characters
                        if (
                            len(chunk_buffer) % 3 == 0
                            or chunk.endswith(" ")
                            or chunk.endswith("\n")
                        ):
                            if auto_format:
                                # Clean the accumulated response
                                cleaned_response = clean_response_text(
                                    chunk_buffer, show_thinking
                                )
                                message_placeholder.markdown(cleaned_response + " |")
                            else:
                                # Show raw response
                                message_placeholder.markdown(chunk_buffer + " |")
                        # nosemgrep sleep to wait for resources
                        time.sleep(0.01)  # Reduced delay since we're batching updates

                    # Final response without cursor
                    if auto_format:
                        full_response = clean_response_text(chunk_buffer, show_thinking)
                    else:
                        full_response = chunk_buffer

                    message_placeholder.markdown(full_response)

                    # Show raw response in expander if requested
                    if show_raw and auto_format:
                        with st.expander("View raw response"):
                            st.text(chunk_buffer)

                except Exception as e:
                    error_msg = f"**Error:** {str(e)}"
                    message_placeholder.markdown(error_msg)
                    full_response = error_msg

            # Add assistant response to chat history
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response, "avatar": AI_AVATAR}
            )

    # Quick action buttons
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Analyze Logs"):
            if not agent_arn:
                st.error("Please select an agent in the sidebar first.")
            elif not st.session_state.uploaded_files.get('failed_logs'):
                st.error("Please upload problem unit logs first. Gold standard logs are optional.")
            else:
                # Include uploaded file contents
                uploaded_files = get_all_uploaded_files()
                file_contents = process_uploaded_files(uploaded_files, st.session_state.get('max_file_content', 2000))
                # Check if we have gold standard logs for comparison
                has_gold_logs = bool(st.session_state.uploaded_files.get('gold_logs'))
                comparison_text = " Compare against the gold standard logs to identify deviations." if has_gold_logs else " Analyze for common failure patterns and anomalies."
                
                base_prompt = f"Please analyze the uploaded log files using {analysis_mode.lower()} mode with confidence threshold {confidence_threshold}. Focus on identifying failure patterns, error messages, and anomalies.{comparison_text} Provide a pass/fail determination with confidence level. IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols."
                prompt = base_prompt + file_contents
                st.session_state.messages.append({"role": "user", "content": base_prompt, "avatar": HUMAN_AVATAR})
                st.session_state.pending_prompt = prompt
                st.rerun()
    
    with col2:
        if st.button("🔧 Identify Components"):
            if not agent_arn:
                st.error("Please select an agent in the sidebar first.")
            else:
                # Include uploaded file contents
                uploaded_files = get_all_uploaded_files()
                file_contents = process_uploaded_files(uploaded_files, st.session_state.get('max_file_content', 2000))
                base_prompt = "Please identify all hardware and software components from the uploaded engineering documentation and create a comprehensive inventory. IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols."
                prompt = base_prompt + file_contents
                st.session_state.messages.append({"role": "user", "content": base_prompt, "avatar": HUMAN_AVATAR})
                st.session_state.pending_prompt = prompt
                st.rerun()
    
    with col3:
        if st.button("📚 Process Guides"):
            if not agent_arn:
                st.error("Please select an agent in the sidebar first.")
            else:
                # Include uploaded file contents
                uploaded_files = get_all_uploaded_files()
                file_contents = process_uploaded_files(uploaded_files, st.session_state.get('max_file_content', 2000))
                visual_text = " Include visual analysis of images and diagrams." if include_visual_analysis else ""
                base_prompt = f"Please process the uploaded troubleshooting guides and extract relevant procedures.{visual_text} IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols."
                prompt = base_prompt + file_contents
                st.session_state.messages.append({"role": "user", "content": base_prompt, "avatar": HUMAN_AVATAR})
                st.session_state.pending_prompt = prompt
                st.rerun()
    
    with col4:
        if st.button("🎯 Full Diagnosis"):
            if not agent_arn:
                st.error("Please select an agent in the sidebar first.")
            elif not st.session_state.uploaded_files.get('failed_logs'):
                st.error("Please upload problem unit logs first for diagnosis. Gold standard logs are optional.")
            else:
                # Include uploaded file contents
                uploaded_files = get_all_uploaded_files()
                file_contents = process_uploaded_files(uploaded_files, st.session_state.get('max_file_content', 2000))
                # Check if we have gold standard logs for comparison
                has_gold_logs = bool(st.session_state.uploaded_files.get('gold_logs'))
                comparison_text = " Compare problem logs against gold standard logs where available." if has_gold_logs else " Focus on identifying failure patterns in the problem logs."
                visual_text = " Include visual analysis." if include_visual_analysis else ""
                
                base_prompt = f"Please perform a comprehensive instrument diagnosis using all uploaded files. Use {analysis_mode.lower()} mode with {confidence_threshold} confidence threshold.{comparison_text}{visual_text} Provide pass/fail determination with detailed analysis. IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols."
                prompt = base_prompt + file_contents
                st.session_state.messages.append({"role": "user", "content": base_prompt, "avatar": HUMAN_AVATAR})
                st.session_state.pending_prompt = prompt
                st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about instrument diagnosis, upload files, or request specific analysis..."):
        if not agent_arn:
            st.error("Please select an agent in the sidebar first.")
            return

        # Include uploaded file contents if any
        uploaded_files = get_all_uploaded_files()
        file_contents = process_uploaded_files(uploaded_files, st.session_state.get('max_file_content', 2000))
        
        # Add ASCII-only instruction to user prompts
        ascii_instruction = " IMPORTANT: Please respond using only ASCII characters - no emojis or Unicode symbols."
        full_prompt = prompt + ascii_instruction + file_contents
        
        # Add user message to chat history (show only the user's text)
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "avatar": HUMAN_AVATAR}
        )
        st.session_state.pending_prompt = full_prompt
        with st.chat_message("user", avatar=HUMAN_AVATAR):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant", avatar=AI_AVATAR):
            message_placeholder = st.empty()
            chunk_buffer = ""

            try:
                # Stream the response
                for chunk in invoke_agent_streaming(
                    prompt,
                    agent_arn,
                    st.session_state.runtime_session_id,
                    region,
                    show_tools,
                ):
                    # Let's see what we get
                    logger.debug(f"MAIN LOOP: chunk type: {type(chunk)}")
                    logger.debug(f"MAIN LOOP: chunk content: {chunk}")

                    # Ensure chunk is a string before concatenating
                    if not isinstance(chunk, str):
                        logger.debug(
                            f"MAIN LOOP: Converting non-string chunk to string"
                        )
                        chunk = str(chunk)

                    # Add chunk to buffer
                    chunk_buffer += chunk

                    # Only update display every few chunks or when we hit certain characters
                    if (
                        len(chunk_buffer) % 3 == 0
                        or chunk.endswith(" ")
                        or chunk.endswith("\n")
                    ):
                        if auto_format:
                            # Clean the accumulated response
                            cleaned_response = clean_response_text(
                                chunk_buffer, show_thinking
                            )
                            message_placeholder.markdown(cleaned_response + " |")
                        else:
                            # Show raw response
                            message_placeholder.markdown(chunk_buffer + " |")
                    # nosemgrep sleep to wait for resources
                    time.sleep(0.01)  # Reduced delay since we're batching updates

                # Final response without cursor
                if auto_format:
                    full_response = clean_response_text(chunk_buffer, show_thinking)
                else:
                    full_response = chunk_buffer

                message_placeholder.markdown(full_response)

                # Show raw response in expander if requested
                if show_raw and auto_format:
                    with st.expander("View raw response"):
                        st.text(chunk_buffer)

            except Exception as e:
                error_msg = f"**Error:** {str(e)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response, "avatar": AI_AVATAR}
        )


if __name__ == "__main__":
    main()
