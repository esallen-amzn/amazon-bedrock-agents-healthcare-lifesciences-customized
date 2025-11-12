# Agent S3 URI Detection Fix

## Problem
Kiro keeps asking users to upload files even when S3 URIs are already provided in the prompt. The agent ignores explicit S3 file information and responds with "Please provide the S3 URIs or session IDs for the logs you need analyzed."

## Root Cause
The agent's system prompt was not explicit enough about S3 URI detection patterns, and the agent was not properly scanning the user message for S3 information before responding.

## Solution Applied

### 1. Updated System Prompt
Enhanced the agent's system prompt in `agent.py` with:
- More explicit S3 URI detection rules
- Clear patterns to look for (S3 URIs, session IDs, keywords)
- Specific examples of what to detect
- Clear instructions on what NOT to do when S3 files are present

### 2. Key Detection Patterns Added
The agent now looks for:
- S3 URIs: `s3://bucket-name/sessions/SESSION-ID/logs/filename`
- Session IDs: UUID format (e.g., `d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b`)
- Keywords: "S3-STORED FILE READY FOR ANALYSIS", "S3 URI:", "SESSION ID:", etc.
- Action indicators: "get_s3_file_content(s3_uri=", "IMMEDIATE ACTION REQUIRED"

### 3. Mandatory Workflow
Updated the workflow to be more explicit:
1. SCAN MESSAGE for S3 information first
2. IF FOUND: Use `get_s3_file_content()` immediately
3. ANALYZE: Use `analyze_log_content()` with retrieved content
4. ONLY ask for uploads if NO S3 information is found

## Test Results
Created test script that validates detection logic:
- ✅ Detects S3 URIs correctly
- ✅ Detects session IDs correctly  
- ✅ Detects S3 keywords correctly
- ✅ Recommends correct action (use S3 tools vs ask for upload)

## Files Modified
1. `agent/agent_config/agent.py` - Updated system prompt
2. Created test files for validation

## Expected Behavior After Fix

### BEFORE (Wrong):
```
User: "S3 URI: s3://bucket/sessions/abc123/logs/error.log"
Agent: "Please provide the S3 URIs or session IDs for the logs you need analyzed."
```

### AFTER (Correct):
```
User: "S3 URI: s3://bucket/sessions/abc123/logs/error.log"
Agent: [Uses get_s3_file_content tool] -> [Analyzes content] -> [Provides diagnosis]
```

## Deployment
The fix is applied to the agent's system prompt. The agent needs to be redeployed for the changes to take effect.

## Validation
Use the test script `test_s3_detection.py` to validate that the detection logic works correctly before deployment.