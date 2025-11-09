"""
S3 Log Sampling Tools - MCP Strategy for Large Files

These tools allow the agent to sample and search specific parts of large log files
without loading the entire file into context. This prevents token limit issues.
"""

import re
from typing import Dict, List, Any, Optional
from strands import tool
from .s3_storage_tools import get_storage_manager
import logging

logger = logging.getLogger(__name__)


@tool(
    name="search_log_for_pattern",
    description="Search S3 log file for specific patterns (ERROR, CRITICAL, etc.) and return only matching lines. Use this instead of loading entire file."
)
def search_log_for_pattern(
    s3_uri: str,
    pattern: str = "ERROR",
    max_matches: int = 50,
    context_lines: int = 2
) -> Dict[str, Any]:
    """
    Search log file for specific pattern and return matching lines with context.
    
    Args:
        s3_uri: S3 URI of the log file
        pattern: Pattern to search for (regex supported)
        max_matches: Maximum number of matches to return
        context_lines: Number of lines before/after match to include
    
    Returns:
        Dictionary with matching lines and metadata
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            return {'error': 'Invalid S3 URI format'}
        
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            return {'error': 'Invalid S3 URI format'}
        
        bucket, key = parts
        if bucket != storage_manager.bucket_name:
            return {'error': f'Bucket mismatch'}
        
        # Stream file and search
        content = storage_manager.stream_file_content(key)
        lines = content.split('\n')
        
        # Compile pattern
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {'error': f'Invalid regex pattern: {e}'}
        
        # Find matches
        matches = []
        for i, line in enumerate(lines):
            if regex.search(line):
                # Get context
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                match_entry = {
                    'line_number': i + 1,
                    'matched_line': line.strip(),
                    'context': '\n'.join(lines[start:end])
                }
                matches.append(match_entry)
                
                if len(matches) >= max_matches:
                    break
        
        return {
            'success': True,
            's3_uri': s3_uri,
            'pattern': pattern,
            'total_matches': len(matches),
            'matches': matches,
            'truncated': len(matches) >= max_matches,
            'message': f'Found {len(matches)} matches for pattern "{pattern}"'
        }
        
    except Exception as e:
        logger.error(f"Error searching log: {e}")
        return {'error': f'Search failed: {str(e)}'}


@tool(
    name="get_log_tail",
    description="Get the last N lines of a log file. Useful for seeing most recent events without loading entire file."
)
def get_log_tail(
    s3_uri: str,
    lines: int = 100
) -> Dict[str, Any]:
    """
    Get the last N lines of a log file.
    
    Args:
        s3_uri: S3 URI of the log file
        lines: Number of lines to retrieve from end
    
    Returns:
        Dictionary with tail content
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            return {'error': 'Invalid S3 URI format'}
        
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            return {'error': 'Invalid S3 URI format'}
        
        bucket, key = parts
        
        # Stream file
        content = storage_manager.stream_file_content(key)
        all_lines = content.split('\n')
        
        # Get tail
        tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        tail_content = '\n'.join(tail_lines)
        
        return {
            'success': True,
            's3_uri': s3_uri,
            'lines_requested': lines,
            'lines_returned': len(tail_lines),
            'total_lines': len(all_lines),
            'content': tail_content,
            'message': f'Retrieved last {len(tail_lines)} lines'
        }
        
    except Exception as e:
        logger.error(f"Error getting log tail: {e}")
        return {'error': f'Failed to get tail: {str(e)}'}


@tool(
    name="get_log_head",
    description="Get the first N lines of a log file. Useful for seeing file start without loading entire file."
)
def get_log_head(
    s3_uri: str,
    lines: int = 100
) -> Dict[str, Any]:
    """
    Get the first N lines of a log file.
    
    Args:
        s3_uri: S3 URI of the log file
        lines: Number of lines to retrieve from start
    
    Returns:
        Dictionary with head content
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            return {'error': 'Invalid S3 URI format'}
        
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            return {'error': 'Invalid S3 URI format'}
        
        bucket, key = parts
        
        # Stream file
        content = storage_manager.stream_file_content(key)
        all_lines = content.split('\n')
        
        # Get head
        head_lines = all_lines[:lines]
        head_content = '\n'.join(head_lines)
        
        return {
            'success': True,
            's3_uri': s3_uri,
            'lines_requested': lines,
            'lines_returned': len(head_lines),
            'total_lines': len(all_lines),
            'content': head_content,
            'message': f'Retrieved first {len(head_lines)} lines'
        }
        
    except Exception as e:
        logger.error(f"Error getting log head: {e}")
        return {'error': f'Failed to get head: {str(e)}'}


@tool(
    name="get_log_statistics",
    description="Get quick statistics about a log file without loading full content. Returns counts of errors, warnings, etc."
)
def get_log_statistics(
    s3_uri: str
) -> Dict[str, Any]:
    """
    Get statistics about a log file (error counts, line counts, etc.).
    
    Args:
        s3_uri: S3 URI of the log file
    
    Returns:
        Dictionary with log statistics
    """
    try:
        storage_manager = get_storage_manager()
        
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            return {'error': 'Invalid S3 URI format'}
        
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            return {'error': 'Invalid S3 URI format'}
        
        bucket, key = parts
        
        # Get file size first
        response = storage_manager.s3_client.head_object(
            Bucket=storage_manager.bucket_name,
            Key=key
        )
        file_size = response['ContentLength']
        
        # Stream and count
        content = storage_manager.stream_file_content(key)
        lines = content.split('\n')
        
        # Count patterns
        error_count = sum(1 for line in lines if re.search(r'(?i)(error|fail|exception)', line))
        warning_count = sum(1 for line in lines if re.search(r'(?i)(warning|warn)', line))
        critical_count = sum(1 for line in lines if re.search(r'(?i)(critical|fatal|severe)', line))
        
        # Find timestamp range
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}')
        first_timestamp = None
        last_timestamp = None
        
        for line in lines[:100]:
            match = timestamp_pattern.search(line)
            if match:
                first_timestamp = match.group()
                break
        
        for line in reversed(lines[-100:]):
            match = timestamp_pattern.search(line)
            if match:
                last_timestamp = match.group()
                break
        
        return {
            'success': True,
            's3_uri': s3_uri,
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'total_lines': len(lines),
            'error_count': error_count,
            'warning_count': warning_count,
            'critical_count': critical_count,
            'first_timestamp': first_timestamp,
            'last_timestamp': last_timestamp,
            'message': f'File has {len(lines)} lines with {error_count} errors, {warning_count} warnings, {critical_count} critical events'
        }
        
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        return {'error': f'Failed to get statistics: {str(e)}'}


# Export tools list
LOG_SAMPLING_TOOLS = [
    search_log_for_pattern,
    get_log_tail,
    get_log_head,
    get_log_statistics
]
