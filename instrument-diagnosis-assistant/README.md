# 🔧 Instrument Diagnosis Assistant

An AI-powered system for analyzing instrument logs and providing troubleshooting guidance using Amazon Nova models and Bedrock Knowledge Bases.

## 🎯 Overview

The Instrument Diagnosis Assistant helps technicians diagnose instrument failures by:
- **Log Analysis**: Compare failed unit logs against gold standard patterns
- **Component Recognition**: Identify hardware/software components from documentation  
- **Multi-modal Processing**: Analyze troubleshooting guides with text, images, and diagrams
- **Cross-source Correlation**: Correlate information across logs, documentation, and guides
- **Diagnosis Generation**: Provide clear pass/fail determinations with confidence levels

## ⚡ Quick Start

### Linux/macOS:
```bash
# 1. Install dependencies
pip install -r dev-requirements.txt

# 2. Configure AWS
aws configure

# 3. Copy configuration template
cp deployment/prod-config.yaml config.yaml

# 4. Run automated deployment
bash scripts/deploy.sh us-east-1 prod
```

### Windows (PowerShell):
```powershell
# 1. Install dependencies
pip install -r dev-requirements.txt

# 2. Configure AWS
aws configure

# 3. Copy configuration template
Copy-Item deployment\prod-config.yaml config.yaml

# 4. Run automated deployment
.\scripts\deploy.ps1 -Region us-east-1 -Environment prod
```

## 🖥️ Local Development

For local development and testing:

### Linux/macOS:
```bash
# 1. Install dependencies
pip install -r dev-requirements.txt

# 2. Copy development configuration
cp deployment/dev-config.yaml config.yaml

# 3. Run the application
python run_app.py --app app.py          # Basic version
python run_app.py --app app_oauth.py    # OAuth version

# Or use convenience script
./start.sh dev app.py
```

### Windows:
```powershell
# 1. Install dependencies
pip install -r dev-requirements.txt

# 2. Copy development configuration
Copy-Item deployment\dev-config.yaml config.yaml

# 3. Run the application
python run_app.py --app app.py          # Basic version
python run_app.py --app app_oauth.py    # OAuth version

# Or use convenience script
start.bat dev app.py
```

### Port Configuration

The application uses configurable ports to avoid conflicts:
- **Development**: Port 8501 (localhost) - Streamlit default
- **Testing**: Port 8504 (localhost)  
- **Production**: Port 8503 (0.0.0.0)

