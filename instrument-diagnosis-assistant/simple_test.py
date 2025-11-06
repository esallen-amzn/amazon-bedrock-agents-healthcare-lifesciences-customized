#!/usr/bin/env python3
"""
Simple agent test script
"""
import subprocess
import json
import uuid

def test_agent():
    """Simple agent test"""
    print("Testing agent invocation...")
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Create payload
    payload = {"prompt": "Hello"}
    
    try:
        # Run agentcore invoke
        cmd = [
            "agentcore", "invoke", 
            "--session-id", session_id,
            json.dumps(payload)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
            cwd="."
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_agent()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")