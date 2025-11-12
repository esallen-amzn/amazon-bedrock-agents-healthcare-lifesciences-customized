"""
Test S3 URI Detection in Agent Messages

This script tests whether the agent properly detects S3 URIs and session IDs
in user messages to prevent asking for file uploads when files are already available.
"""

import re
from typing import Dict, List


def detect_s3_info(message: str) -> Dict:
    """
    Detect S3 information in user message
    
    Args:
        message: User message text
        
    Returns:
        Dictionary with detection results
    """
    # Patterns to detect S3 information
    s3_uri_pattern = r's3://[a-zA-Z0-9\-\.]+/[a-zA-Z0-9\-\./]+'
    session_id_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
    
    # Find S3 URIs
    s3_uris = re.findall(s3_uri_pattern, message)
    
    # Find session IDs
    session_ids = re.findall(session_id_pattern, message)
    
    # Check for S3-related keywords
    s3_keywords = [
        "S3-STORED FILE READY FOR ANALYSIS",
        "S3 URI:",
        "SESSION ID:",
        "IMMEDIATE ACTION REQUIRED",
        "get_s3_file_content",
        "s3://",
        "S3 STORAGE:",
        "AGENT ACTION REQUIRED",
        "S3 FILES READY"
    ]
    
    found_keywords = [kw for kw in s3_keywords if kw in message]
    
    return {
        "has_s3_info": bool(s3_uris or session_ids or found_keywords),
        "s3_uris": s3_uris,
        "session_ids": session_ids,
        "keywords_found": found_keywords,
        "should_use_s3_tools": bool(s3_uris or session_ids),
        "recommended_action": "use_s3_tools" if (s3_uris or session_ids) else "ask_for_upload"
    }


def test_s3_detection():
    """Test S3 detection with various message formats"""
    
    test_cases = [
        {
            "name": "Kiro's problematic message",
            "message": """Please perform comprehensive instrument diagnosis using all uploaded files. Use comprehensive analysis mode with 0.75 confidence threshold. Use analyze_logs() for each log file (baseline optional). Analyze problem logs for failure patterns and system health indicators. Include visual analysis. Provide pass/fail determination with detailed analysis. IMPORTANT: Use only ASCII characters in your response - no emojis or Unicode symbols.
? AGENT ACTION REQUIRED: 1 S3 FILES READY
YOU MUST USE get_s3_file_content() TOOL NOW - DO NOT ASK FOR FILES
TOTAL SIZE: 5.00 MB S3 STORAGE: Files stored with session-based organization

? FILE #1: error.00.log S3_URI: s3://instrument-diagnosis-logs-390402579286/sessions/d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b/logs/20251107_143245_error.00.log SIZE: 5.00 MB ? ACTION: get_s3_file_content(s3_uri='s3://instrument-diagnosis-logs-390402579286/sessions/d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b/logs/20251107_143245_error.00.log') STANDARD FILE ACTION: Use get_s3_file_content(s3_uri='s3://instrument-diagnosis-logs-390402579286/sessions/d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b/logs/20251107_143245_error.00.log') to retrieve content""",
            "expected_action": "use_s3_tools"
        },
        {
            "name": "Simple S3 URI",
            "message": "Please analyze this log file: s3://my-bucket/sessions/abc123/logs/error.log",
            "expected_action": "use_s3_tools"
        },
        {
            "name": "Session ID only",
            "message": "Analyze logs for session d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b",
            "expected_action": "use_s3_tools"
        },
        {
            "name": "No S3 info",
            "message": "Please analyze my log files for errors",
            "expected_action": "ask_for_upload"
        },
        {
            "name": "S3 keyword present",
            "message": "S3-STORED FILE READY FOR ANALYSIS: error.log",
            "expected_action": "use_s3_tools"
        }
    ]
    
    print("=== S3 Detection Test Results ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 50)
        
        result = detect_s3_info(test_case['message'])
        
        print(f"Has S3 Info: {result['has_s3_info']}")
        print(f"S3 URIs Found: {len(result['s3_uris'])}")
        if result['s3_uris']:
            for uri in result['s3_uris']:
                print(f"  - {uri}")
        
        print(f"Session IDs Found: {len(result['session_ids'])}")
        if result['session_ids']:
            for sid in result['session_ids']:
                print(f"  - {sid}")
        
        print(f"Keywords Found: {len(result['keywords_found'])}")
        if result['keywords_found']:
            for kw in result['keywords_found']:
                print(f"  - {kw}")
        
        print(f"Recommended Action: {result['recommended_action']}")
        
        # Check if test passed
        passed = result['recommended_action'] == test_case['expected_action']
        print(f"Test Result: {'PASS' if passed else 'FAIL'}")
        
        if not passed:
            print(f"Expected: {test_case['expected_action']}, Got: {result['recommended_action']}")
        
        print("\n")


def generate_agent_instructions():
    """Generate specific instructions for the agent to handle S3 detection"""
    
    instructions = """
=== AGENT S3 DETECTION INSTRUCTIONS ===

When you receive a user message, FIRST run this mental checklist:

1. SCAN for S3 URIs (s3://...)
2. SCAN for Session IDs (UUID format)
3. SCAN for keywords: "S3-STORED FILE", "S3 URI:", "SESSION ID:", "AGENT ACTION REQUIRED"

IF ANY ARE FOUND:
- Extract the S3 URI from the message
- Use get_s3_file_content(s3_uri="extracted_uri") immediately
- Proceed with analysis using analyze_log_content()
- DO NOT ask for file uploads

IF NONE ARE FOUND:
- Ask user to upload files via the UI

EXAMPLE CORRECT RESPONSES:

User: "S3 URI: s3://bucket/sessions/abc123/logs/error.log"
Agent: [Uses get_s3_file_content tool] -> [Analyzes content] -> [Provides diagnosis]

User: "Please analyze my logs"
Agent: "Please upload your log files using the file upload interface."

NEVER DO THIS:
User: "S3 URI: s3://bucket/sessions/abc123/logs/error.log"
Agent: "Please upload your log files" ❌ WRONG!
"""
    
    return instructions


if __name__ == "__main__":
    # Run the tests
    test_s3_detection()
    
    # Print agent instructions
    print(generate_agent_instructions())