#!/usr/bin/env python3
"""
Simple test script to verify the agent is working
"""
import subprocess
import json
import sys

def test_simple_prompt():
    """Test the agent with a simple prompt"""
    payload = {"prompt": "Hello, what can you help me with?"}
    payload_json = json.dumps(payload)
    
    try:
        # Use agentcore invoke command
        result = subprocess.run(
            ["agentcore", "invoke", payload_json],
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
            cwd="."
        )
        
        if result.returncode == 0:
            print("✅ Agent responded successfully!")
            print("Response:", result.stdout.strip())
            return True
        else:
            print("❌ Agent failed to respond")
            print("Error:", result.stderr.strip())
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Agent timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

if __name__ == "__main__":
    print("Testing Instrument Diagnosis Assistant...")
    success = test_simple_prompt()
    sys.exit(0 if success else 1)