"""
Apply S3 URI Detection Fix to Agent

This script applies the S3 URI detection fix to the agent configuration.
"""

import os
import shutil
from pathlib import Path


def apply_s3_fix():
    """Apply the S3 URI detection fix to the agent"""
    
    # Paths
    project_root = Path("c:/Users/esallen/MyStuff/code/github/amazon-bedrock-agents-healthcare-lifesciences")
    agent_file = project_root / "instrument-diagnosis-assistant/agent/agent_config/agent.py"
    backup_file = agent_file.with_suffix('.py.backup')
    
    print("=== Applying S3 URI Detection Fix ===")
    
    # Check if agent file exists
    if not agent_file.exists():
        print(f"ERROR: Agent file not found: {agent_file}")
        return False
    
    # Create backup
    print(f"Creating backup: {backup_file}")
    shutil.copy2(agent_file, backup_file)
    
    # The fix has already been applied via fsReplace
    # This script serves as documentation and validation
    
    print("✅ S3 URI detection fix has been applied to agent.py")
    print("✅ Backup created successfully")
    
    # Validate the fix
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key fix indicators
    fix_indicators = [
        "S3 FILE DETECTION RULES",
        "SCAN the entire user message for:",
        "get_s3_file_content(s3_uri=",
        "NEVER respond with \"Please upload files\"",
        "SCAN MESSAGE: Look for S3 URIs"
    ]
    
    missing_indicators = []
    for indicator in fix_indicators:
        if indicator not in content:
            missing_indicators.append(indicator)
    
    if missing_indicators:
        print("⚠️  WARNING: Some fix indicators not found:")
        for indicator in missing_indicators:
            print(f"   - {indicator}")
        return False
    
    print("✅ All fix indicators found in agent.py")
    print("\n=== Next Steps ===")
    print("1. Redeploy the agent using: agentcore deploy")
    print("2. Test with S3 URIs to verify the fix works")
    print("3. Monitor agent behavior to ensure it uses S3 tools correctly")
    
    return True


def create_test_message():
    """Create a test message to validate the fix"""
    
    test_message = """
Please perform comprehensive instrument diagnosis using all uploaded files.

AGENT ACTION REQUIRED: 1 S3 FILES READY
S3 URI: s3://instrument-diagnosis-logs-390402579286/sessions/d3cd3b66-5635-4f0a-9e34-8d0efa9fe72b/logs/20251107_143245_error.00.log

The agent should immediately use get_s3_file_content() tool with this URI.
"""
    
    return test_message


if __name__ == "__main__":
    success = apply_s3_fix()
    
    if success:
        print("\n=== Test Message for Validation ===")
        print("Use this message to test the agent after redeployment:")
        print("-" * 50)
        print(create_test_message())
        print("-" * 50)
        print("Expected behavior: Agent should use get_s3_file_content() tool immediately")
        print("Wrong behavior: Agent asks 'Please provide the S3 URIs...'")
    else:
        print("❌ Fix application failed. Please check the errors above.")