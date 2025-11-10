# Log Analysis Tools

## Overview

The `log_analysis_tools.py` module provides comprehensive log file analysis capabilities with support for large files (up to 250MB), pattern detection, baseline comparison, and batch processing. It handles both local file analysis and integrates with S3-stored logs.

## Purpose

This module enables:
- Detection of failure patterns in log files
- Comparison against gold standard baselines
- Processing of large log files using chunked strategy
- Batch analysis of multiple log files
- Extraction of specific failure indicators
- File scanning and discovery

## Key Components

### LogProcessor (Class)

Core log processing engine with configurable chunk sizes and pattern detection.

**Configuration**:
- `chunk_size_mb`: Size of each chunk for large file processing (default: 50MB)
- `max_file_size_mb`: Maximum supported file size (default: 250MB)

**Failure Patterns Detected**:
1. **connection_timeout** (CRITICAL)
   - Regex: `(?i)(timeout|connection.*failed|communication.*timeout)`
   - Description: Connection or communication timeout detected

2. **memory_issues** (CRITICAL)
   - Regex: `(?i)(memory.*leak|overflow|out of memory|high usage)`
   - Description: Memory-related issues detected

3. **disk_issues** (WARNING)
   - Regex: `(?i)(disk.*error|write.*error|low space|disk.*full)`
   - Description: Disk or storage issues detected

4. **service_failures** (CRITICAL)
   - Regex: `(?i)(service.*failed|failed.*start|error.*loading)`
   - Description: Service or component failure detected

5. **performance_degradation** (WARNING)
   - Regex: `(?i)(degraded|slow|intermittent|partial.*success)`
   - Description: Performance degradation detected

6. **driver_issues** (WARNING)
   - Regex: `(?i)(driver.*error|outdated.*driver|version.*mismatch)`
   - Description: Driver-related issues detected

### Chunking Strategy for Large Files

The module uses an intelligent chunking strategy to handle large log files:

1. **File Validation**: Checks file size and readability before processing
2. **Chunk Creation**: Splits file into manageable chunks (default 50MB)
3. **Line-Aware Splitting**: Ensures chunks split on line boundaries
4. **Metadata Tracking**: Tracks line numbers and byte positions for each chunk
5. **Pattern Aggregation**: Combines patterns found across all chunks
6. **Memory Efficiency**: Processes one chunk at a time to minimize memory usage

**Chunk Structure**:
```python
LogChunk(
    chunk_id=0,
    content="...",  # Chunk text content
    start_line=1,
    end_line=1000,
    size_bytes=52428800  # 50MB
)
```

## Available Tools

### 1. analyze_logs

**Description**: Analyze log files with optional gold standard comparison to identify failures and anomalies. Can process single files or multiple files in batch.

**Parameters**:
- `test_log_path` (str): Path to the log file to analyze
- `baseline_log_path` (str): Optional path to the gold standard log file for comparison (empty string if not available)
- `analysis_type` (str): Type of analysis ("full", "patterns_only", "quick")

**Returns**: Dictionary containing analysis results with status, patterns, and recommendations

**Usage Example**:
```python
# Standalone analysis
result = analyze_logs(
    test_log_path="temp_uploads/error_log.txt",
    baseline_log_path="",
    analysis_type="full"
)

# Baseline comparison
result = analyze_logs(
    test_log_path="temp_uploads/test_log.txt",
    baseline_log_path="temp_uploads/gold_standard.txt",
    analysis_type="full"
)
```

**Output Structure**:
```json
{
  "status": "FAIL",
  "confidence": 0.9,
  "failure_indicators": [
    "Connection or communication timeout detected",
    "Service or component failure detected"
  ],
  "comparison_summary": "Found 8 patterns vs 2 in baseline. Status: SIGNIFICANT_DEVIATION",
  "recommendations": [
    "CRITICAL: Investigate connection timeouts and service failures immediately",
    "WARNING: Multiple performance issues detected - check system resources"
  ],
  "processing_stats": {
    "test_file_size": 1048576,
    "baseline_file_size": 524288,
    "patterns_detected": 8,
    "critical_patterns": 3,
    "warning_patterns": 5,
    "has_baseline": true,
    "comparison_result": {
      "status": "SIGNIFICANT_DEVIATION",
      "severity": "CRITICAL",
      "critical_deviation": 3,
      "warning_deviation": 3,
      "unique_test_patterns": ["connection_timeout", "service_failures"]
    }
  }
}
```

### 2. analyze_multiple_logs

**Description**: Analyze multiple log files in batch for comprehensive diagnosis across multiple instruments or time periods.

**Parameters**:
- `log_file_paths` (List[str]): List of paths to log files to analyze
- `baseline_log_path` (str): Optional path to gold standard log file for comparison
- `analysis_type` (str): Type of analysis ("full", "patterns_only", "quick")

**Returns**: Dictionary containing aggregated analysis results across all files

**Usage Example**:
```python
result = analyze_multiple_logs(
    log_file_paths=[
        "temp_uploads/instrument1_log.txt",
        "temp_uploads/instrument2_log.txt",
        "temp_uploads/instrument3_log.txt"
    ],
    baseline_log_path="temp_uploads/baseline.txt",
    analysis_type="full"
)
```

**Output Structure**:
```json
{
  "overall_status": "FAIL",
  "confidence": 0.9,
  "files_processed": 3,
  "total_critical_patterns": 5,
  "total_warning_patterns": 12,
  "summary": "Batch analysis of 3 files completed. Total critical patterns: 5, Total warnings: 12. Overall assessment: FAIL",
  "recommendations": [
    "CRITICAL: Multiple files show critical failure patterns - immediate investigation required"
  ],
  "individual_results": [
    {
      "file_path": "temp_uploads/instrument1_log.txt",
      "result": { "status": "FAIL", "confidence": 0.9, ... }
    }
  ],
  "batch_analysis": true
}
```

