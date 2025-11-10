# S3 Storage Tools

## Overview

The `s3_storage_tools.py` module provides comprehensive S3 storage management for log files with session-based organization, presigned URLs, metadata tracking, and streaming capabilities. It handles file uploads, retrievals, and management operations for the Instrument Diagnosis Assistant.

## Purpose

This module enables:
- Upload log files to S3 with automatic organization
- Session-based file management and organization
- Generate presigned URLs for temporary file access
- Stream file content from S3 without full download
- List and manage session files
- Track file metadata and upload history

## Key Components

### S3LogMetadata (Dataclass)

Represents metadata for S3-stored log files:

- `s3_uri`: Full S3 URI (s3://bucket/key)
- `bucket`: S3 bucket name
- `key`: S3 object key
- `file_name`: Original file name
- `file_size`: File size in bytes
- `upload_timestamp`: ISO format upload timestamp
- `session_id`: Session identifier
- `content_type`: MIME content type
- `presigned_url`: Optional presigned URL for access
- `etag`: S3 ETag for file integrity

### S3StorageManager (Class)

Core S3 storage management engine with extended timeouts for large files.

**Configuration**:
- Read timeout: 300 seconds (5 minutes)
- Connect timeout: 60 seconds
- Retry attempts: 3 with adaptive mode
- Server-side encryption: AES256

### Session-Based Organization

Files are organized in S3 using a hierarchical structure:

```
s3://bucket/
└── sessions/
    └── {session_id}/
        └── logs/
            └── {timestamp}_{filename}
```

**Benefits**:
- Easy session isolation
- Chronological file tracking
- Simple cleanup and archival
- Clear audit trail

**Example S3 Keys**:
```
sessions/session123/logs/20250109_120000_error_log.txt
sessions/session123/logs/20250109_120500_system_log.txt
sessions/session123/analysis/diagnosis_DIAG-session123-20250109120000.json
```

## Available Tools

### 1. upload_log_to_s3

**Description**: Upload a log file to S3 storage with session-based organization. Returns S3 URI and metadata for the uploaded file.

**Parameters**:
- `file_path` (str): Path to the log file to upload
- `session_id` (str): Unique session identifier for organizing files
- `file_description` (str): Optional description of the file

**Returns**: Dictionary containing S3 URI, metadata, and upload status

**Usage Example**:
```python
result = upload_log_to_s3(
    file_path="temp_uploads/error_log.txt",
    session_id="session123",
    file_description="Error log from instrument A"
)
```

**Output Structure**:
```json
{
  "success": true,
  "message": "Successfully uploaded error_log.txt to S3",
  "s3_uri": "s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
  "bucket": "instrument-diagnosis-logs-123456789",
  "key": "sessions/session123/logs/20250109_120000_error_log.txt",
  "file_name": "error_log.txt",
  "file_size": 1048576,
  "file_size_mb": 1.0,
  "upload_timestamp": "2025-01-09T12:00:00",
  "session_id": "session123",
  "presigned_url": "https://bucket.s3.amazonaws.com/...",
  "presigned_url_expires": "1 hour"
}
```

### 2. get_s3_file_content

**Description**: Retrieve log file content from S3 storage by streaming. Use this to access uploaded log files for analysis.

**Parameters**:
- `s3_uri` (str): S3 URI (s3://bucket/key) - provide either this or s3_key
- `s3_key` (str): S3 object key - provide either this or s3_uri
- `max_size_mb` (int): Maximum file size to retrieve in MB (default: 50)

**Returns**: Dictionary containing file content and metadata

**Usage Example**:
```python
# Using S3 URI
result = get_s3_file_content(
    s3_uri="s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
    max_size_mb=50
)

# Using S3 key
result = get_s3_file_content(
    s3_key="sessions/session123/logs/20250109_120000_error_log.txt",
    max_size_mb=50
)
```

**Output Structure**:
```json
{
  "success": true,
  "content": "2025-01-09 12:00:00 ERROR Connection timeout...\n...",
  "file_size": 1048576,
  "file_size_mb": 1.0,
  "s3_key": "sessions/session123/logs/20250109_120000_error_log.txt",
  "s3_uri": "s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt"
}
```

**Large File Handling**:
If file exceeds max_size_mb:
```json
{
  "error": "File too large: 75.5MB (max: 50MB)",
  "file_size_mb": 75.5,
  "suggestion": "Use extract_s3_log_summary for large files"
}
```

### 3. list_session_logs

**Description**: List all log files uploaded for a specific session. Use this to discover available files for analysis.

**Parameters**:
- `session_id` (str): Session identifier

**Returns**: Dictionary containing list of files and session information

**Usage Example**:
```python
result = list_session_logs(session_id="session123")
```

**Output Structure**:
```json
{
  "session_id": "session123",
  "files_found": 3,
  "total_size_mb": 5.5,
  "files": [
    {
      "key": "sessions/session123/logs/20250109_120000_error_log.txt",
      "size": 1048576,
      "last_modified": "2025-01-09T12:00:00",
      "file_name": "error_log.txt"
    },
    {
      "key": "sessions/session123/logs/20250109_120500_system_log.txt",
      "size": 2097152,
      "last_modified": "2025-01-09T12:05:00",
      "file_name": "system_log.txt"
    }
  ],
  "message": "Found 3 log files for session session123"
}
```

### 4. generate_presigned_url

**Description**: Generate a temporary presigned URL for accessing an S3-stored log file. Useful for sharing or downloading files.

**Parameters**:
- `s3_uri` (str): S3 URI (s3://bucket/key) - provide either this or s3_key
- `s3_key` (str): S3 object key - provide either this or s3_uri
- `expiration_hours` (int): URL expiration time in hours (default: 1)

**Returns**: Dictionary containing presigned URL and expiration info

**Usage Example**:
```python
result = generate_presigned_url(
    s3_uri="s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
    expiration_hours=2
)
```

**Output Structure**:
```json
{
  "success": true,
  "presigned_url": "https://bucket.s3.amazonaws.com/sessions/session123/logs/20250109_120000_error_log.txt?AWSAccessKeyId=...&Signature=...&Expires=...",
  "s3_key": "sessions/session123/logs/20250109_120000_error_log.txt",
  "s3_uri": "s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
  "expires_in_hours": 2,
  "expires_at": "2025-01-09T14:00:00"
}
```

## File Validation

The module includes comprehensive file validation before upload:

### Validation Checks
1. **File Existence**: Verifies file exists at specified path
2. **File Size**: Checks against maximum size limit (default: 500MB)
3. **File Extension**: Validates allowed extensions (.log, .txt, .csv, .out, .err)
4. **Readability**: Attempts to read first 1KB to verify file is readable

**Validation Response**:
```python
(is_valid, message)
# Examples:
(True, "File validation passed")
(False, "File too large: 550.5MB (max: 500MB)")
(False, "Invalid file type: .pdf. Allowed: .log, .txt, .csv, .out, .err")
```

## S3 Key Generation

Keys are generated with timestamp and sanitized filenames:

```python
def generate_s3_key(session_id, file_name, prefix="sessions"):
    # Sanitize filename (alphanumeric, _, -, . only)
    safe_filename = sanitize(file_name)
    
    # Add timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Build key
    return f"{prefix}/{session_id}/logs/{timestamp}_{safe_filename}"
```

**Example**:
```
Input: session_id="session123", file_name="error log (1).txt"
Output: "sessions/session123/logs/20250109_120000_error_log_1.txt"
```

## Metadata Storage

Files are uploaded with comprehensive metadata:

```python
{
    'ContentType': 'text/plain',
    'ServerSideEncryption': 'AES256',
    'Metadata': {
        'session-id': 'session123',
        'original-filename': 'error_log.txt',
        'upload-timestamp': '2025-01-09T12:00:00',
        'description': 'Error log from instrument A'  # Optional
    }
}
```

## Streaming Operations

The module uses streaming for efficient file operations:

### Upload Streaming
- Uses `upload_file()` for efficient large file uploads
- Automatic multipart upload for files >5MB
- Progress tracking available

### Download Streaming
- Uses `get_object()` with streaming body
- Reads content in chunks (default: 8192 bytes)
- Memory-efficient for large files

## Dependencies

- `boto3`: AWS SDK for S3 operations
- `botocore`: AWS core functionality and configuration
- `strands`: Tool decorator for agent integration
- `dataclasses`: Structured data representation
- `datetime`: Timestamp generation
- `logging`: Error and info logging

## Error Handling

- Invalid S3 URIs return descriptive error messages
- File not found errors are caught and reported
- Access denied errors trigger clear responses
- Bucket mismatch errors prevent incorrect operations
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Use session IDs**: Always provide meaningful session IDs for organization
2. **Add descriptions**: Include file descriptions for better tracking
3. **Check file sizes**: Validate sizes before upload to avoid failures
4. **Use presigned URLs**: For temporary access without AWS credentials
5. **List before retrieve**: Use list_session_logs to discover available files
6. **Stream large files**: Use streaming for files >50MB
7. **Set appropriate expiration**: Choose presigned URL expiration based on use case
8. **Monitor uploads**: Check success status in response
9. **Clean up old sessions**: Implement lifecycle policies for old files
10. **Use consistent naming**: Follow naming conventions for easy discovery
