#!/bin/bash
# Linux/macOS shell script to start Instrument Diagnosis Assistant
# Usage: ./start.sh [dev|test|prod] [app.py|app_oauth.py]

ENVIRONMENT=${1:-dev}
APP_FILE=${2:-app.py}

echo "Starting Instrument Diagnosis Assistant..."
echo "Environment: $ENVIRONMENT"
echo "App: $APP_FILE"
echo

# Copy appropriate config if config.yaml doesn't exist
if [ ! -f config.yaml ]; then
    echo "Copying $ENVIRONMENT configuration..."
    cp "deployment/${ENVIRONMENT}-config.yaml" config.yaml
fi

# Run the app
python3 run_app.py --config config.yaml --app "$APP_FILE"