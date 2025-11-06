@echo off
echo === AWS Credential Setup ===
echo.
echo Paste your AWS credentials below:
echo.

set /p AWS_ACCESS_KEY_ID="AWS Access Key ID: "
set /p AWS_SECRET_ACCESS_KEY="AWS Secret Access Key: "
set /p AWS_SESSION_TOKEN="AWS Session Token (optional): "
set AWS_DEFAULT_REGION=us-east-1

echo.
echo ✅ AWS credentials set for this session!
echo Testing credentials...

aws sts get-caller-identity
if %errorlevel% equ 0 (
    echo ✅ Credentials are valid!
) else (
    echo ❌ Credential test failed. Please check your credentials.
)

echo.
echo You can now run your AgentCore commands in this window.
pause