@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   PlanIFlow - Project Planner v1.3 - Quick Run
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher from https://www.python.org/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
    echo [INFO] This is a one-time setup, please wait...
    echo.
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
    echo.
) else (
    echo [INFO] Virtual environment found.
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo.

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import PyQt6; import pandas; import matplotlib; import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Dependencies not found or incomplete. Installing...
    echo.
    
    if not exist "requirements.txt" (
        echo [ERROR] requirements.txt not found!
        pause
        exit /b 1
    )
    
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Dependencies installed successfully.
    echo.
) else (
    echo [SUCCESS] All dependencies are installed.
    echo.
)

REM Run the application
echo ===============================================
echo   Launching PlanIFlow - Project Planner v1.3...
echo ===============================================

python main.py

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat

echo.
echo ===============================================
echo   Application closed.
echo ===============================================
pause