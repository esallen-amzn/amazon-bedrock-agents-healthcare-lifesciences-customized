"""
Debug deployment to check if changes were applied
"""

def check_deployment_status():
    """Check if the deployment includes our S3 detection fix"""
    
    # Check the agent file for our changes
    agent_file = "c:/Users/esallen/MyStuff/code/github/amazon-bedrock-agents-healthcare-lifesciences/instrument-diagnosis-assistant/agent/agent_config/agent.py"
    
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Key indicators that should be in the deployed version
    indicators = [
        "S3 FILE DETECTION RULES",
        "you MUST scan the entire user message for:",
        "IMMEDIATELY use get_s3_file_content",
        "NEVER respond with \"Please upload files\"",
        "SCAN MESSAGE: Look for S3 URIs"
    ]
    
    print("=== Checking Local Agent File ===")
    for indicator in indicators:
        found = indicator in content
        status = "✓" if found else "✗"
        print(f"{status} {indicator}")
    
    # Check if there might be a deployment cache issue
    print("\n=== Potential Issues ===")
    print("1. AgentCore might be caching the old version")
    print("2. The deployment might not have picked up the changes")
    print("3. There might be multiple agent versions running")
    
    print("\n=== Solutions to Try ===")
    print("1. Force redeploy: agentcore deploy --force")
    print("2. Check deployment logs for errors")
    print("3. Verify the correct agent.py is being packaged")
    print("4. Clear any deployment cache")

if __name__ == "__main__":
    check_deployment_status()