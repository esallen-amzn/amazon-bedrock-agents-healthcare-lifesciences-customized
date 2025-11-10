# Diagnosis Tools

## Overview

The `diagnosis_tools.py` module provides comprehensive diagnosis generation capabilities for the Instrument Diagnosis Assistant. It analyzes log analysis results and generates structured diagnoses with confidence scoring, root cause analysis, and actionable recommendations.

## Purpose

This module transforms raw log analysis data into actionable diagnostic reports that include:
- Pass/Fail/Uncertain status determination
- Confidence scoring based on pattern analysis
- Severity assessment (CRITICAL, HIGH, MEDIUM, LOW, NONE)
- Root cause identification
- Actionable troubleshooting recommendations
- Supporting evidence and S3 references

## Key Components

### DiagnosisResult (Dataclass)

Represents a comprehensive diagnosis result with the following fields:

- `diagnosis_id`: Unique identifier (format: DIAG-{session_id}-{timestamp})
- `timestamp`: ISO format timestamp of diagnosis generation
- `status`: Overall status ("PASS", "FAIL", "UNCERTAIN")
- `confidence`: Confidence score (0.0-1.0)
- `severity`: Severity level ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE")
- `summary`: Human-readable summary of findings
- `failure_indicators`: List of detected failure indicators
- `root_causes`: List of identified root causes with evidence
- `recommendations`: List of actionable recommendations
- `supporting_evidence`: Dictionary of supporting data
- `s3_references`: List of S3 URIs for related files

### DiagnosisGenerator (Class)

Core diagnosis generation engine with the following capabilities:

#### Pass/Fail Determination Logic

The diagnosis status is determined using a multi-factor analysis:

1. **FAIL Status** - Assigned when:
   - Critical patterns detected (count > 0)
   - Critical events found in logs
   - Confidence: 0.9

2. **UNCERTAIN Status** - Assigned when:
   - Error count > 50
   - Warning patterns > 50
   - No critical issues but significant warnings
   - Confidence: 0.7

3. **PASS Status** - Assigned when:
   - No critical patterns
   - Error count < 10
   - Minimal warnings
   - Confidence: 0.8-0.85

#### Severity Determination

Severity is calculated based on:
- Critical pattern count
- Error count thresholds (>50 = HIGH, >20 = MEDIUM)
- Warning count thresholds (>50 = MEDIUM)
- Critical events presence

#### Root Cause Analysis

Root causes are identified by:
1. Grouping patterns by type (connection_timeout, memory_issues, etc.)
2. Calculating aggregate confidence per pattern type
3. Extracting sample evidence from matched log lines
4. Sorting by severity and confidence
5. Limiting to top 10 root causes

## Available Tools

### 1. generate_diagnosis

**Description**: Generate comprehensive diagnosis from S3 log analysis results with confidence scoring, root cause analysis, and actionable recommendations.

**Parameters**:
- `s3_uri` (str): S3 URI of log file to diagnose - provide either this or s3_key
- `s3_key` (str): S3 key of log file to diagnose - provide either this or s3_uri
- `session_id` (str): Session identifier for organizing results
- `baseline_s3_uri` (str): Optional baseline S3 URI for comparison
- `baseline_s3_key` (str): Optional baseline S3 key for comparison
- `additional_context` (str): Additional context to inform diagnosis

**Returns**: Dictionary containing comprehensive diagnosis with recommendations

**Usage Example**:
```python
# Standalone diagnosis
result = generate_diagnosis(
    s3_uri="s3://bucket/sessions/session123/logs/error.log",
    session_id="session123",
    additional_context="System was recently upgraded"
)

# Diagnosis with baseline comparison
result = generate_diagnosis(
    s3_key="sessions/session123/logs/test.log",
    baseline_s3_key="sessions/baseline/logs/gold_standard.log",
    session_id="session123"
)
```