### 3. scan_for_uploaded_files

**Description**: MANDATORY FIRST STEP: Always use this tool first to scan temp_uploads directory for available log files before any analysis.

**Parameters**: None

**Returns**: Dictionary containing information about available files for analysis

**Usage Example**:
```python
result = scan_for_uploaded_files()
```

**Output Structure**:
```json
{
  "files_found": 3,
  "message": "Found 3 log files ready for analysis",
  "files": [
    {
      "name": "error_log.txt",
      "path": "temp_uploads/error_log.txt",
      "size_bytes": 1048576,
      "size_mb": 1.0,
      "type": "error_log"
    }
  ],
  "recommended_action": "Use analyze_logs('temp_uploads/error_log.txt', '') to analyze the largest file"
}
```

### 4. process_large_files

**Description**: Process large log files (>50MB) using chunked processing for memory efficiency.

**Parameters**:
- `file_path` (str): Path to the large log file to process
- `processing_mode` (str): Processing mode ("patterns", "summary", "full")
- `chunk_size_mb` (int): Size of each chunk in MB (default: 50)

**Returns**: Dictionary containing processing results and aggregated analysis

**Usage Example**:
```python
result = process_large_files(
    file_path="temp_uploads/large_log.txt",
    processing_mode="full",
    chunk_size_mb=50
)
```

**Output Structure**:
```json
{
  "status": "CRITICAL_ISSUES_DETECTED",
  "confidence": 0.9,
  "file_info": {
    "path": "temp_uploads/large_log.txt",
    "total_chunks": 5,
    "total_lines": 250000,
    "file_size_mb": 245.5
  },
  "analysis_summary": {
    "total_patterns": 25,
    "critical_patterns": 8,
    "warning_patterns": 17,
    "pattern_types": ["connection_timeout", "memory_issues", "service_failures"]
  },
  "chunk_details": [
    {
      "chunk_id": 0,
      "lines": "1-50000",
      "size_mb": 50.0,
      "patterns_found": 5,
      "critical_patterns": 2,
      "warning_patterns": 3
    }
  ],
  "top_issues": [
    {
      "type": "connection_timeout",
      "severity": "CRITICAL",
      "description": "Connection or communication timeout detected",
      "confidence": 0.85,
      "sample_matches": ["Line 1234: Connection timeout...", "Line 5678: Timeout error..."]
    }
  ]
}
```

### 5. analyze_log_content

**Description**: Analyze log content directly without requiring file paths - useful for uploaded file content.

**Parameters**:
- `test_log_content` (str): The log content to analyze
- `baseline_log_content` (str): Optional baseline log content for comparison
- `analysis_type` (str): Type of analysis ("full", "patterns_only", "quick")

**Returns**: Dictionary containing analysis results with status, patterns, and recommendations

**Usage Example**:
```python
with open("temp_uploads/log.txt", "r") as f:
    content = f.read()

result = analyze_log_content(
    test_log_content=content,
    baseline_log_content="",
    analysis_type="full"
)
```

### 6. extract_failure_indicators

**Description**: Extract and categorize specific failure patterns and indicators from log content.

**Parameters**:
- `log_content` (str): Raw log content to analyze
- `indicator_types` (List[str]): List of specific indicator types to look for (optional)
- `severity_filter` (str): Filter by severity ("all", "critical", "warning")

**Returns**: Dictionary containing categorized failure indicators and analysis

**Usage Example**:
```python
result = extract_failure_indicators(
    log_content=content,
    indicator_types=["connection_timeout", "memory_issues"],
    severity_filter="critical"
)
```

## Baseline Comparison Logic

When a baseline log is provided, the module performs comparative analysis:

### Comparison Metrics
1. **Critical Deviation**: Difference in critical pattern count
2. **Warning Deviation**: Difference in warning pattern count
3. **Unique Patterns**: Patterns present in test but not in baseline

### Status Determination
- **SIGNIFICANT_DEVIATION**: Critical deviation > 0 (CRITICAL severity)
- **MODERATE_DEVIATION**: Warning deviation > 2 (WARNING severity)
- **MINOR_DEVIATION**: Warning deviation > 0 (INFO severity)
- **BASELINE_MATCH**: No significant deviations (INFO severity)

### Confidence Scoring
- With baseline comparison: 0.9 (critical deviation) / 0.7 (warning deviation) / 0.85 (match)
- Without baseline: 0.85 (critical) / 0.7 (warnings) / 0.8 (pass)

## Dependencies

- `strands`: Tool decorator for agent integration
- `re`: Regular expression pattern matching
- `json`: JSON data handling
- `dataclasses`: Structured data representation
- `pathlib`: File path operations
- `logging`: Error and info logging

## File Validation

The module includes comprehensive file validation:
- File existence check
- File size validation (max 250MB)
- Readability verification
- Extension validation (.log, .txt, .csv, .out, .err)

## Error Handling

- Invalid file paths return descriptive error messages
- File size violations trigger clear error responses
- Empty or unreadable files are detected and reported
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Always scan first**: Use `scan_for_uploaded_files()` before analysis
2. **Use chunked processing**: For files >50MB, use `process_large_files()`
3. **Provide baselines**: When available, use baseline comparison for better accuracy
4. **Batch processing**: Use `analyze_multiple_logs()` for multiple files
5. **Check file sizes**: Validate file sizes before processing
6. **Review confidence scores**: Higher confidence indicates more reliable results
7. **Prioritize critical patterns**: Focus on CRITICAL severity patterns first
