"""
Validate S3 URI Detection Fix

Simple validation script without Unicode characters.
"""

import os
from pathlib import Path


def validate_s3_fix():
    """Validate that the S3 URI detection fix has been applied"""
    
    # Paths
    project_root = Path("c:/Users/esallen/MyStuff/code/github/amazon-bedrock-agents-healthcare-lifesciences")
    agent_file = project_root / "instrument-diagnosis-assistant/agent/agent_config/agent.py"
    
    print("=== Validating S3 URI Detection Fix ===")
    
    # Check if agent file exists
    if not agent_file.exists():
        print(f"ERROR: Agent file not found: {agent_file}")
        return False
    
    # Read the agent file
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key fix indicators
    fix_indicators = [
        "S3 FILE DETECTION RULES",
        "you MUST scan the entire user message for:",
        "get_s3_file_content(s3_uri=",
        "NEVER respond with \"Please upload files\"",
        "SCAN MESSAGE: Look for S3 URIs"
    ]
    
    print("Checking for fix indicators...")
    
    found_indicators = []
    missing_indicators = []
    
    for indicator in fix_indicators:
        if indicator in content:
            found_indicators.append(indicator)
            print(f"[OK] Found: {indicator}")
        else:
            missing_indicators.append(indicator)
            print(f"[MISSING] Not found: {indicator}")
    
    print(f"\nResults: {len(found_indicators)}/{len(fix_indicators)} indicators found")
    
    if missing_indicators:
        print("\nWARNING: Some fix indicators not found:")
        for indicator in missing_indicators:
            print(f"   - {indicator}")
        return False
    
    print("\nSUCCESS: All fix indicators found in agent.py")
    print("\nNext Steps:")
    print("1. Redeploy the agent using: agentcore deploy")
    print("2. Test with S3 URIs to verify the fix works")
    print("3. Monitor agent behavior to ensure it uses S3 tools correctly")
    
    return True


def create_test_scenarios():
    """Create test scenarios for validation"""
    
    scenarios = [
        {
            "name": "Kiro's Original Problem",
            "message": """S3 URI: s3://instrument-diagnosis-logs-390402579286/sessions/d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b/logs/20251107_143245_error.00.log
AGENT ACTION REQUIRED: 1 S3 FILES READY""",
            "expected": "Agent should use get_s3_file_content() immediately",
            "wrong": "Agent asks 'Please provide the S3 URIs...'"
        },
        {
            "name": "Simple S3 URI",
            "message": "Please analyze s3://my-bucket/sessions/abc123/logs/error.log",
            "expected": "Agent should use get_s3_file_content() immediately",
            "wrong": "Agent asks for file upload"
        },
        {
            "name": "Session ID Only",
            "message": "Analyze logs for session d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b",
            "expected": "Agent should use list_session_logs() then get_s3_file_content()",
            "wrong": "Agent asks for file upload"
        }
    ]
    
    return scenarios


if __name__ == "__main__":
    success = validate_s3_fix()
    
    if success:
        print("\n=== Test Scenarios for Validation ===")
        scenarios = create_test_scenarios()
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\nTest {i}: {scenario['name']}")
            print("-" * 40)
            print(f"Message: {scenario['message']}")
            print(f"Expected: {scenario['expected']}")
            print(f"Wrong: {scenario['wrong']}")
    else:
        print("\nFIX VALIDATION FAILED: Please check the errors above.")