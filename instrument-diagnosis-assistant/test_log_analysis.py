#!/usr/bin/env python3
"""
Test log analysis with the agent
"""

import subprocess
import uuid

def test_log_analysis():
    session_id = str(uuid.uuid4())
    
    # Simple log analysis test
    prompt = "Analyze this instrument log: USB Connection TIMEOUT on COM3, Data Buffer OVERFLOW status CRITICAL, Analysis pipeline failure, Memory leak detected 2.1GB/hour. Provide diagnosis and recommendations."
    
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
    print("Testing log analysis...")
    success = test_log_analysis()
    print(f"Test {'PASSED' if success else 'FAILED'}")