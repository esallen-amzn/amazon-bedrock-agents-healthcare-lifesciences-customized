@echo off
REM Windows batch script to start Instrument Diagnosis Assistant
REM Usage: start.bat [dev|test|prod] [app.py|app_oauth.py]

set ENVIRONMENT=%1
set APP_FILE=%2

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
if "%APP_FILE%"=="" set APP_FILE=app.py

echo Starting Instrument Diagnosis Assistant...
echo Environment: %ENVIRONMENT%
echo App: %APP_FILE%
echo.

REM Copy appropriate config if config.yaml doesn't exist
if not exist config.yaml (
    echo Copying %ENVIRONMENT% configuration...
    copy deployment\%ENVIRONMENT%-config.yaml config.yaml
)

REM Run the app
python run_app.py --config config.yaml --app %APP_FILE%

pause