You can override the port with: `python run_app.py --port 8505`

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete setup and deployment instructions
- **[Windows Setup Guide](WINDOWS_SETUP.md)** - Windows-specific setup instructions
- **[User Guide](USER_GUIDE.md)** - End-user instructions and best practices
- **[Customer Transfer Checklist](CUSTOMER_TRANSFER_CHECKLIST.md)** - Customer onboarding guide
- **[Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions

## 🏗️ Architecture

### Core Components
- **Amazon Nova Pro**: Primary text analysis and reasoning model
- **Amazon Nova Canvas**: Multi-modal document processing for images and diagrams
- **Bedrock Knowledge Base**: Stores troubleshooting guides and engineering documentation
- **AgentCore**: Orchestrates the AI agent and provides web interface
- **Streamlit UI**: User-friendly interface for file uploads and diagnosis results

### Data Flow
1. **Upload**: Users upload log files, documentation, and troubleshooting guides
2. **Processing**: Nova models analyze text and visual content
3. **Correlation**: System correlates information across multiple data sources
4. **Diagnosis**: AI provides pass/fail determination with confidence levels
5. **Guidance**: System offers specific recommendations and next steps

## 🔧 Configuration

The system uses environment-specific configuration files:

- **Development**: `deployment/dev-config.yaml` - Lower thresholds, debug logging
- **Testing**: `deployment/test-config.yaml` - Validation scenarios, moderate settings  
- **Production**: `deployment/prod-config.yaml` - Optimized for accuracy and performance

Key configuration options:
```yaml
models:
  text_model: "us.amazon.nova-pro-v1:0"
  multimodal_model: "us.amazon.nova-canvas-v1:0"

log_analysis:
  confidence_threshold: 0.75
  failure_threshold: 0.8
  max_file_size_mb: 500

knowledge_base:
  kb_id: "your-kb-id"  # Set during deployment
  retrieval_config:
    max_results: 15
    score_threshold: 0.75
```

## 📁 Project Structure

```
instrument-diagnosis-assistant/
├── agent/                          # Agent configuration and tools
│   ├── agent_config/
│   │   ├── tools/                  # Custom analysis tools
│   │   ├── agent.py               # Main agent logic
│   │   └── config_manager.py      # Configuration management
├── app_modules/                    # Streamlit UI components (OAuth)
├── scripts/                        # Deployment and setup scripts
│   ├── deploy.sh                  # Linux/macOS deployment
│   ├── deploy.ps1                 # Windows deployment
│   └── setup-knowledge-base.py    # Knowledge Base setup
├── deployment/                     # Environment configurations
│   ├── dev-config.yaml
│   ├── test-config.yaml
│   └── prod-config.yaml
├── sample_data/                    # Sample files for testing
│   ├── failed_unit_logs/
│   ├── engineering_docs/
│   └── troubleshooting_guides/
├── app.py                         # Main Streamlit application
├── app_oauth.py                   # OAuth-enabled application
├── .agentcore.yaml               # AgentCore deployment configuration
└── config.yaml                   # Active configuration (copied from deployment/)
```

## 🚀 Features

### File Processing
- **Large File Support**: Process log files up to 500MB
- **Multi-format Support**: PDF, DOC, images, text files
- **Chunked Analysis**: Efficient processing of large datasets
- **Batch Upload**: Upload multiple files simultaneously

### AI Analysis
- **Log Comparison**: Compare failed logs against gold standards
- **Component Recognition**: Extract component information from documentation
- **Visual Analysis**: Process images and diagrams in troubleshooting guides
- **Cross-correlation**: Find relationships across different data sources

### User Interface
- **Intuitive Upload**: Drag-and-drop file upload with progress indicators
- **Real-time Results**: Live diagnosis results with confidence scoring
- **Quick Actions**: Pre-configured analysis buttons for common tasks
- **Interactive Chat**: Ask follow-up questions and get clarifications

### Deployment Options
- **Multiple Environments**: Dev, test, and production configurations
- **Cross-platform**: Support for Windows, Linux, and macOS
- **Automated Setup**: One-command deployment with Knowledge Base creation
- **OAuth Integration**: Secure authentication with AWS Cognito

## 🔍 Sample Data

The project includes sample data for testing:

- **Failed Unit Logs**: Example log files showing various failure patterns
- **Engineering Docs**: Component specifications and system architecture
- **Troubleshooting Guides**: Multi-modal guides with images and procedures

Use sample data to:
1. Test the system after deployment
2. Train users on the interface
3. Validate analysis accuracy
4. Demonstrate capabilities to stakeholders

## 🤝 Contributing

1. Follow the existing code structure and naming conventions
2. Add tests for new functionality
3. Update documentation for any changes
4. Test on both Windows and Unix systems
5. Ensure compatibility with all environment configurations

## 📞 Support

- **Setup Issues**: See [Deployment Guide](DEPLOYMENT_GUIDE.md) and [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- **Windows-specific**: See [Windows Setup Guide](WINDOWS_SETUP.md)
- **User Questions**: See [User Guide](USER_GUIDE.md)
- **Customer Transfer**: See [Customer Transfer Checklist](CUSTOMER_TRANSFER_CHECKLIST.md)

---

**Version**: 1.0.0  
**Compatible Regions**: us-east-1, us-west-2, eu-west-1  
**Requirements**: Python 3.9+, AWS CLI, AgentCore CLI
