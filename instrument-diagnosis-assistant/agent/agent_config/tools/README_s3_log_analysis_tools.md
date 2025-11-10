# S3 Log Analysis Tools

## Overview

The `s3_log_analysis_tools.py` module provides S3-based log analysis with streaming and chunked processing to handle large files efficiently. It analyzes logs stored in S3 without loading entire files into memory, making it ideal for large log files.

## Purpose

This module enables:
- Streaming analysis of S3-stored log files
- Smart summary extraction for large files
- Comparison of S3 logs against baselines
- Batch analysis of multiple S3 files
- Memory-efficient processing of large files
- Pattern detection and failure analysis

## Key Components

### LogSummary (Dataclass)

Represents a smart summary extracted from a log file:

- `s3_uri`: S3 URI of the log file
- `file_name`: Original file name
- `total_lines`: Total line count
- `error_count`: Number of error lines
- `warning_count`: Number of warning lines
- `critical_events`: List of critical event lines
- `error_patterns`: Sample error lines
- `warning_patterns`: Sample warning lines
- `timestamp_range`: Tuple of (first_timestamp, last_timestamp)
- `summary_length`: Total content length in characters

### S3LogAnalyzer (Class)

Core analyzer for S3-stored logs with streaming support.

**Configuration**:
- `chunk_size_mb`: Chunk size for processing (default: 10MB)
- `buffer_size`: Buffer size for streaming (default: 8192 bytes)

### Smart Summary Extraction for Large Files

The module uses intelligent summarization to handle large files:

1. **Streaming Read**: Reads file from S3 using streaming
2. **Pattern Detection**: Identifies errors, warnings, and critical events
3. **Sample Collection**: Collects representative samples (first 20 errors, 10 warnings)
4. **Timestamp Extraction**: Finds first and last timestamps
5. **Statistics Generation**: Counts patterns and events
6. **Memory Efficiency**: Processes without loading full file

**Summary Limits**:
- Critical events: First 10
- Error patterns: First 10
- Warning patterns: First 5
- Maximum summary length: Configurable (default: 5000 characters)

## Available Tools

### 1. analyze_s3_log

**Description**: Analyze a log file stored in S3 by streaming content and extracting failure patterns. Efficient for large files.

