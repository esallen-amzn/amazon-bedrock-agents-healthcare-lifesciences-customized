#!/usr/bin/env python3
"""
Test the agent with a specific instrument diagnosis query
"""

import subprocess
import uuid

def test_diagnosis_specific():
    session_id = str(uuid.uuid4())
    
    # Specific instrument diagnosis test
    prompt = "I have an instrument with USB connection timeout on COM3, data buffer overflow, and analysis pipeline failure. Please provide a diagnosis with confidence level."
    
    cmd = [
        "agentcore", "invoke", 
        "--session-id", session_id,
        '{"prompt": "' + prompt + '"}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        print("Response:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing specific instrument diagnosis...")
    success = test_diagnosis_specific()
    print(f"Test {'PASSED' if success else 'FAILED'}")