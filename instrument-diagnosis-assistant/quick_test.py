#!/usr/bin/env python3
import subprocess
import uuid

session_id = str(uuid.uuid4())
cmd = ["agentcore", "invoke", "--session-id", session_id, '{"prompt": "Hello"}']

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"Return code: {result.returncode}")
    if result.returncode == 0:
        print("✅ Agent is working!")
    else:
        print("❌ Agent failed")
        print("STDERR:", result.stderr)
except Exception as e:
    print(f"Error: {e}")