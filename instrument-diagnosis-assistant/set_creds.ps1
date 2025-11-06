# Quick AWS Credential Setup Script
# Usage: .\set_creds.ps1

Write-Host "=== AWS Credential Setup ===" -ForegroundColor Cyan
Write-Host "Paste your AWS credentials below (press Enter after each):" -ForegroundColor Yellow

# Prompt for credentials
$accessKey = Read-Host "AWS Access Key ID"
$secretKey = Read-Host "AWS Secret Access Key" -AsSecureString
$sessionToken = Read-Host "AWS Session Token (if using temporary credentials)"

# Convert secure string back to plain text for environment variable
$secretKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretKey))

# Set environment variables
$env:AWS_ACCESS_KEY_ID = $accessKey
$env:AWS_SECRET_ACCESS_KEY = $secretKeyPlain
if ($sessionToken) {
    $env:AWS_SESSION_TOKEN = $sessionToken
}
$env:AWS_DEFAULT_REGION = "us-east-1"

Write-Host "✅ AWS credentials set for this PowerShell session!" -ForegroundColor Green
Write-Host "Testing credentials..." -ForegroundColor Yellow

# Test credentials
try {
    $identity = aws sts get-caller-identity 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credentials are valid!" -ForegroundColor Green
        $identity | ConvertFrom-Json | Format-Table
    } else {
        Write-Host "❌ Credential test failed. Please check your credentials." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error testing credentials: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nYou can now run your AgentCore commands in this window." -ForegroundColor Cyan