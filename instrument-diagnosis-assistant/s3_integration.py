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
