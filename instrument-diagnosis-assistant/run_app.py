#!/usr/bin/env python3
"""
Configurable Streamlit app launcher for Instrument Diagnosis Assistant
Reads port and host configuration from config.yaml
"""

import os
import sys
import yaml
import argparse
import subprocess
from pathlib import Path


def load_config(config_file: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"❌ Configuration file {config_file} not found.")
        print("Please copy one of the template configs from deployment/ directory:")
        print("  - deployment/dev-config.yaml (for development)")
        print("  - deployment/test-config.yaml (for testing)")
        print("  - deployment/prod-config.yaml (for production)")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)


def get_streamlit_config(config: dict) -> tuple:
    """Extract Streamlit configuration from config"""
    # Default values
    default_port = 8501
    default_host = "localhost"
    
    # Try to get from config
    deployment_config = config.get('deployment', {})
    streamlit_config = deployment_config.get('streamlit', {})
    
    port = streamlit_config.get('port', default_port)
    host = streamlit_config.get('host', default_host)
    
    return host, port


def main():
    parser = argparse.ArgumentParser(description="Run Instrument Diagnosis Assistant Streamlit App")
    parser.add_argument("--config", "-c", default="config.yaml", help="Configuration file path")
    parser.add_argument("--app", "-a", default="app.py", choices=["app.py", "app_oauth.py"], 
                       help="Which app to run (app.py for basic, app_oauth.py for OAuth)")
    parser.add_argument("--port", "-p", type=int, help="Override port from config")
    parser.add_argument("--host", type=str, help="Override host from config")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Load configuration
    print(f"📖 Loading configuration from {args.config}")
    config = load_config(args.config)
    
    # Get Streamlit configuration
    host, port = get_streamlit_config(config)
    
    # Override with command line arguments if provided
    if args.port:
        port = args.port
    if args.host:
        host = args.host
    
    # Determine app file
    app_file = args.app
    if not Path(app_file).exists():
        print(f"❌ App file {app_file} not found.")
        sys.exit(1)
    
    # Build Streamlit command
    cmd = [
        "streamlit", "run", app_file,
        "--server.port", str(port),
        "--server.address", host,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    if args.debug:
        cmd.extend(["--logger.level", "debug"])
    
    # Display startup information
    print(f"🚀 Starting Instrument Diagnosis Assistant")
    print(f"   App: {app_file}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   URL: http://{host}:{port}")
    print(f"   Environment: {config.get('deployment', {}).get('environment', 'unknown')}")
    print()
    
    # Check for port conflicts
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  Warning: Port {port} appears to be in use.")
            print(f"   You may need to choose a different port or stop the conflicting service.")
            print()
    except Exception:
        pass  # Ignore socket check errors
    
    # Run Streamlit
    try:
        print(f"🎯 Running command: {' '.join(cmd)}")
        print("=" * 60)
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Instrument Diagnosis Assistant")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it with: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()