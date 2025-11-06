# 🪟 Windows Setup Guide - Instrument Diagnosis Assistant

This guide provides Windows-specific instructions for setting up and deploying the Instrument Diagnosis Assistant.

## 📋 Windows Prerequisites

### Required Software

1. **Python 3.9 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify installation: `python --version`

2. **AWS CLI**
   - Download from: https://aws.amazon.com/cli/
   - Or install via PowerShell: `winget install Amazon.AWSCLI`
   - Verify installation: `aws --version`

3. **Git for Windows**
   - Download from: https://git-scm.com/download/win
   - Or install via PowerShell: `winget install Git.Git`

4. **PowerShell 5.1 or higher** (usually pre-installed)
   - Check version: `$PSVersionTable.PSVersion`

### Optional but Recommended

1. **Windows Terminal**
   - Install from Microsoft Store or: `winget install Microsoft.WindowsTerminal`
   - Provides better PowerShell experience

2. **Visual Studio Code**
   - Download from: https://code.visualstudio.com/
   - Or install via PowerShell: `winget install Microsoft.VisualStudioCode`

## 🚀 Quick Windows Setup

### 1. Open PowerShell as Administrator

Right-click on PowerShell and select "Run as Administrator"

### 2. Set Execution Policy (if needed)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Clone and Setup Project

```powershell
# Clone the repository
git clone <repository-url>
cd instrument-diagnosis-assistant

# Install Python dependencies
pip install -r dev-requirements.txt

# Configure AWS CLI
aws configure
```

### 4. Choose Configuration

```powershell
# Copy configuration template (choose one)
Copy-Item deployment\dev-config.yaml config.yaml      # Development
Copy-Item deployment\test-config.yaml config.yaml     # Testing  
Copy-Item deployment\prod-config.yaml config.yaml     # Production
```

### 5. Run Deployment

```powershell
# Full automated deployment
.\scripts\deploy.ps1 -Region us-east-1 -Environment prod

# Or step by step:
# 1. Setup Knowledge Base
python scripts\setup-knowledge-base.py --region us-east-1 --config config.yaml

# 2. Deploy AgentCore
agentcore deploy --region us-east-1
```

## 🔧 Windows-Specific Configuration

### File Paths

