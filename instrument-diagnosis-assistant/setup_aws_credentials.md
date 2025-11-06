# AWS Credential Setup Guide

## Option 1: AWS CLI Configuration (Recommended)

### For AWS SSO (Single Sign-On):
```bash
# Configure AWS SSO
aws configure sso

# Follow the prompts:
# - SSO session name: [your-session-name]
# - SSO start URL: [your-sso-url]
# - SSO region: us-east-1
# - Account ID: 390402579286
# - Role name: [your-role-name]
# - CLI default client Region: us-east-1
# - CLI default output format: json

# Login (this will open browser)
aws sso login --profile [profile-name]
```

### For Access Keys:
```bash
# Configure with access keys
aws configure

# Enter:
# - AWS Access Key ID: [your-access-key]
# - AWS Secret Access Key: [your-secret-key]
# - Default region: us-east-1
# - Default output format: json
```

## Option 2: Environment Variables

### Create a batch file (Windows):
Create `set_aws_creds.bat`:
```batch
@echo off
set AWS_ACCESS_KEY_ID=your-access-key-here
set AWS_SECRET_ACCESS_KEY=your-secret-key-here
set AWS_SESSION_TOKEN=your-session-token-here
set AWS_DEFAULT_REGION=us-east-1
echo AWS credentials set for this session
```

### Create a PowerShell script:
Create `set_aws_creds.ps1`:
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-here"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key-here"
$env:AWS_SESSION_TOKEN="your-session-token-here"
$env:AWS_DEFAULT_REGION="us-east-1"
Write-Host "AWS credentials set for this session"
```

## Option 3: Credential File

### Edit ~/.aws/credentials:
```ini
[default]
aws_access_key_id = your-access-key-here
aws_secret_access_key = your-secret-key-here
aws_session_token = your-session-token-here
region = us-east-1
```

## Option 4: Quick Setup Script

Create a script that automatically sets credentials when you open a new terminal.

### For PowerShell Profile:
1. Find your PowerShell profile location:
   ```powershell
   $PROFILE
   ```

2. Edit the profile file and add:
   ```powershell
   # Auto-load AWS credentials
   if (Test-Path "C:\path\to\your\aws_creds.ps1") {
       . "C:\path\to\your\aws_creds.ps1"
   }
   ```

## Testing Credentials

After setting up, test with:
```bash
aws sts get-caller-identity
```

## Troubleshooting

### If credentials expire frequently:
- Use AWS SSO for longer-lasting sessions
- Set up credential refresh scripts
- Use AWS CLI profiles with role assumption

### For temporary credentials:
- Create a script to quickly paste and set credentials
- Use environment variable files that you can source
- Set up AWS credential helper tools