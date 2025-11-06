# 🔧 Instrument Diagnosis Assistant - Deployment Guide

This guide provides comprehensive instructions for deploying and transferring the Instrument Diagnosis Assistant to customer environments.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Knowledge Base Setup](#knowledge-base-setup)
6. [Deployment](#deployment)
7. [Testing](#testing)
8. [Customer Transfer](#customer-transfer)
9. [Troubleshooting](#troubleshooting)

## 🚀 Prerequisites

### AWS Requirements
- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Access to Amazon Bedrock with Nova models enabled
- Sufficient service quotas for:
  - Amazon Bedrock (Nova Pro, Nova Canvas)
  - Amazon Bedrock Knowledge Bases
  - Amazon S3
  - AWS Lambda (for AgentCore)

### Software Requirements
- Python 3.9 or higher https://github.com/awslabs/amazon-bedrock-agentcore)
- AgentCore CLI (install from:
- Git (for version control)

### Permissions Required
The deploying user/role needs the following AWS permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "bedrock-agent:*",
                "s3:*",
                "iam:CreateRole",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy",
                "lambda:*",
                "apigateway:*",
                "cognito-idp:*",
                "opensearch:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## ⚡ Quick Start

For experienced users who want to deploy quickly:

### Linux/macOS:
```bash
# 1. Clone and navigate to the project
cd instrument-diagnosis-assistant

# 2. Choose your environment and copy configuration
cp deployment/prod-config.yaml config.yaml

# 3. Run automated deployment
bash scripts/deploy.sh us-east-1 prod

# 4. Access the application
# URL will be provided after deployment completes
```

### Windows (PowerShell):
```powershell
# 1. Clone and navigate to the project
cd instrument-diagnosis-assistant

# 2. Choose your environment and copy configuration
Copy-Item deployment\prod-config.yaml config.yaml

# 3. Run automated deployment
.\scripts\deploy.ps1 -Region us-east-1 -Environment prod

# 4. Access the application
# URL will be provided after deployment completes
```

## 🔧 Detailed Setup

### Step 1: Environment Preparation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd instrument-diagnosis-assistant
   ```

2. **Install Dependencies**
   ```bash
   pip install -r dev-requirements.txt
   ```

3. **Configure AWS CLI**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, Region, and Output format
   ```

4. **Verify Bedrock Access**
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

### Step 2: Configuration Selection

Choose the appropriate configuration template based on your environment:

- **Development**: `deployment/dev-config.yaml`
- **Testing**: `deployment/test-config.yaml`  
- **Production**: `deployment/prod-config.yaml`

Copy your chosen template to `config.yaml`:

**Linux/macOS:**
```bash
cp deployment/prod-config.yaml config.yaml
```

**Windows:**
```powershell
Copy-Item deployment\prod-config.yaml config.yaml
```

### Step 3: Customize Configuration

Edit `config.yaml` to match your requirements:

```yaml
# Key settings to customize:
deployment:
  aws_region: "us-east-1"  # Your preferred region
  environment: "production"  # or "development", "test"
  
  # Streamlit configuration
  streamlit:
    port: 8503  # Configurable port (8501=dev, 8503=prod, 8504=test)
    host: "0.0.0.0"  # "localhost" for local, "0.0.0.0" for external access

models:
  text_model: "us.amazon.nova-pro-v1:0"
  multimodal_model: "us.amazon.nova-canvas-v1:0"

# Adjust thresholds based on your accuracy requirements
log_analysis:
  confidence_threshold: 0.75  # Higher = more conservative
  failure_threshold: 0.8
```

## 🧠 Knowledge Base Setup

The Knowledge Base stores troubleshooting guides and engineering documentation for intelligent retrieval.

### Automated Setup

Run the Knowledge Base setup script:

**Linux/macOS:**
```bash
python3 scripts/setup-knowledge-base.py --region us-east-1 --config config.yaml
```

**Windows:**
```powershell
python scripts\setup-knowledge-base.py --region us-east-1 --config config.yaml
```

This script will:
- Create S3 buckets for data storage
- Set up IAM roles and policies
- Create the Bedrock Knowledge Base
- Configure data sources
- Update your config.yaml with the Knowledge Base ID

### Manual Setup (if automated setup fails)

1. **Create S3 Buckets**
   ```bash
   aws s3 mb s3://your-prefix-troubleshooting-guides --region us-east-1
   aws s3 mb s3://your-prefix-engineering-docs --region us-east-1
   ```

2. **Create Knowledge Base in AWS Console**
   - Go to Amazon Bedrock > Knowledge Bases
   - Click "Create knowledge base"
   - Choose "Create and use a new service role"
   - Select "Quick create a new vector store"
   - Use embedding model: `amazon.titan-embed-text-v2:0`

3. **Add Data Sources**
   - Add S3 data source pointing to your troubleshooting guides bucket
   - Add S3 data source pointing to your engineering docs bucket
   - Configure chunking: Fixed size, 512 tokens, 20% overlap

4. **Update Configuration**
   Add the Knowledge Base ID to your `config.yaml`:
   ```yaml
   knowledge_base:
     kb_id: "YOUR_KB_ID_HERE"
   ```

## 🚀 Deployment

### Option 1: Automated Deployment

Use the provided deployment script:

**Linux/macOS:**
```bash
# Full deployment with Knowledge Base setup
bash scripts/deploy.sh us-east-1 prod

# Skip Knowledge Base setup (if already done)
bash scripts/deploy.sh us-east-1 prod true
```

**Windows (PowerShell):**
```powershell
# Full deployment with Knowledge Base setup
.\scripts\deploy.ps1 -Region us-east-1 -Environment prod

# Skip Knowledge Base setup (if already done)
.\scripts\deploy.ps1 -Region us-east-1 -Environment prod -SkipKBSetup
```

### Option 2: Manual Deployment

1. **Deploy AgentCore**
   ```bash
   agentcore deploy --region us-east-1
   ```

2. **Upload Sample Data** (optional)
   ```bash
   aws s3 sync sample_data/troubleshooting_guides/ s3://your-troubleshooting-bucket/
   aws s3 sync sample_data/engineering_docs/ s3://your-engineering-bucket/
   ```

3. **Sync Knowledge Base**
   - Go to Bedrock Console > Knowledge Bases
   - Select your Knowledge Base
   - Click "Sync" for each data source

## 🧪 Testing

### Basic Functionality Test

1. **Access the Application**
   - Get the application URL from AgentCore deployment output
   - Open in web browser

2. **Upload Test Files**
   - Upload sample log files from `sample_data/`
   - Upload engineering documentation
   - Upload troubleshooting guides

3. **Run Diagnosis**
   - Click "Full Diagnosis" button
   - Verify the system provides pass/fail determination
   - Check confidence levels and recommendations

### Automated Testing

Run the test scenarios:
```bash
python3 scripts/run-tests.py --config config.yaml --environment test
```

## 📦 Customer Transfer

### Transfer Package Contents

Provide customers with:

1. **Source Code**
   - Complete `instrument-diagnosis-assistant/` directory
   - All configuration templates
   - Sample data for testing

2. **Documentation**
   - This deployment guide
   - User manual (`USER_GUIDE.md`)
   - API documentation
   - Troubleshooting guide

3. **Configuration Templates**
   - Environment-specific configs in `deployment/`
   - Sample `.agentcore.yaml`

### Customer Transfer Checklist

**Pre-Transfer:**
- [ ] Verify all AWS prerequisites are met
- [ ] Confirm Bedrock model access in target region
- [ ] Test deployment in similar environment
- [ ] Prepare customer-specific configuration

**During Transfer:**
- [ ] Walk through deployment process
- [ ] Verify Knowledge Base setup
- [ ] Test with customer's sample data
- [ ] Configure authentication (OAuth/Cognito)
- [ ] Set up monitoring and logging

**Post-Transfer:**
- [ ] Provide training on system usage
- [ ] Document any customizations made
- [ ] Establish support procedures
- [ ] Schedule follow-up reviews

### Customer Onboarding Steps

1. **Environment Setup** (Customer)
   - AWS account preparation
   - IAM permissions configuration
   - Bedrock model access enablement

2. **Deployment** (Joint)
   - Run deployment scripts together
   - Verify each step completes successfully
   - Test basic functionality

3. **Data Migration** (Customer)
   - Upload actual log files and documentation
   - Sync Knowledge Base data sources
   - Validate data processing

4. **Customization** (Joint)
   - Adjust confidence thresholds
   - Configure component recognition rules
   - Set up monitoring and alerts

5. **Training** (Joint)
   - System usage training
   - Troubleshooting procedures
   - Maintenance tasks

## 🔍 Troubleshooting

### Common Issues

**1. Bedrock Model Access Denied**
```
Error: Access denied to model us.amazon.nova-pro-v1:0
```
**Solution:** Enable Nova models in Bedrock console for your region

**2. Knowledge Base Creation Fails**
```
Error: Insufficient permissions to create OpenSearch collection
```
**Solution:** Ensure IAM user has OpenSearch permissions or use admin role

**3. S3 Bucket Access Issues**
```
Error: Access denied to S3 bucket
```
**Solution:** Check bucket policies and IAM permissions

**4. AgentCore Deployment Timeout**
```
Error: Deployment timed out after 10 minutes
```
**Solution:** Check CloudFormation console for detailed error messages

### Diagnostic Commands

```bash
# Check AWS credentials and permissions
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1

# Verify AgentCore installation
agentcore --version
agentcore list --region us-east-1

# Check Knowledge Base status
aws bedrock-agent list-knowledge-bases --region us-east-1

# View deployment logs
agentcore logs --region us-east-1
```

### Log Locations

- **AgentCore Logs**: Available via `agentcore logs` command
- **Lambda Logs**: CloudWatch Logs (search for function name)
- **Knowledge Base Logs**: CloudWatch Logs (bedrock-agent group)

### Support Contacts

For deployment issues:
1. Check this troubleshooting guide
2. Review AWS CloudFormation events
3. Contact AWS Support for service-specific issues
4. Escalate to development team for application issues

## 📊 Monitoring and Maintenance

### Key Metrics to Monitor

- **Response Time**: Average time for diagnosis completion
- **Accuracy**: Confidence levels and user feedback
- **Usage**: Number of diagnoses per day/week
- **Errors**: Failed requests and error rates

### Regular Maintenance Tasks

- **Weekly**: Review error logs and user feedback
- **Monthly**: Update Knowledge Base with new documentation
- **Quarterly**: Review and adjust confidence thresholds
- **Annually**: Update to latest Bedrock models and features

### Backup and Recovery

- **Configuration**: Store `config.yaml` in version control
- **Knowledge Base**: Regular S3 bucket backups
- **User Data**: Implement data retention policies

---

## 📞 Support Information

- **Documentation**: See `USER_GUIDE.md` for end-user instructions
- **Technical Issues**: Check CloudWatch logs and error messages
- **Feature Requests**: Contact development team
- **AWS Service Issues**: Use AWS Support

**Deployment Version**: 1.0.0  
**Last Updated**: November 2025  
**Compatible Regions**: us-east-1, us-west-2, eu-west-1