# Quick Start Guide - macOS

## Prerequisites

✅ Python 3.12+ installed  
✅ Virtual environment activated  
✅ Dependencies installed from `dev-requirements.txt`

## Installation

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip3 install -r dev-requirements.txt

# 3. Verify installation
python3 -c "import streamlit; import bedrock_agentcore; print('✅ Ready!')"
```

## Starting the Application

### Option 1: Quick Start (Recommended)
```bash
./start.sh dev app.py
```

### Option 2: OAuth Authentication
```bash
./start.sh dev app_oauth.py
```

### Option 3: Custom Configuration
```bash
python3 run_app.py --config config.yaml --app app.py --port 8501
```

### Option 4: Direct Streamlit
```bash
streamlit run app.py --server.port 8501
```

## Configuration

The application uses environment-specific configuration files:

- `deployment/dev-config.yaml` - Development environment
- `deployment/test-config.yaml` - Testing environment
- `deployment/prod-config.yaml` - Production environment

The `start.sh` script automatically copies the appropriate config to `config.yaml`.

## AWS Configuration (Optional)

For full functionality, configure AWS credentials:

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Accessing the Application

Once started, open your browser to:
```
http://localhost:8501
```

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
./start.sh dev app.py
python3 run_app.py --port 8502
```

### Import Errors
```bash
# Reinstall dependencies
pip3 install -r dev-requirements.txt
```

### Permission Denied
```bash
# Fix script permissions
chmod +x start.sh
chmod +x scripts/*.sh
```

### AWS Credentials Not Found
The application will start but with limited functionality. Configure AWS credentials for full features.

## Testing the Installation

Run the startup test to verify everything is working:

```bash
python3 windows-to-mac-migration/test_app_startup.py
```

Expected output:
```
✅ ALL TESTS PASSED
The application is ready to start on macOS.
```

## Common Commands

```bash
# Start development server
./start.sh dev app.py

# Stop the server
# Press Ctrl+C in the terminal

# View logs
# Logs appear in the terminal where you started the app

# Clean up
./scripts/cleanup.sh
```

## Next Steps

1. Upload instrument log files through the UI
2. Upload reference documentation (optional)
3. Run diagnosis analysis
4. Review results and recommendations

## Support

For issues specific to the Windows-to-Mac migration, see:
- `windows-to-mac-migration/README.md`
- `windows-to-mac-migration/TASK_10_VERIFICATION.md`