**Output Structure**:
```json
{
  "diagnosis_id": "DIAG-session123-20250109120000",
  "timestamp": "2025-01-09T12:00:00",
  "status": "FAIL",
  "confidence": 0.9,
  "severity": "CRITICAL",
  "summary": "DIAGNOSIS: System failure detected. Severity: CRITICAL. Detected 3 failure indicator(s)...",
  "failure_indicators": [
    "Connection or communication timeout detected",
    "Service or component failure detected"
  ],
  "root_causes": [
    {
      "category": "connection_timeout",
      "description": "Connection or communication timeout detected",
      "confidence": 0.85,
      "occurrence_count": 15,
      "severity": "CRITICAL",
      "evidence": [["Line 45: Connection timeout...", "Line 67: Timeout error..."]]
    }
  ],
  "recommendations": [
    {
      "priority": "URGENT",
      "action": "Immediate Investigation Required",
      "description": "Critical system failures detected. Stop operations and investigate immediately.",
      "estimated_time": "Immediate"
    },
    {
      "priority": "HIGH",
      "action": "Check Network and USB Connections",
      "description": "Verify all physical connections, network cables, and USB ports. Test connectivity.",
      "estimated_time": "15-30 minutes"
    }
  ],
  "supporting_evidence": {
    "log_statistics": {
      "total_lines": 5000,
      "error_count": 75,
      "warning_count": 120,
      "timestamp_range": ["2025-01-09T10:00:00", "2025-01-09T12:00:00"]
    },
    "pattern_summary": {
      "total_patterns": 8,
      "critical_patterns": 3,
      "warning_patterns": 5
    }
  },
  "s3_references": [
    "s3://bucket/sessions/session123/logs/error.log"
  ],
  "success": true,
  "diagnosis_saved_to_s3": true,
  "diagnosis_s3_uri": "s3://bucket/sessions/session123/analysis/diagnosis_DIAG-session123-20250109120000.json"
}
```

### 2. get_diagnosis_from_s3

**Description**: Retrieve a previously generated diagnosis from S3 storage by diagnosis ID or S3 URI.

**Parameters**:
- `diagnosis_id` (str): Diagnosis ID to retrieve
- `session_id` (str): Session ID (required if using diagnosis_id)
- `diagnosis_s3_uri` (str): Direct S3 URI to diagnosis file

**Returns**: Dictionary containing diagnosis information

**Usage Example**:
```python
# Retrieve by diagnosis ID
result = get_diagnosis_from_s3(
    diagnosis_id="DIAG-session123-20250109120000",
    session_id="session123"
)

# Retrieve by S3 URI
result = get_diagnosis_from_s3(
    diagnosis_s3_uri="s3://bucket/sessions/session123/analysis/diagnosis_DIAG-session123-20250109120000.json"
)
```

## Recommendation Categories

The diagnosis generator provides recommendations in the following categories:

### Priority Levels
- **URGENT**: Immediate action required (critical failures)
- **HIGH**: Important actions (service failures, connection issues)
- **MEDIUM**: Recommended actions (performance, disk space)
- **LOW**: Monitoring and preventive actions

### Action Types
1. **Immediate Investigation** - Critical failures detected
2. **Check Network and USB Connections** - Connection timeouts
3. **Monitor System Resources** - Memory issues
4. **Check Disk Space** - Disk issues
5. **Restart Services** - Service failures
6. **Performance Optimization** - Performance degradation
7. **Update Drivers** - Driver issues
8. **Continue Monitoring** - System healthy (PASS status)
9. **Enhanced Monitoring** - Uncertain status

## Dependencies

- `strands`: Tool decorator for agent integration
- `s3_storage_tools`: S3 file management
- `s3_log_analysis_tools`: Log analysis functionality
- `boto3`: AWS S3 operations
- `dataclasses`: Structured data representation
- `logging`: Error and info logging

## Integration Notes

1. **S3 Integration**: All diagnoses are automatically saved to S3 for audit trail
2. **Session Organization**: Diagnoses are organized by session ID in S3
3. **Baseline Comparison**: Supports comparison against gold standard logs
4. **Confidence Thresholds**: Configurable thresholds for high/medium/low confidence
5. **Evidence Collection**: Automatically collects supporting evidence from analysis

## Error Handling

The module includes comprehensive error handling:
- Invalid S3 URIs return descriptive error messages
- Missing parameters trigger validation errors
- S3 save failures are logged but don't block diagnosis generation
- All exceptions are caught and returned as error dictionaries

## Best Practices

1. **Always provide session_id** for proper organization
2. **Use baseline comparison** when gold standard logs are available
3. **Include additional_context** for better diagnosis accuracy
4. **Save diagnoses to S3** for audit trail and historical analysis
5. **Review confidence scores** to assess diagnosis reliability
6. **Prioritize recommendations** by priority level and estimated time
