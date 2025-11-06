#!/usr/bin/env python3
"""
Debug script to test agent invocation with detailed logging
"""
import subprocess
import json
import os
import sys
import logging

# Set up logging with UTF-8 encoding for Windows
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_agent_invoke():
    """Test agent invocation with detailed logging"""
    
    # Test payload
    payload = {"prompt": "Hello, what can you help me with?"}
    payload_json = json.dumps(payload)
    
    # Generate a proper session ID (minimum 33 characters)
    import uuid
    session_id = str(uuid.uuid4())
    
    # Command to execute
    cmd = [
        "agentcore", "invoke", 
        "--session-id", session_id,
        payload_json
    ]
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Payload: {payload_json}")
    
    try:
        # Execute the command
        logger.info("Starting subprocess...")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30,  # 30 second timeout for debugging
            cwd=os.getcwd()
        )
        
        logger.info(f"Command completed with return code: {result.returncode}")
        logger.info(f"STDOUT length: {len(result.stdout) if result.stdout else 0}")
        logger.info(f"STDERR length: {len(result.stderr) if result.stderr else 0}")
        
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.info(f"STDERR: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ SUCCESS: Agent responded")
            if result.stdout:
                print(f"Response: {result.stdout}")
            return True
        else:
            print("❌ FAILED: Agent returned error")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after 30 seconds")
        print("❌ TIMEOUT: Agent took too long to respond")
        return False
    except Exception as e:
        logger.error(f"Exception: {type(e).__name__}: {str(e)}")
        print(f"❌ EXCEPTION: {type(e).__name__}: {str(e)}")
        return False

def check_agentcore_status():
    """Check agentcore status"""
    logger.info("Checking agentcore status...")
    try:
        result = subprocess.run(
            ["agentcore", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logger.info(f"Status command return code: {result.returncode}")
        if result.stdout:
            logger.info(f"Status output: {result.stdout}")
        if result.stderr:
            logger.info(f"Status error: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to check status: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Instrument Diagnosis Assistant...")
    
    # Check status first
    print("\n1. Checking AgentCore status...")
    if check_agentcore_status():
        print("✅ AgentCore status check passed")
    else:
        print("❌ AgentCore status check failed")
    
    # Test invocation
    print("\n2. Testing agent invocation...")
    success = test_agent_invoke()
    
    print(f"\n🎯 Result: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)