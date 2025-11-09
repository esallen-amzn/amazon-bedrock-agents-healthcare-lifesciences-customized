"""
S3 Storage Tools for Instrument Diagnosis Assistant

These tools handle S3 upload, retrieval, and management of log files with
session-based organization, presigned URLs, and metadata tracking.
"""

import os
import boto3
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from strands import tool
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class S3LogMetadata:
    """Metadata for S3-stored log files"""
    s3_uri: str
    bucket: str
    key: str
    file_name: str
    file_size: int
    upload_timestamp: str
    session_id: str
    content_type: str
    presigned_url: Optional[str] = None
    etag: Optional[str] = None


class S3StorageManager:
    """Manages S3 storage operations for log files"""
    
    def __init__(self, bucket_name: str = None, region: str = "us-east-1"):
        """
        Initialize S3 storage manager.
        
        Args:
            bucket_name: S3 bucket name (will try to get from SSM if not provided)
            region: AWS region
        """
        from botocore.config import Config
        
        self.region = region
        
        # Configure boto3 clients with extended timeouts for large file operations
        boto_config = Config(
            region_name=region,
            read_timeout=300,  # 5 minutes for large file reads
            connect_timeout=60,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        self.s3_client = boto3.client('s3', config=boto_config)
        self.ssm_client = boto3.client('ssm', config=boto_config)
        
        # Get bucket name from SSM if not provided
        if not bucket_name:
            try:
                response = self.ssm_client.get_parameter(
                    Name='/app/myapp/s3/bucket_name'
                )
                self.bucket_name = response['Parameter']['Value']
            except Exception as e:
                logger.warning(f"Could not get bucket name from SSM: {e}")
                self.bucket_name = f"instrument-diagnosis-logs-{boto3.client('sts').get_caller_identity()['Account']}"
        else:
            self.bucket_name = bucket_name
        
        logger.info(f"S3StorageManager initialized with bucket: {self.bucket_name}")
    
    def validate_file(self, file_path: str, max_size_mb: int = 500, 
                     allowed_extensions: List[str] = None) -> tuple[bool, str]:
        """
        Validate file before upload.
        
        Args:
            file_path: Path to file to validate
            max_size_mb: Maximum file size in MB
            allowed_extensions: List of allowed file extensions
        
        Returns:
            Tuple of (is_valid, message)
        """
        if allowed_extensions is None:
            allowed_extensions = ['.log', '.txt', '.csv', '.out', '.err']
        
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_size_mb}MB)"
            
            # Check extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                return False, f"Invalid file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            
            # Check if file is readable
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
            
            return True, "File validation passed"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    def generate_s3_key(self, session_id: str, file_name: str, prefix: str = "sessions") -> str:
        """
        Generate S3 key with session-based organization.
        
        Args:
            session_id: Unique session identifier
            file_name: Original file name
            prefix: S3 prefix for organization
        
        Returns:
            S3 key string
        """
        # Sanitize file name
        safe_filename = "".join(c for c in file_name if c.isalnum() or c in ('_', '-', '.'))
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        return f"{prefix}/{session_id}/logs/{timestamp}_{safe_filename}"
    
    def upload_file(self, file_path: str, session_id: str, 
                   metadata: Dict[str, str] = None) -> S3LogMetadata:
        """
        Upload file to S3 with streaming.
        
        Args:
            file_path: Path to file to upload
            session_id: Session identifier
            metadata: Additional metadata to store with file
        
        Returns:
            S3LogMetadata object with upload details
        """
        try:
            # Validate file
            is_valid, msg = self.validate_file(file_path)
            if not is_valid:
                raise ValueError(msg)
            
            # Generate S3 key
            file_name = os.path.basename(file_path)
            s3_key = self.generate_s3_key(session_id, file_name)
            
            # Prepare metadata
            file_size = os.path.getsize(file_path)
            content_type = self._get_content_type(file_name)
            
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256',
                'Metadata': {
                    'session-id': session_id,
                    'original-filename': file_name,
                    'upload-timestamp': datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            }
            
            # Upload file
            logger.info(f"Uploading {file_name} to s3://{self.bucket_name}/{s3_key}")
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Get ETag
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            etag = response.get('ETag', '').strip('"')
            
            # Create metadata object
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            metadata_obj = S3LogMetadata(
                s3_uri=s3_uri,
                bucket=self.bucket_name,
                key=s3_key,
                file_name=file_name,
                file_size=file_size,
                upload_timestamp=datetime.utcnow().isoformat(),
                session_id=session_id,
                content_type=content_type,
                etag=etag
            )
            
            logger.info(f"Successfully uploaded {file_name} to {s3_uri}")
            return metadata_obj
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for temporary access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download file from S3 to local path.
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading s3://{self.bucket_name}/{s3_key} to {local_path}")
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except Exception as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False
    
    def stream_file_content(self, s3_key: str, chunk_size: int = 8192) -> str:
        """
        Stream file content from S3.
        
        Args:
            s3_key: S3 object key
            chunk_size: Size of chunks to read
        
        Returns:
            File content as string
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8', errors='ignore')
            return content
        except Exception as e:
            logger.error(f"Error streaming file from S3: {str(e)}")
            raise
    
    def list_session_files(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all files for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of file metadata dictionaries
        """
        try:
            prefix = f"sessions/{session_id}/logs/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'file_name': os.path.basename(obj['Key'])
                })
            
            return files
        except Exception as e:
            logger.error(f"Error listing session files: {str(e)}")
            return []
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def _get_content_type(self, file_name: str) -> str:
        """Determine content type from file extension"""
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            '.log': 'text/plain',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.out': 'text/plain',
            '.err': 'text/plain'
        }
        return content_types.get(ext, 'application/octet-stream')


