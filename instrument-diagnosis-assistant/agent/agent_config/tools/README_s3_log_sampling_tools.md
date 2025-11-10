# S3 Log Sampling Tools - MCP Strategy

## Overview

The `s3_log_sampling_tools.py` module implements the MCP (Model Context Protocol) sampling strategy for large log files. It allows selective sampling and searching of specific parts of large files without loading the entire file into context, preventing token limit issues.

## Purpose

This module enables:
- Search for specific patterns in large log files
- Retrieve tail (last N lines) of log files
- Retrieve head (first N lines) of log files
- Get quick statistics without loading full content
- Prevent token limit issues with large files
- Efficient targeted analysis of specific log sections

## MCP Sampling Strategy

The MCP strategy is designed to work within token limits by:

1. **Selective Loading**: Only load relevant portions of files
2. **Pattern-Based Search**: Find specific patterns without full file scan
3. **Boundary Sampling**: Access file head/tail for context
4. **Statistics First**: Get overview before detailed analysis
5. **Context Preservation**: Include surrounding lines for context

### Why MCP Strategy?

**Problem**: Large log files (100MB+) cannot fit in agent context
**Solution**: Sample specific sections based on analysis needs

**Benefits**:
- Avoid token limit errors
- Faster analysis (only process relevant sections)
- Targeted investigation (focus on errors/warnings)
- Memory efficient (stream without full load)
- Flexible exploration (head, tail, search, stats)

## Available Tools

### 1. search_log_for_pattern

**Description**: Search S3 log file for specific patterns (ERROR, CRITICAL, etc.) and return only matching lines. Use this instead of loading entire file.

**Parameters**:
- `s3_uri` (str): S3 URI of the log file
- `pattern` (str): Pattern to search for (regex supported) - default: "ERROR"
- `max_matches` (int): Maximum number of matches to return - default: 50
- `context_lines` (int): Number of lines before/after match to include - default: 2

**Returns**: Dictionary with matching lines and metadata

**Usage Example**:
```python
# Search for ERROR patterns
result = search_log_for_pattern(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    pattern="ERROR",
    max_matches=50,
    context_lines=2
)

# Search for CRITICAL patterns
result = search_log_for_pattern(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    pattern="CRITICAL",
    max_matches=20,
    context_lines=3
)

# Search with regex
result = search_log_for_pattern(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    pattern="(?i)(timeout|connection.*failed)",
    max_matches=30,
    context_lines=2
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_uri": "s3://bucket/sessions/session123/logs/large_log.txt",
  "pattern": "ERROR",
  "total_matches": 45,
  "matches": [
    {
      "line_number": 1234,
      "matched_line": "2025-01-09 12:00:00 ERROR Connection timeout detected",
      "context": "2025-01-09 11:59:58 INFO Attempting connection\n2025-01-09 11:59:59 INFO Waiting for response\n2025-01-09 12:00:00 ERROR Connection timeout detected\n2025-01-09 12:00:01 WARNING Retrying connection\n2025-01-09 12:00:02 INFO Connection established"
    },
    {
      "line_number": 5678,
      "matched_line": "2025-01-09 13:30:15 ERROR Service failed to start",
      "context": "..."
    }
  ],
  "truncated": false,
  "message": "Found 45 matches for pattern \"ERROR\""
}
```

**Best Practices**:
- Start with broad patterns (ERROR, CRITICAL)
- Use context_lines to understand surrounding events
- Limit max_matches for initial exploration
- Use regex for complex pattern matching
- Check truncated flag to see if more matches exist

### 2. get_log_tail

**Description**: Get the last N lines of a log file. Useful for seeing most recent events without loading entire file.

**Parameters**:
- `s3_uri` (str): S3 URI of the log file
- `lines` (int): Number of lines to retrieve from end - default: 100

**Returns**: Dictionary with tail content

**Usage Example**:
```python
# Get last 100 lines
result = get_log_tail(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    lines=100
)

# Get last 500 lines for more context
result = get_log_tail(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    lines=500
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_uri": "s3://bucket/sessions/session123/logs/large_log.txt",
  "lines_requested": 100,
  "lines_returned": 100,
  "total_lines": 250000,
  "content": "2025-01-09 15:58:00 INFO Processing complete\n2025-01-09 15:58:01 INFO Shutting down\n...\n2025-01-09 16:00:00 INFO System stopped",
  "message": "Retrieved last 100 lines"
}
```

**Use Cases**:
- Check most recent errors
- Verify system shutdown/startup
- See latest status messages
- Identify recent failures
- Monitor ongoing operations

### 3. get_log_head

**Description**: Get the first N lines of a log file. Useful for seeing file start without loading entire file.

**Parameters**:
- `s3_uri` (str): S3 URI of the log file
- `lines` (int): Number of lines to retrieve from start - default: 100

**Returns**: Dictionary with head content

**Usage Example**:
```python
# Get first 100 lines
result = get_log_head(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    lines=100
)

# Get first 200 lines for initialization context
result = get_log_head(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt",
    lines=200
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_uri": "s3://bucket/sessions/session123/logs/large_log.txt",
  "lines_requested": 100,
  "lines_returned": 100,
  "total_lines": 250000,
  "content": "2025-01-09 08:00:00 INFO System starting\n2025-01-09 08:00:01 INFO Loading configuration\n...\n2025-01-09 08:01:40 INFO Initialization complete",
  "message": "Retrieved first 100 lines"
}
```

**Use Cases**:
- Check system initialization
- Verify configuration loading
- See startup errors
- Identify early failures
- Review initial conditions

