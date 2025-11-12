"""
Check if S3 detection fix is in the agent file
"""

def check_s3_fix():
    """Check if the S3 detection fix is present"""
    
    agent_file = "c:/Users/esallen/MyStuff/code/github/amazon-bedrock-agents-healthcare-lifesciences/instrument-diagnosis-assistant/agent/agent_config/agent.py"
    
    try:
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Key indicators
        indicators = [
            "S3 FILE DETECTION RULES",
            "you MUST scan the entire user message for:",
            "IMMEDIATELY use get_s3_file_content",
            "NEVER respond with \"Please upload files\"",
            "SCAN MESSAGE: Look for S3 URIs"
        ]
        
        print("=== Checking Agent File for S3 Fix ===")
        found_count = 0
        
        for indicator in indicators:
            found = indicator in content
            status = "[OK]" if found else "[MISSING]"
            print(f"{status} {indicator}")
            if found:
                found_count += 1
        
        print(f"\nResult: {found_count}/{len(indicators)} indicators found")
        
        if found_count == len(indicators):
            print("SUCCESS: All S3 detection fixes are in the local file")
            print("\nIf agent is still not working, try:")
            print("1. Force redeploy: agentcore deploy --force")
            print("2. Check if there are multiple versions")
            print("3. Verify deployment completed successfully")
        else:
            print("ERROR: S3 detection fix is incomplete")
            
    except Exception as e:
        print(f"Error reading agent file: {e}")

if __name__ == "__main__":
    check_s3_fix()