Windows uses backslashes (`\`) for file paths, but the Python scripts handle this automatically. The configuration files use forward slashes (`/`) which work on both Windows and Unix systems.

### Environment Variables

Set environment variables in PowerShell:
```powershell
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_PROFILE = "default"
```

Or permanently via System Properties:
1. Right-click "This PC" → Properties
2. Advanced System Settings → Environment Variables
3. Add new variables under "User variables"

### PowerShell Script Parameters

The Windows deployment script supports these parameters:

```powershell
.\scripts\deploy.ps1 [parameters]

# Parameters:
-Region <string>        # AWS region (default: us-east-1)
-Environment <string>   # Environment type (default: dev)
-SkipKBSetup           # Skip Knowledge Base setup (switch)

# Examples:
.\scripts\deploy.ps1 -Region us-west-2 -Environment prod
.\scripts\deploy.ps1 -SkipKBSetup
```

### Testing the Script

Before running the deployment, you can test the PowerShell script syntax:

```powershell
# Test script syntax
powershell -Command "& { Get-Content 'scripts\deploy.ps1' | Out-Null; Write-Host 'Script syntax is valid' }"

# Run with WhatIf to see what would happen (dry run)
.\scripts\deploy.ps1 -Region us-east-1 -Environment dev -WhatIf
```

## 🐛 Windows-Specific Troubleshooting

### PowerShell Execution Policy Error

**Error:** `cannot be loaded because running scripts is disabled on this system`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found Error

**Error:** `'python' is not recognized as an internal or external command`

**Solutions:**
1. Reinstall Python with "Add to PATH" checked
2. Or use full path: `C:\Python39\python.exe`
3. Or add Python to PATH manually:
   - System Properties → Environment Variables
   - Edit PATH variable
   - Add Python installation directory

### AWS CLI Not Found

**Error:** `'aws' is not recognized as an internal or external command`

**Solutions:**
1. Restart PowerShell after AWS CLI installation
2. Add AWS CLI to PATH manually
3. Use full path: `C:\Program Files\Amazon\AWSCLIV2\aws.exe`

### Long Path Issues

Windows has a 260-character path limit that can cause issues.

**Solution:** Enable long paths in Windows 10/11:
1. Open Group Policy Editor (`gpedit.msc`)
2. Navigate to: Computer Configuration → Administrative Templates → System → Filesystem
3. Enable "Enable Win32 long paths"

Or via PowerShell (as Administrator):
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Antivirus Interference

Some antivirus software may interfere with Python scripts or AWS CLI.

**Solutions:**
1. Add project directory to antivirus exclusions
2. Temporarily disable real-time protection during setup
3. Use Windows Defender exclusions:
   - Windows Security → Virus & threat protection
   - Manage settings → Add or remove exclusions

## 📁 Windows File Structure

The project structure on Windows:
```
instrument-diagnosis-assistant\
├── scripts\
│   ├── deploy.ps1              # Windows deployment script
│   ├── deploy.sh               # Linux/macOS deployment script
│   └── setup-knowledge-base.py # Cross-platform Python script
├── deployment\
│   ├── dev-config.yaml
│   ├── test-config.yaml
│   └── prod-config.yaml
├── config.yaml                 # Your active configuration
└── ...
```

## 🔄 Windows Development Workflow

### 1. Daily Development

```powershell
# Navigate to project
cd C:\path\to\instrument-diagnosis-assistant

# Activate virtual environment (if using)
.\venv\Scripts\Activate.ps1

# Run local development (recommended - uses configured port)
python run_app.py --app app.py          # Basic version (port 8501)
python run_app.py --app app_oauth.py    # OAuth version (port 8501)

# Or use convenience script
start.bat dev app.py

# Or run directly with Streamlit (manual port specification)
streamlit run app.py --server.port 8501
streamlit run app_oauth.py --server.port 8501

# Override port if needed
python run_app.py --app app.py --port 8505
```

### 2. Testing Changes

```powershell
# Run tests
python -m pytest tests\

# Check code formatting
black --check .

# Run linting
flake8 .
```

### 3. Deployment Updates

```powershell
# Update configuration
notepad config.yaml

# Redeploy
agentcore deploy --region us-east-1

# Check logs
agentcore logs --region us-east-1
```

## 🎯 Windows Performance Tips

### 1. Use SSD Storage
- Install project on SSD for better performance
- Avoid network drives for development

### 2. Windows Defender Exclusions
- Add project directory to Windows Defender exclusions
- Exclude Python installation directory

### 3. PowerShell Profile
Create a PowerShell profile for common aliases:

```powershell
# Check if profile exists
Test-Path $PROFILE

# Create profile if it doesn't exist
New-Item -ItemType File -Path $PROFILE -Force

# Edit profile
notepad $PROFILE
```

Add to profile:
```powershell
# Aliases for common commands
Set-Alias -Name ll -Value Get-ChildItem
Set-Alias -Name grep -Value Select-String

# Function for quick navigation
function cdida { Set-Location "C:\path\to\instrument-diagnosis-assistant" }

# AWS profile shortcuts
function aws-dev { $env:AWS_PROFILE = "dev" }
function aws-prod { $env:AWS_PROFILE = "prod" }
```

## 📞 Windows-Specific Support

### Common Windows Issues

1. **Path Length Limitations**: Enable long paths as described above
2. **Permission Issues**: Run PowerShell as Administrator when needed
3. **Firewall Blocking**: Allow Python and AWS CLI through Windows Firewall
4. **Encoding Issues**: Use UTF-8 encoding in text editors

### Getting Help

1. **Windows-specific issues**: Check Windows Event Viewer for system errors
2. **PowerShell help**: Use `Get-Help <command>` for PowerShell commands
3. **AWS CLI help**: Use `aws help` or `aws <service> help`

### Useful Windows Commands

```powershell
# Check system information
Get-ComputerInfo

# Check installed software
Get-WmiObject -Class Win32_Product | Select-Object Name, Version

# Check running processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"}

# Check network connectivity
Test-NetConnection -ComputerName amazonaws.com -Port 443

# Check environment variables
Get-ChildItem Env: | Where-Object {$_.Name -like "*AWS*"}
```

---

**Windows Version Compatibility:**
- Windows 10 (version 1903 or later)
- Windows 11 (all versions)
- Windows Server 2019/2022

**Last Updated:** November 2025  
**For Windows-specific support:** Contact your system administrator