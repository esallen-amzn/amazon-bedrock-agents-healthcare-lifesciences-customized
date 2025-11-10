"""
S3 Integration for Instrument Diagnosis Assistant
Handles file uploads to S3 and session management
"""

import boto3
import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from botocore.config import Config

logger = logging.getLogger(__name__)

# S3 Configuration
S3_BUCKET = "instrument-diagnosis-logs-390402579286"
S3_REGION = "us-east-1"


def upload_files_to_s3(
    uploaded_files: List[Any],
    session_id: str,
    progress_callback: Optional[callable] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Upload files to S3 with session-based organization.
    
    Args:
        uploaded_files: List of Streamlit uploaded file objects
        session_id: Session ID for organizing files
        progress_callback: Optional callback for progress updates
    
    Returns:
        Dictionary mapping filename to file metadata (s3_uri, bucket, key, size, etc.)
    """
    if not uploaded_files:
        return {}
    
    # Configure S3 client with extended timeout
    config = Config(
        read_timeout=300,
        connect_timeout=60,
        retries={'max_attempts': 3}
    )
    
    s3_client = boto3.client('s3', region_name=S3_REGION, config=config)
    file_metadata = {}
    
    for idx, file in enumerate(uploaded_files):
        try:
            if progress_callback:
                progress_callback(idx + 1, len(uploaded_files), file.name)
            
            # Generate S3 key with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            s3_key = f"sessions/{session_id}/logs/{timestamp}_{file.name}"
            
            # Reset file pointer
            file.seek(0)
            file_size = len(file.getvalue())
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=file.getvalue(),
                ContentType=file.type or 'application/octet-stream',
                Metadata={
                    'original-filename': file.name,
                    'upload-timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'session-id': session_id
                }
            )
            
            s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
            
            file_metadata[file.name] = {
                's3_uri': s3_uri,
                'bucket': S3_BUCKET,
                'key': s3_key,
                'file_name': file.name,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'upload_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'session_id': session_id,
                'content_type': file.type or 'application/octet-stream'
            }
            
            logger.info(f"Successfully uploaded {file.name} to {s3_uri}")
            
        except Exception as e:
            logger.error(f"Error uploading file {file.name} to S3: {e}")
            continue
    
    return file_metadata


def update_session_file_registry(session_state: Any, file_metadata: Dict[str, Dict[str, Any]]):
    """
    Update the session registry with new S3 file information.
    
    Args:
        session_state: Streamlit session state object
        file_metadata: Dictionary of file metadata from upload_files_to_s3
    """
    if 'session_file_registry' not in session_state:
        session_state.session_file_registry = {
            'uploaded_files': {},
            'analysis_completed': {},
            'last_analysis_time': None
        }
    
    # Update registry with new S3 files
    for original_name, metadata in file_metadata.items():
        session_state.session_file_registry['uploaded_files'][original_name] = {
            's3_uri': metadata['s3_uri'],
            's3_key': metadata['key'],
            'bucket': metadata['bucket'],
            'size': metadata['file_size'],
            'upload_time': time.time(),
            'analyzed': False
        }


def get_session_context(session_state: Any) -> str:
    """
    Generate session context for the agent with S3 file information.
    
    Args:
        session_state: Streamlit session state object
    
    Returns:
        Formatted string with S3 file information for the prompt
    """
    if 'session_file_registry' not in session_state:
        return ""
    
    registry = session_state.session_file_registry
    uploaded_files = registry.get('uploaded_files', {})
    
    if not uploaded_files:
        return ""
    
    context_parts = []
    context_parts.append("\n" + "="*60)
    context_parts.append("S3 FILES AVAILABLE FOR ANALYSIS")
    context_parts.append("="*60)
    
    for filename, info in uploaded_files.items():
        context_parts.append(f"\nFile: {filename}")
        context_parts.append(f"S3 URI: {info['s3_uri']}")
        context_parts.append(f"Size: {info['size'] / (1024*1024):.2f} MB")
        
        # Provide action based on file size
        if info['size'] > 500 * 1024:  # >500KB
            context_parts.append(f"ACTION: extract_s3_log_summary(s3_uri='{info['s3_uri']}')")
        else:
            context_parts.append(f"ACTION: get_s3_file_content(s3_uri='{info['s3_uri']}')")
    
    context_parts.append("\n" + "="*60)
    context_parts.append("IMPORTANT: Use the S3 tools above to access files")
    context_parts.append("="*60 + "\n")
    
    return '\n'.join(context_parts)


def load_existing_s3_files_for_session(session_state: Any, session_id: str):
    """
    Load previously uploaded S3 files for the current session.
    
    Args:
        session_state: Streamlit session state object
        session_id: Session ID to load files for
    """
    try:
        config = Config(read_timeout=60, connect_timeout=30)
        s3_client = boto3.client('s3', region_name=S3_REGION, config=config)
        
        prefix = f"sessions/{session_id}/logs/"
        
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            return
        
        if 'session_file_registry' not in session_state:
            session_state.session_file_registry = {
                'uploaded_files': {},
                'analysis_completed': {},
                'last_analysis_time': None
            }
        
        for obj in response['Contents']:
            s3_key = obj['Key']
            s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
            
            # Extract original filename
            filename = s3_key.split('/')[-1]
            if '_' in filename:
                # Remove timestamp prefix
                parts = filename.split('_', 2)
                if len(parts) >= 3:
                    original_name = parts[2]
                else:
                    original_name = filename
            else:
                original_name = filename
            
            session_state.session_file_registry['uploaded_files'][original_name] = {
                's3_uri': s3_uri,
                's3_key': s3_key,
                'bucket': S3_BUCKET,
                'size': obj['Size'],
                'upload_time': obj['LastModified'].timestamp(),
                'analyzed': False
            }
            
            logger.info(f"Loaded existing S3 file: {original_name} -> {s3_uri}")
    
    except Exception as e:
        logger.error(f"Error loading existing S3 files: {e}")


def process_uploaded_files(uploaded_files, session_state, max_content_length: int = 2000) -> str:
    """
    Process uploaded files by uploading to S3 and returning S3 URI information for the agent.
    
    Args:
        uploaded_files: List of Streamlit uploaded file objects
        session_state: Streamlit session state object
        max_content_length: Unused (kept for compatibility)
    
    Returns:
        Formatted string with S3 file information and agent instructions
    """
    import streamlit as st
    
    if not uploaded_files:
        # Check if we have files from previous uploads in this session
        session_context = get_session_context(session_state)
        if session_context:
            return session_context
        
        # Try to load existing S3 files for this session
        if 'runtime_session_id' in session_state:
            load_existing_s3_files_for_session(session_state, session_state.runtime_session_id)
            session_context = get_session_context(session_state)
            if session_context:
                return session_context
        
        return ""
    
    # Get session ID from Streamlit session state
    if 'runtime_session_id' not in session_state:
        session_state.runtime_session_id = str(uuid.uuid4())
    session_id = session_state.runtime_session_id
    
    # Create progress callback for upload status
    progress_placeholder = st.empty()
    
    def show_progress(current, total, filename):
        progress_placeholder.info(f"⬆️ Uploading to S3: {filename} ({current}/{total})")
    
    # Upload files to S3 and get metadata
    file_metadata = upload_files_to_s3(uploaded_files, session_id, progress_callback=show_progress)
    
    # Clear progress message
    progress_placeholder.empty()
    
    if not file_metadata:
        return "\n=== NO FILES SUCCESSFULLY UPLOADED TO S3 ===\n"
    
    # Update session registry
    update_session_file_registry(session_state, file_metadata)
    
    # Create action summary with S3 file information
    action_summary = []
    action_summary.append("\n" + "="*60)
    action_summary.append("CRITICAL INSTRUCTION: FILES ARE ALREADY UPLOADED TO S3")
    action_summary.append("DO NOT ASK FOR FILES - USE S3 TOOLS IMMEDIATELY")
    action_summary.append("="*60)
    action_summary.append(f"AGENT ACTION REQUIRED: {len(file_metadata)} S3 FILES READY")
    action_summary.append("="*60)
    
    # Sort files chronologically by upload timestamp (oldest first for timeline analysis)
    sorted_files = sorted(file_metadata.items(), key=lambda x: x[1].get('upload_timestamp', ''))
    
    total_size = sum(meta['file_size'] for meta in file_metadata.values())
    action_summary.append(f"TOTAL SIZE: {total_size / (1024*1024):.2f} MB")
    action_summary.append(f"S3 STORAGE: Files stored with session-based organization")
    action_summary.append("")
    
    # Handle multiple files - analyze chronologically for timeline analysis
    if len(file_metadata) > 1:
        action_summary.append("MULTIPLE LOG FILES DETECTED - CHRONOLOGICAL ANALYSIS REQUIRED")
        action_summary.append("FILES SORTED BY TIMESTAMP: Oldest to newest for timeline analysis")
        action_summary.append("STRATEGY: Analyze each file, then synthesize overall diagnosis across timeline")
        action_summary.append("")
    
    files_processed = 0
    # Show all files for comprehensive analysis (not just first one)
    max_files_to_show = len(file_metadata)
    
    for original_name, metadata in sorted_files:
        file_size = metadata['file_size']
        s3_uri = metadata['s3_uri']
        s3_key = metadata['key']
        
        action_summary.append(f"\n📁 FILE {files_processed + 1}: {original_name}")
        action_summary.append(f"   S3_URI: {s3_uri}")
        action_summary.append(f"   SIZE: {file_size / (1024*1024):.2f} MB")
        
        # Provide S3-based analysis instructions - use summary for files >500KB
        if file_size > 500 * 1024:  # Files > 500KB
            action_summary.append(f"   ⚡ ACTION: extract_s3_log_summary(s3_uri='{s3_uri}')")
            action_summary.append(f"   REASON: File >{file_size / (1024*1024):.1f}MB - MUST use summary for speed")
        else:
            action_summary.append(f"   ⚡ ACTION: get_s3_file_content(s3_uri='{s3_uri}')")
            action_summary.append(f"   REASON: Small file - can retrieve full content")
        
        action_summary.append("")
        
        files_processed += 1
        # CRITICAL: Limit to avoid token limits with multiple large files
        if files_processed >= max_files_to_show:
            remaining_files = len(file_metadata) - files_processed
            if remaining_files > 0:
                action_summary.append(f"[{remaining_files} additional files available - process one at a time]")
                action_summary.append(f"IMPORTANT: Analyze the first file above, then user can request next file")
                action_summary.append(f"Use list_session_logs(session_id='{session_id}') to see all files")
            break
    
    # Add appropriate action based on file count
    action_summary.append("\n" + "="*60)
    action_summary.append("⚡ ANALYSIS STRATEGY:")
    action_summary.append("="*60)
    
    if len(file_metadata) == 1:
        first_file = list(file_metadata.values())[0]
        action_summary.append("SINGLE FILE ANALYSIS:")
        if first_file['file_size'] > 500 * 1024:  # 500KB threshold
            action_summary.append(f"1. Call: extract_s3_log_summary(s3_uri='{first_file['s3_uri']}')")
            action_summary.append(f"2. Analyze the summary for failure patterns and errors")
            action_summary.append(f"3. Provide diagnosis with pass/fail determination and recommendations")
        else:
            action_summary.append(f"1. Call: get_s3_file_content(s3_uri='{first_file['s3_uri']}')")
            action_summary.append(f"2. Analyze the content for failure patterns and errors")
            action_summary.append(f"3. Provide diagnosis with pass/fail determination and recommendations")
    else:
        action_summary.append(f"CHRONOLOGICAL ANALYSIS OF {len(file_metadata)} FILES:")
        action_summary.append("1. For EACH file (in chronological order listed above):")
        action_summary.append("   - If file >500KB: extract_s3_log_summary(s3_uri='...')")
        action_summary.append("   - If file <500KB: get_s3_file_content(s3_uri='...')")
        action_summary.append("   - Note key findings, errors, and patterns")
        action_summary.append("2. SYNTHESIZE findings across all files:")
        action_summary.append("   - Identify progression of issues over time")
        action_summary.append("   - Determine if problems are recurring or evolving")
        action_summary.append("   - Correlate errors across multiple logs")
        action_summary.append("3. Provide OVERALL DIAGNOSIS:")
        action_summary.append("   - Pass/fail determination based on all files")
        action_summary.append("   - Timeline of issues (when did problems start/worsen)")
        action_summary.append("   - Root cause analysis across timeline")
        action_summary.append("   - Prioritized action items to resolve issues")
    
    action_summary.append("")
    action_summary.append("🚫 DO NOT ASK USER TO UPLOAD FILES - THEY ARE ALREADY IN S3")
    action_summary.append("="*60)
    
    return '\n'.join(action_summary)