# Global storage manager instance
_storage_manager = None


def get_storage_manager() -> S3StorageManager:
    """Get or create global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = S3StorageManager()
    return _storage_manager


@tool(
    name="upload_log_to_s3",
    description="Upload a log file to S3 storage with session-based organization. Returns S3 URI and metadata for the uploaded file."
)
def upload_log_to_s3(
    file_path: str,
    session_id: str,
    file_description: str = ""
) -> Dict[str, Any]:
    """
    Upload log file to S3 storage.
    
    Args:
        file_path: Path to the log file to upload
        session_id: Unique session identifier for organizing files
        file_description: Optional description of the file
    
    Returns:
        Dictionary containing S3 URI, metadata, and upload status
    """
    try:
        storage_manager = get_storage_manager()
        
        # Prepare metadata
        metadata = {}
        if file_description:
            metadata['description'] = file_description
        
        # Upload file
        s3_metadata = storage_manager.upload_file(file_path, session_id, metadata)
        
        # Generate presigned URL for temporary access
        presigned_url = storage_manager.generate_presigned_url(s3_metadata.key)
        s3_metadata.presigned_url = presigned_url
        
        result = {
            'success': True,
            'message': f"Successfully uploaded {s3_metadata.file_name} to S3",
            's3_uri': s3_metadata.s3_uri,
            'bucket': s3_metadata.bucket,
            'key': s3_metadata.key,
            'file_name': s3_metadata.file_name,
            'file_size': s3_metadata.file_size,
            'file_size_mb': round(s3_metadata.file_size / (1024 * 1024), 2),
            'upload_timestamp': s3_metadata.upload_timestamp,
            'session_id': s3_metadata.session_id,
            'presigned_url': presigned_url,
            'presigned_url_expires': '1 hour'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in upload_log_to_s3: {str(e)}")
        return {
            'success': False,
            'error': f"Upload failed: {str(e)}"
        }


@tool(
    name="get_s3_file_content",
    description="Retrieve log file content from S3 storage by streaming. Use this to access uploaded log files for analysis."
)
def get_s3_file_content(
    s3_uri: str = "",
    s3_key: str = "",
    max_size_mb: int = 50
) -> Dict[str, Any]:
    """
    Retrieve log file content from S3.
    
    Args:
        s3_uri: S3 URI (s3://bucket/key) - provide either this or s3_key
        s3_key: S3 object key - provide either this or s3_uri
        max_size_mb: Maximum file size to retrieve in MB
    
    Returns:
        Dictionary containing file content and metadata
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI if provided
        if s3_uri:
            if not s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format. Must start with s3://'}
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            bucket, key = parts
            if bucket != storage_manager.bucket_name:
                return {'error': f'Bucket mismatch. Expected: {storage_manager.bucket_name}'}
            s3_key = key
        
        if not s3_key:
            return {'error': 'Either s3_uri or s3_key must be provided'}
        
        # Check file size before downloading
        try:
            response = storage_manager.s3_client.head_object(
                Bucket=storage_manager.bucket_name,
                Key=s3_key
            )
            file_size = response['ContentLength']
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                return {
                    'error': f'File too large: {file_size / (1024*1024):.1f}MB (max: {max_size_mb}MB)',
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'suggestion': 'Use extract_s3_log_summary for large files'
                }
        except ClientError as e:
            return {'error': f'File not found or access denied: {str(e)}'}
        
        # Stream file content
        content = storage_manager.stream_file_content(s3_key)
        
        return {
            'success': True,
            'content': content,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            's3_key': s3_key,
            's3_uri': f"s3://{storage_manager.bucket_name}/{s3_key}"
        }
        
    except Exception as e:
        logger.error(f"Error in get_s3_file_content: {str(e)}")
        return {'error': f'Failed to retrieve file content: {str(e)}'}


@tool(
    name="list_session_logs",
    description="List all log files uploaded for a specific session. Use this to discover available files for analysis."
)
def list_session_logs(session_id: str) -> Dict[str, Any]:
    """
    List all log files for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dictionary containing list of files and session information
    """
    try:
        storage_manager = get_storage_manager()
        files = storage_manager.list_session_files(session_id)
        
        if not files:
            return {
                'session_id': session_id,
                'files_found': 0,
                'message': 'No files found for this session',
                'files': []
            }
        
        # Calculate total size
        total_size = sum(f['size'] for f in files)
        
        return {
            'session_id': session_id,
            'files_found': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files': files,
            'message': f'Found {len(files)} log files for session {session_id}'
        }
        
    except Exception as e:
        logger.error(f"Error in list_session_logs: {str(e)}")
        return {'error': f'Failed to list session logs: {str(e)}'}


@tool(
    name="generate_presigned_url",
    description="Generate a temporary presigned URL for accessing an S3-stored log file. Useful for sharing or downloading files."
)
def generate_presigned_url(
    s3_uri: str = "",
    s3_key: str = "",
    expiration_hours: int = 1
) -> Dict[str, Any]:
    """
    Generate presigned URL for S3 file access.
    
    Args:
        s3_uri: S3 URI (s3://bucket/key) - provide either this or s3_key
        s3_key: S3 object key - provide either this or s3_uri
        expiration_hours: URL expiration time in hours (default: 1)
    
    Returns:
        Dictionary containing presigned URL and expiration info
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI if provided
        if s3_uri:
            if not s3_uri.startswith('s3://'):
                return {'error': 'Invalid S3 URI format. Must start with s3://'}
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) != 2:
                return {'error': 'Invalid S3 URI format'}
            bucket, key = parts
            if bucket != storage_manager.bucket_name:
                return {'error': f'Bucket mismatch. Expected: {storage_manager.bucket_name}'}
            s3_key = key
        
        if not s3_key:
            return {'error': 'Either s3_uri or s3_key must be provided'}
        
        # Generate presigned URL
        expiration_seconds = expiration_hours * 3600
        url = storage_manager.generate_presigned_url(s3_key, expiration_seconds)
        
        return {
            'success': True,
            'presigned_url': url,
            's3_key': s3_key,
            's3_uri': f"s3://{storage_manager.bucket_name}/{s3_key}",
            'expires_in_hours': expiration_hours,
            'expires_at': (datetime.utcnow() + timedelta(hours=expiration_hours)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in generate_presigned_url: {str(e)}")
        return {'error': f'Failed to generate presigned URL: {str(e)}'}


# List of S3 storage tools
S3_STORAGE_TOOLS = [
    upload_log_to_s3,
    get_s3_file_content,
    list_session_logs,
    generate_presigned_url
]
