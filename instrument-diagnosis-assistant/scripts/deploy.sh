#!/bin/bash

# Instrument Diagnosis Assistant Deployment Script
# This script automates the deployment process for the Instrument Diagnosis Assistant

set -e  # Exit on any error

# Configuration
PROJECT_NAME="instrument-diagnosis-assistant"
DEFAULT_REGION="us-east-1"
DEFAULT_ENV="dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Parse command line arguments
REGION=${1:-$DEFAULT_REGION}
ENVIRONMENT=${2:-$DEFAULT_ENV}
SKIP_KB_SETUP=${3:-false}

log_info "Starting deployment for Instrument Diagnosis Assistant"
log_info "Region: $REGION"
log_info "Environment: $ENVIRONMENT"
echo

# Check prerequisites
log_info "Checking prerequisites..."

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if agentcore CLI is available
if ! command -v agentcore &> /dev/null; then
    log_warning "AgentCore CLI not found. Please ensure it's installed and in your PATH."
    log_info "You can install it from: https://github.com/awslabs/amazon-bedrock-agentcore"
fi

log_success "Prerequisites check completed"
echo

# Step 1: Setup configuration
log_info "Setting up configuration for $ENVIRONMENT environment..."

CONFIG_TEMPLATE="deployment/${ENVIRONMENT}-config.yaml"
CONFIG_FILE="config.yaml"

if [ ! -f "$CONFIG_TEMPLATE" ]; then
    log_error "Configuration template not found: $CONFIG_TEMPLATE"
    log_info "Available templates:"
    ls -la deployment/*.yaml 2>/dev/null || log_warning "No configuration templates found"
    exit 1
fi

# Copy configuration template
cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
log_success "Configuration copied from $CONFIG_TEMPLATE to $CONFIG_FILE"

# Update region in config if different from default
if [ "$REGION" != "$DEFAULT_REGION" ]; then
    log_info "Updating region in configuration to $REGION"
    # Use sed to update the region (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/aws_region: .*/aws_region: \"$REGION\"/" "$CONFIG_FILE"
    else
        sed -i "s/aws_region: .*/aws_region: \"$REGION\"/" "$CONFIG_FILE"
    fi
fi

# Step 2: Setup Knowledge Base (unless skipped)
if [ "$SKIP_KB_SETUP" != "true" ]; then
    log_info "Setting up Knowledge Base and S3 buckets..."
    
    if [ -f "scripts/setup-knowledge-base.py" ]; then
        python3 scripts/setup-knowledge-base.py --region "$REGION" --config "$CONFIG_FILE"
        if [ $? -eq 0 ]; then
            log_success "Knowledge Base setup completed"
        else
            log_error "Knowledge Base setup failed"
            exit 1
        fi
    else
        log_warning "Knowledge Base setup script not found. Skipping KB setup."
        log_info "You'll need to manually create the Knowledge Base and update config.yaml"
    fi
else
    log_info "Skipping Knowledge Base setup (SKIP_KB_SETUP=true)"
fi

echo

# Step 3: Upload sample data (if available)
log_info "Uploading sample data..."

if [ -d "sample_data" ]; then
    # Read S3 bucket names from config (this is a simplified approach)
    TROUBLE_BUCKET=$(grep -A 10 "s3_buckets:" "$CONFIG_FILE" | grep "troubleshooting-guides:" | cut -d'"' -f2 2>/dev/null || echo "")
    ENG_BUCKET=$(grep -A 10 "s3_buckets:" "$CONFIG_FILE" | grep "engineering-docs:" | cut -d'"' -f2 2>/dev/null || echo "")
    
    if [ -n "$TROUBLE_BUCKET" ] && [ -d "sample_data/troubleshooting_guides" ]; then
        log_info "Uploading troubleshooting guides to s3://$TROUBLE_BUCKET"
        aws s3 sync sample_data/troubleshooting_guides/ s3://$TROUBLE_BUCKET/ --region "$REGION"
        log_success "Troubleshooting guides uploaded"
    fi
    
    if [ -n "$ENG_BUCKET" ] && [ -d "sample_data/engineering_docs" ]; then
        log_info "Uploading engineering docs to s3://$ENG_BUCKET"
        aws s3 sync sample_data/engineering_docs/ s3://$ENG_BUCKET/ --region "$REGION"
        log_success "Engineering docs uploaded"
    fi
else
    log_warning "Sample data directory not found. Skipping sample data upload."
fi

echo

# Step 4: Deploy AgentCore
log_info "Deploying AgentCore agent..."

if command -v agentcore &> /dev/null; then
    # Set environment variables for deployment
    export AWS_DEFAULT_REGION="$REGION"
    
    # Deploy the agent
    agentcore deploy --region "$REGION"
    
    if [ $? -eq 0 ]; then
        log_success "AgentCore deployment completed"
    else
        log_error "AgentCore deployment failed"
        exit 1
    fi
else
    log_warning "AgentCore CLI not available. Please deploy manually:"
    log_info "1. Install AgentCore CLI"
    log_info "2. Run: agentcore deploy --region $REGION"
fi

echo

# Step 5: Post-deployment steps
log_info "Post-deployment configuration..."

log_info "Checking deployment status..."
# You could add status checks here

log_success "Deployment completed successfully!"
echo

# Display next steps
log_info "Next steps:"
echo "1. 📚 Sync Knowledge Base data sources in the AWS Bedrock console"
echo "2. 🧪 Test the deployment with sample data"
echo "3. 📊 Upload your actual log files and documentation"
echo "4. 🔧 Access the Streamlit interface to start diagnosing instruments"
echo

# Display useful information
log_info "Useful commands:"
echo "• View logs: agentcore logs --region $REGION"
echo "• Update deployment: agentcore deploy --region $REGION"
echo "• Destroy deployment: agentcore destroy --region $REGION"
echo

log_info "Configuration file: $CONFIG_FILE"
log_info "Environment: $ENVIRONMENT"
log_info "Region: $REGION"

echo
log_success "🎉 Instrument Diagnosis Assistant deployment complete!"