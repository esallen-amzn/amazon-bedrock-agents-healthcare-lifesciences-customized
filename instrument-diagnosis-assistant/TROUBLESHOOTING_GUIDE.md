# Troubleshooting Guide: "Unknown Error" Issue

## Problem Identified

The "Unknown error" message is caused by two issues:

### 1. Expired AWS Credentials
```
❌ Error retrieving memory status: An error occurred (ExpiredTokenException) when calling the GetMemory operation: The security token included in the request is expired
```

### 2. Agent Not Ready
```
Agent Status: instrument_diagnosis_assistant
Deploying - Agent created, endpoint starting
Endpoint: DEFAULT (Unknown)
```

## Solutions

### Step 1: Refresh AWS Credentials

**Option A: Using AWS CLI**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

**Option B: Using the credential helper scripts**
```powershell
# Run the PowerShell script we created earlier
.\set_creds.ps1
```

**Option C: Using AWS SSO (if configured)**
```bash
aws sso login
```

### Step 2: Wait for Agent Deployment

The agent is currently deploying. You need to wait for it to be ready:

```bash
# Check agent status periodically
agentcore status

# Wait until you see:
# ✅ Agent Status: READY
# ✅ Endpoint: [some URL]
```

### Step 3: Verify Agent is Ready

Once the agent is ready, you should see:
- Agent status shows "READY" instead of "Deploying"
- Endpoint shows an actual URL instead of "Unknown"
- No ExpiredTokenException errors

## How to Check if Fixed

1. **Run status check:**
   ```bash
   agentcore status
   ```

2. **Look for these indicators:**
   - ✅ No ExpiredTokenException errors
   - ✅ Agent Status shows "READY"
   - ✅ Endpoint shows actual URL

3. **Test a simple invoke:**
   ```bash
   echo '{"prompt": "Hello"}' | agentcore invoke -
   ```

## Prevention

### Set Up Credential Refresh
1. Use AWS SSO for automatic credential refresh
2. Set up credential helper scripts for easy renewal
3. Monitor credential expiration times

### Monitor Agent Status
1. Check agent status before using the app
2. Set up CloudWatch alarms for agent health
3. Use the observability dashboard for monitoring

## Additional Debugging

### Check CloudWatch Logs
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/instrument_diagnosis_assistant-pr2Osn4Xxi-DEFAULT --log-stream-name-prefix "2025/11/06/[runtime-logs]" --follow
```

### View Observability Dashboard
Visit: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#gen-ai-observability/agent-core

### Enable Debug Mode
In the Streamlit app, check "Show Debug Info" in the sidebar to see:
- Current agent ARN
- Session ID
- Region
- Detailed error messages

## Additional Issue: Unicode Character Encoding

### Problem
```
Invocation failed: 'charmap' codec can't encode character '\U0001f527' in position 0: character maps to <undefined>
```

### Cause
Windows command line has issues with Unicode characters (like emojis 🔧📊) in subprocess calls.

### Solution
The app now automatically:
- Converts Unicode characters to ASCII-safe equivalents
- Uses UTF-8 encoding with error replacement
- Ensures JSON payloads are ASCII-safe

### What This Means
- Emojis in prompts will be replaced with `?` characters
- The agent will still understand the intent
- No more encoding-related failures

## Expected Timeline

- **Credential refresh**: Immediate (1-2 minutes)
- **Agent deployment**: 5-15 minutes typically
- **First invoke after deployment**: May take 30-60 seconds for cold start
- **Unicode character handling**: Automatic (no user action needed)

## Next Steps

1. **Immediate**: Refresh your AWS credentials
2. **Wait**: Monitor `agentcore status` until agent is READY
3. **Test**: Try the Streamlit app again
4. **Monitor**: Use the debug info to verify everything is working

The improved error handling in the app will now provide more specific information about these issues in the future.