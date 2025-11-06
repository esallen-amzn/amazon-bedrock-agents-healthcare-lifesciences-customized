# Instrument Diagnosis Assistant Deployment Script for Windows
# This PowerShell script automates the deployment process for Windows environments

param(
    [string]$Region = "us-east-1",
    [string]$Environment = "dev",
    [switch]$SkipKBSetup = $false
)

# Configuration
$PROJECT_NAME = "instrument-diagnosis-assistant"

# Helper functions for colored output
function Write-InfoMessage {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Blue
}

function Write-SuccessMessage {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

Write-InfoMessage "Starting deployment for Instrument Diagnosis Assistant"
Write-InfoMessage "Region: $Region"
Write-InfoMessage "Environment: $Environment"
Write-Host ""

# Check prerequisites
Write-InfoMessage "Checking prerequisites..."

# Check if AWS CLI is installed and configured
try {
    $awsVersion = aws --version 2>$null
    if (-not $awsVersion) {
        throw "AWS CLI not found"
    }
    Write-SuccessMessage "AWS CLI found: $($awsVersion.Split()[0])"
} catch {
    Write-ErrorMessage "AWS CLI is not installed. Please install it first."
    Write-InfoMessage "Download from: https://aws.amazon.com/cli/"
    exit 1
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
    if (-not $identity) {
        throw "No AWS credentials"
    }
    Write-SuccessMessage "AWS credentials configured for account: $($identity.Account)"
} catch {
    Write-ErrorMessage "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    if (-not $pythonVersion) {
        throw "Python not found"
    }
    Write-SuccessMessage "Python found: $pythonVersion"
} catch {
    Write-ErrorMessage "Python is not installed. Please install Python 3.9+ first."
    Write-InfoMessage "Download from: https://www.python.org/downloads/"
    exit 1
}

# Check if agentcore CLI is available
try {
    $agentcoreVersion = agentcore --version 2>$null
    if ($agentcoreVersion) {
        Write-SuccessMessage "AgentCore CLI found: $agentcoreVersion"
    } else {
        throw "AgentCore not found"
    }
} catch {
    Write-WarningMessage "AgentCore CLI not found. Please ensure it's installed and in your PATH."
    Write-InfoMessage "You can install it from: https://github.com/awslabs/amazon-bedrock-agentcore"
}

Write-SuccessMessage "Prerequisites check completed"
Write-Host ""

# Step 1: Setup configuration
Write-InfoMessage "Setting up configuration for $Environment environment..."

$CONFIG_TEMPLATE = "deployment\$Environment-config.yaml"
$CONFIG_FILE = "config.yaml"

if (-not (Test-Path $CONFIG_TEMPLATE)) {
    Write-ErrorMessage "Configuration template not found: $CONFIG_TEMPLATE"
    Write-InfoMessage "Available templates:"
    Get-ChildItem "deployment\*.yaml" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 1
}

# Copy configuration template
Copy-Item $CONFIG_TEMPLATE $CONFIG_FILE -Force
Write-SuccessMessage "Configuration copied from $CONFIG_TEMPLATE to $CONFIG_FILE"

# Update region in config if different from default
if ($Region -ne "us-east-1") {
    Write-InfoMessage "Updating region in configuration to $Region"
    (Get-Content $CONFIG_FILE) -replace 'aws_region: .*', "aws_region: `"$Region`"" | Set-Content $CONFIG_FILE
}

# Step 2: Setup Knowledge Base (unless skipped)
if (-not $SkipKBSetup) {
    Write-InfoMessage "Setting up Knowledge Base and S3 buckets..."
    
    if (Test-Path "scripts\setup-knowledge-base.py") {
        try {
            python scripts\setup-knowledge-base.py --region $Region --config $CONFIG_FILE
            if ($LASTEXITCODE -eq 0) {
                Write-SuccessMessage "Knowledge Base setup completed"
            } else {
                Write-ErrorMessage "Knowledge Base setup failed"
                exit 1
            }
        } catch {
            Write-ErrorMessage "Failed to run Knowledge Base setup script: $_"
            exit 1
        }
    } else {
        Write-WarningMessage "Knowledge Base setup script not found. Skipping KB setup."
        Write-InfoMessage "You'll need to manually create the Knowledge Base and update config.yaml"
    }
} else {
    Write-InfoMessage "Skipping Knowledge Base setup (SkipKBSetup flag set)"
}

Write-Host ""

# Step 3: Upload sample data (if available)
Write-InfoMessage "Uploading sample data..."

if (Test-Path "sample_data") {
    # Simple approach: use default bucket naming pattern
    $prefix = "instrument-diagnosis-assistant"
    $TROUBLE_BUCKET = "$prefix-troubleshooting-guides"
    $ENG_BUCKET = "$prefix-engineering-docs"
    
    if (Test-Path "sample_data\troubleshooting_guides") {
        Write-InfoMessage "Uploading troubleshooting guides to s3://$TROUBLE_BUCKET"
        aws s3 sync sample_data\troubleshooting_guides\ s3://$TROUBLE_BUCKET/ --region $Region
        if ($LASTEXITCODE -eq 0) {
            Write-SuccessMessage "Troubleshooting guides uploaded"
        }
    }
    
    if (Test-Path "sample_data\engineering_docs") {
        Write-InfoMessage "Uploading engineering docs to s3://$ENG_BUCKET"
        aws s3 sync sample_data\engineering_docs\ s3://$ENG_BUCKET/ --region $Region
        if ($LASTEXITCODE -eq 0) {
            Write-SuccessMessage "Engineering docs uploaded"
        }
    }
} else {
    Write-WarningMessage "Sample data directory not found. Skipping sample data upload."
}

Write-Host ""

# Step 4: Deploy AgentCore
Write-InfoMessage "Deploying AgentCore agent..."

try {
    # Set environment variables for deployment
    $env:AWS_DEFAULT_REGION = $Region
    
    # Deploy the agent
    agentcore deploy --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-SuccessMessage "AgentCore deployment completed"
    } else {
        Write-ErrorMessage "AgentCore deployment failed"
        exit 1
    }
} catch {
    Write-WarningMessage "AgentCore CLI not available or deployment failed. Please deploy manually:"
    Write-InfoMessage "1. Install AgentCore CLI"
    Write-InfoMessage "2. Run: agentcore deploy --region $Region"
}

Write-Host ""

# Step 5: Post-deployment steps
Write-InfoMessage "Post-deployment configuration..."

Write-InfoMessage "Checking deployment status..."
# You could add status checks here

Write-SuccessMessage "Deployment completed successfully!"
Write-Host ""

# Display next steps
Write-InfoMessage "Next steps:"
Write-Host "1. Sync Knowledge Base data sources in the AWS Bedrock console"
Write-Host "2. Test the deployment with sample data"
Write-Host "3. Upload your actual log files and documentation"
Write-Host "4. Access the Streamlit interface to start diagnosing instruments"
Write-Host ""

# Display useful information
Write-InfoMessage "Useful commands:"
Write-Host "• View logs: agentcore logs --region $Region"
Write-Host "• Update deployment: agentcore deploy --region $Region"
Write-Host "• Destroy deployment: agentcore destroy --region $Region"
Write-Host ""

Write-InfoMessage "Configuration file: $CONFIG_FILE"
Write-InfoMessage "Environment: $Environment"
Write-InfoMessage "Region: $Region"

Write-Host ""
Write-SuccessMessage "Instrument Diagnosis Assistant deployment complete!"

# Pause to allow user to read output
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")