**Parameters**:
- `s3_uri` (str): S3 URI (s3://bucket/key) - provide either this or s3_key
- `s3_key` (str): S3 object key - provide either this or s3_uri

**Returns**: Dictionary containing analysis results with patterns and summary

**Usage Example**:
```python
result = analyze_s3_log(
    s3_uri="s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt"
)

# Or using S3 key
result = analyze_s3_log(
    s3_key="sessions/session123/logs/20250109_120000_error_log.txt"
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_key": "sessions/session123/logs/20250109_120000_error_log.txt",
  "s3_uri": "s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
  "summary": {
    "s3_uri": "s3://bucket/sessions/session123/logs/20250109_120000_error_log.txt",
    "file_name": "error_log.txt",
    "total_lines": 5000,
    "error_count": 75,
    "warning_count": 120,
    "critical_events": [
      "Line 234: CRITICAL: System failure detected",
      "Line 567: CRITICAL: Connection lost"
    ],
    "error_patterns": [
      "Line 45: ERROR: Connection timeout",
      "Line 89: ERROR: Service failed to start"
    ],
    "warning_patterns": [
      "Line 12: WARNING: High memory usage",
      "Line 34: WARNING: Disk space low"
    ],
    "timestamp_range": ["2025-01-09T10:00:00", "2025-01-09T12:00:00"],
    "summary_length": 1048576
  },
  "patterns": {
    "total": 8,
    "critical": 3,
    "warnings": 5,
    "details": [
      {
        "type": "connection_timeout",
        "severity": "CRITICAL",
        "description": "Connection or communication timeout detected",
        "confidence": 0.85,
        "matches": 15,
        "sample_lines": [
          "Line 45: Connection timeout...",
          "Line 67: Timeout error...",
          "Line 89: Communication timeout..."
        ]
      }
    ]
  },
  "recommendations": [
    "CRITICAL: Critical failure patterns detected - immediate investigation required",
    "HIGH: 75 errors detected - system may be unstable"
  ],
  "status": "FAIL",
  "confidence": 0.9
}
```

### 2. extract_s3_log_summary

**Description**: Extract a smart summary from an S3-stored log file including error counts, critical events, and key patterns. Use this for large files before full analysis.

**Parameters**:
- `s3_uri` (str): S3 URI (s3://bucket/key) - provide either this or s3_key
- `s3_key` (str): S3 object key - provide either this or s3_uri
- `max_summary_length` (int): Maximum length of summary in characters (default: 5000)

**Returns**: Dictionary containing log summary with key metrics and events

**Usage Example**:
```python
result = extract_s3_log_summary(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    max_summary_length=10000
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_uri": "s3://bucket/sessions/session123/logs/large_log.txt",
  "file_name": "large_log.txt",
  "total_lines": 250000,
  "error_count": 1250,
  "warning_count": 3500,
  "critical_events": [
    "Line 1234: CRITICAL: System failure",
    "Line 5678: CRITICAL: Connection lost"
  ],
  "error_patterns": [
    "Line 45: ERROR: Connection timeout",
    "Line 89: ERROR: Service failed"
  ],
  "warning_patterns": [
    "Line 12: WARNING: High memory usage"
  ],
  "timestamp_range": ["2025-01-09T08:00:00", "2025-01-09T16:00:00"],
  "summary_length": 245000000,
  "quick_assessment": "ISSUES_DETECTED",
  "severity": "HIGH"
}
```

**Quick Assessment Values**:
- `ISSUES_DETECTED`: Error count > 50 or critical events present (HIGH/MEDIUM severity)
- `WARNINGS_PRESENT`: Warning count > 20 (LOW severity)
- `APPEARS_HEALTHY`: Minimal issues (NONE severity)

### 3. compare_s3_logs

**Description**: Compare two S3-stored log files to identify differences and deviations. Useful for comparing test logs against gold standard baselines.

**Parameters**:
- `test_s3_uri` (str): S3 URI for test log - provide either this or test_s3_key
- `test_s3_key` (str): S3 key for test log - provide either this or test_s3_uri
- `baseline_s3_uri` (str): S3 URI for baseline log - provide either this or baseline_s3_key
- `baseline_s3_key` (str): S3 key for baseline log - provide either this or baseline_s3_uri

**Returns**: Dictionary containing comparison results and deviation analysis

**Usage Example**:
```python
result = compare_s3_logs(
    test_s3_uri="s3://bucket/sessions/session123/logs/test_log.txt",
    baseline_s3_uri="s3://bucket/sessions/baseline/logs/gold_standard.txt"
)
```

**Output Structure**:
```json
{
  "success": true,
  "test_file": {
    "s3_key": "sessions/session123/logs/test_log.txt",
    "summary": {
      "total_lines": 5000,
      "error_count": 75,
      "warning_count": 120
    },
    "patterns": 8
  },
  "baseline_file": {
    "s3_key": "sessions/baseline/logs/gold_standard.txt",
    "summary": {
      "total_lines": 4800,
      "error_count": 15,
      "warning_count": 45
    },
    "patterns": 3
  },
  "comparison": {
    "status": "SIGNIFICANT_DEVIATION",
    "severity": "CRITICAL",
    "test_patterns": 8,
    "baseline_patterns": 3,
    "critical_deviation": 3,
    "warning_deviation": 5,
    "unique_test_patterns": ["connection_timeout", "service_failures"]
  },
  "deviation_analysis": {
    "critical_deviation": 3,
    "warning_deviation": 5,
    "status": "SIGNIFICANT_DEVIATION",
    "severity": "CRITICAL"
  },
  "recommendations": [
    "CRITICAL: Test log shows more critical issues than baseline - investigate immediately",
    "WARNING: Significant increase in warning patterns compared to baseline",
    "ATTENTION: New pattern types detected: connection_timeout, service_failures"
  ],
  "overall_status": "FAIL",
  "confidence": 0.9
}
```

### 4. batch_analyze_s3_logs

**Description**: Analyze multiple S3-stored log files in batch for comprehensive diagnosis across multiple instruments or sessions.

**Parameters**:
- `s3_keys` (List[str]): List of S3 object keys to analyze
- `baseline_s3_key` (str): Optional baseline S3 key for comparison

**Returns**: Dictionary containing aggregated analysis results

**Usage Example**:
```python
result = batch_analyze_s3_logs(
    s3_keys=[
        "sessions/session123/logs/instrument1_log.txt",
        "sessions/session123/logs/instrument2_log.txt",
        "sessions/session123/logs/instrument3_log.txt"
    ],
    baseline_s3_key="sessions/baseline/logs/gold_standard.txt"
)
```

**Output Structure**:
```json
{
  "success": true,
  "overall_status": "FAIL",
  "confidence": 0.9,
  "files_analyzed": 3,
  "successful_analyses": 3,
  "total_critical_patterns": 5,
  "total_errors": 225,
  "total_warnings": 360,
  "summary": "Batch analysis of 3 files: 3 successful. Total: 5 critical patterns, 225 errors, 360 warnings.",
  "recommendations": [
    "CRITICAL: Multiple files show critical patterns - system-wide investigation required",
    "HIGH: High error density across files - check system configuration"
  ],
  "individual_results": [
    {
      "success": true,
      "s3_key": "sessions/session123/logs/instrument1_log.txt",
      "summary": {...},
      "patterns": {...}
    }
  ]
}
```

## Streaming Analysis Process

### 1. File Streaming
- Connect to S3 and initiate streaming
- Read content in chunks (default: 8192 bytes)
- Process content without full file load

### 2. Pattern Detection
- Apply regex patterns to streamed content
- Identify errors, warnings, and critical events
- Calculate pattern confidence scores

### 3. Summary Generation
- Count total lines, errors, warnings
- Extract sample lines for each category
- Identify timestamp range
- Calculate statistics

### 4. Result Compilation
- Aggregate patterns across chunks
- Generate recommendations
- Determine overall status and confidence

## Comparison Logic

When comparing test logs against baselines:

### Deviation Calculation
- **Critical Deviation**: test_critical - baseline_critical
- **Warning Deviation**: test_warnings - baseline_warnings
- **Unique Patterns**: Patterns in test but not in baseline

### Status Determination
- **SIGNIFICANT_DEVIATION**: Critical deviation > 0 (CRITICAL)
- **MODERATE_DEVIATION**: Warning deviation > 5 (WARNING)
- **MINOR_DEVIATION**: Warning deviation > 0 (INFO)
- **BASELINE_MATCH**: No significant deviations (INFO)

### Confidence Scoring
- Critical deviation: 0.9
- Warning deviation: 0.7
- Baseline match: 0.85

## Dependencies

- `strands`: Tool decorator for agent integration
- `s3_storage_tools`: S3 file management
- `log_analysis_tools`: Pattern detection logic
- `boto3`: AWS S3 operations
- `dataclasses`: Structured data representation
- `logging`: Error and info logging

## Error Handling

- Invalid S3 URIs return descriptive error messages
- File not found errors are caught and reported
- Access denied errors trigger clear responses
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Use summaries first**: Extract summary before full analysis for large files
2. **Batch processing**: Use batch_analyze for multiple files
3. **Baseline comparison**: Always compare against gold standards when available
4. **Check file sizes**: Use summaries for files >50MB
5. **Review patterns**: Focus on critical patterns first
6. **Monitor confidence**: Higher confidence indicates more reliable results
7. **Use streaming**: Leverage streaming for memory efficiency
8. **Aggregate results**: Use batch analysis for system-wide view