### 4. get_log_statistics

**Description**: Get quick statistics about a log file without loading full content. Returns counts of errors, warnings, etc.

**Parameters**:
- `s3_uri` (str): S3 URI of the log file

**Returns**: Dictionary with log statistics

**Usage Example**:
```python
result = get_log_statistics(
    s3_uri="s3://bucket/sessions/session123/logs/large_log.txt"
)
```

**Output Structure**:
```json
{
  "success": true,
  "s3_uri": "s3://bucket/sessions/session123/logs/large_log.txt",
  "file_size_bytes": 245000000,
  "file_size_mb": 233.65,
  "total_lines": 250000,
  "error_count": 1250,
  "warning_count": 3500,
  "critical_count": 15,
  "first_timestamp": "2025-01-09T08:00:00",
  "last_timestamp": "2025-01-09T16:00:00",
  "message": "File has 250000 lines with 1250 errors, 3500 warnings, 15 critical events"
}
```

**Use Cases**:
- Quick health check
- Decide if detailed analysis needed
- Estimate analysis scope
- Identify time range
- Prioritize investigation

## MCP Strategy Workflow

### Recommended Analysis Sequence

1. **Start with Statistics**
   ```python
   stats = get_log_statistics(s3_uri)
   # Decide next steps based on counts
   ```

2. **Check Recent Activity**
   ```python
   tail = get_log_tail(s3_uri, lines=100)
   # See what happened most recently
   ```

3. **Search for Critical Issues**
   ```python
   critical = search_log_for_pattern(s3_uri, pattern="CRITICAL", max_matches=20)
   # Focus on most severe issues
   ```

4. **Search for Specific Errors**
   ```python
   errors = search_log_for_pattern(s3_uri, pattern="ERROR", max_matches=50)
   # Investigate error patterns
   ```

5. **Check Initialization (if needed)**
   ```python
   head = get_log_head(s3_uri, lines=100)
   # Verify startup was successful
   ```

### Pattern Search Best Practices

**Common Patterns**:
- `ERROR` - All error messages
- `CRITICAL` - Critical failures
- `WARNING` - Warning messages
- `(?i)(timeout|connection.*failed)` - Connection issues
- `(?i)(memory|out of memory)` - Memory problems
- `(?i)(disk|storage|space)` - Disk issues
- `(?i)(service.*failed|failed.*start)` - Service failures

**Context Guidelines**:
- Use 2-3 context lines for quick overview
- Use 5-10 context lines for detailed investigation
- More context helps understand event sequence

**Match Limits**:
- Start with 20-50 matches for exploration
- Increase if pattern is rare
- Decrease if pattern is very common

## Token Management

### Why Token Limits Matter

Large log files can easily exceed token limits:
- 100MB log file ≈ 25M tokens (way over limit)
- Full file load causes context overflow
- Agent cannot process entire file at once

### How MCP Strategy Helps

**Without MCP Strategy**:
```
Load entire 100MB file → Token limit exceeded → Analysis fails
```

**With MCP Strategy**:
```
1. Get statistics (< 1K tokens)
2. Search for "ERROR" (< 10K tokens for 50 matches)
3. Get tail (< 5K tokens for 100 lines)
Total: < 20K tokens → Analysis succeeds
```

### Token Estimation

- Statistics: ~500-1000 tokens
- Head/Tail (100 lines): ~2000-5000 tokens
- Search results (50 matches with context): ~5000-10000 tokens
- Total typical workflow: ~10000-20000 tokens (well within limits)

## Dependencies

- `strands`: Tool decorator for agent integration
- `s3_storage_tools`: S3 file management
- `re`: Regular expression pattern matching
- `logging`: Error and info logging

## Error Handling

- Invalid S3 URIs return descriptive error messages
- Invalid regex patterns trigger clear error responses
- File not found errors are caught and reported
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Always start with statistics**: Get overview before detailed analysis
2. **Use targeted searches**: Search for specific patterns instead of loading full file
3. **Check tail first**: Most recent events often most relevant
4. **Use context wisely**: Balance between context and token usage
5. **Limit matches**: Start with smaller limits, increase if needed
6. **Use regex for flexibility**: Complex patterns help find specific issues
7. **Combine tools**: Use multiple tools for comprehensive analysis
8. **Monitor token usage**: Keep total tokens under limits
9. **Prioritize critical patterns**: Focus on CRITICAL and ERROR first
10. **Document findings**: Note line numbers for future reference

## Example Workflows

### Workflow 1: Quick Health Check
```python
# 1. Get statistics
stats = get_log_statistics(s3_uri)

# 2. If errors > 100, search for patterns
if stats['error_count'] > 100:
    errors = search_log_for_pattern(s3_uri, "ERROR", max_matches=20)

# 3. Check recent activity
tail = get_log_tail(s3_uri, lines=50)
```

### Workflow 2: Failure Investigation
```python
# 1. Search for critical failures
critical = search_log_for_pattern(s3_uri, "CRITICAL", max_matches=10, context_lines=5)

# 2. Search for related errors
errors = search_log_for_pattern(s3_uri, "ERROR", max_matches=30, context_lines=3)

# 3. Check when issue started
head = get_log_head(s3_uri, lines=100)
```

### Workflow 3: Performance Analysis
```python
# 1. Search for performance issues
perf = search_log_for_pattern(s3_uri, "(?i)(slow|timeout|degraded)", max_matches=40)

# 2. Check recent performance
tail = get_log_tail(s3_uri, lines=200)

# 3. Get overall statistics
stats = get_log_statistics(s3_uri)
```
