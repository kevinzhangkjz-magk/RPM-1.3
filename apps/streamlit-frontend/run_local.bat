@echo off
REM Windows batch file to run the Streamlit application
REM Double-click this file on Windows to start the app

echo ========================================
echo RPM Streamlit Application Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Run the Python launcher script
python run_local.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    pause
)