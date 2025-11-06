#!/usr/bin/env python3
"""
Test the Instrument Diagnosis Assistant with a sample log file
"""

import subprocess
import json
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_with_log_file():
    """Test the agent with a sample log file"""
    
    # Read the sample log file
    with open("sample_data/failed_unit_logs/pc_log_fail_001.txt", "r") as f:
        log_content = f.read()
    
    # Create the prompt with file content
    prompt = f"""Please analyze this failed unit log file and provide a comprehensive diagnosis:

=== UPLOADED FILES (1 file) ===
--- FILE: pc_log_fail_001.txt (1234 bytes) ---
{log_content}
=== END OF UPLOADED FILES ===

Please provide:
1. Pass/Fail determination with confidence level
2. Key failure indicators identified
3. Root cause analysis
4. Recommended troubleshooting steps
"""
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create the payload
    payload = {
        "prompt": prompt
    }
    
    try:
        logger.info("Testing agent with log file analysis...")
        logger.info(f"Session ID: {session_id}")
        
        # Execute the agentcore invoke command
        cmd = [
            "agentcore", "invoke", 
            "--session-id", session_id,
            json.dumps(payload)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="."
        )
        
        if result.returncode == 0:
            logger.info("✅ Agent analysis completed successfully!")
            print("\n" + "="*80)
            print("AGENT ANALYSIS RESULTS:")
            print("="*80)
            print(result.stdout)
            print("="*80)
            return True
        else:
            logger.error(f"❌ Agent analysis failed with return code: {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Agent analysis timed out after 60 seconds")
        return False
    except Exception as e:
        logger.error(f"❌ Error during agent analysis: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Instrument Diagnosis Assistant with Log File...")
    success = test_agent_with_log_file()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")