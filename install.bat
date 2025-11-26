@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   PlanIFlow - Project Planner v1.6 - One-Click Installer
echo ===============================================
echo.
echo This installer will set up PlanIFlow - Project Planner v1.6
echo.
echo This will:
echo   1. Check Python installation
echo   2. Create virtual environment
echo   3. Install all dependencies
echo   4. Run the application
echo.
set /p CONTINUE="Continue with installation? (Y/N): "
if /i not "!CONTINUE!"=="Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

echo.
echo ===============================================
echo   Starting installation...
echo ===============================================
echo.

REM Step 1: Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    
    REM Offer to open download page
    set /p OPEN_SITE="Open Python download page in browser? (Y/N): "
    if /i "!OPEN_SITE!"=="Y" (
        start https://www.python.org/downloads/
    )
    exit /b 1
)
python --version
echo [SUCCESS] Python found.
echo.

REM Step 2: Create virtual environment
echo [2/4] Creating virtual environment...
if exist "venv\" (
    echo [INFO] Removing existing virtual environment...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created.
echo.

REM Step 3: Activate and upgrade pip
echo [3/4] Activating environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo [SUCCESS] Environment activated.
echo.

REM Step 4: Install dependencies
echo [4/4] Installing dependencies...
echo [INFO] This may take 2-3 minutes depending on your internet speed...
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    echo.
    echo Troubleshooting:
    echo   1. Check your internet connection
    echo   2. Try running as Administrator
    echo   3. Temporarily disable antivirus
    echo.
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)
echo [SUCCESS] All dependencies installed.
echo.

REM List installed packages
echo [INFO] Installed packages:
echo.
pip list --format=columns | findstr /i "PyQt6 pandas matplotlib openpyxl"
echo.

call venv\Scripts\deactivate.bat

echo ===============================================
echo   Installation Complete!
echo ===============================================
echo.
echo Project Planner v1.6 is ready to use!
echo.
echo Quick Start Guide:
echo   - Run the app:        run.bat
echo   - Build executable:   build.bat
echo.
echo Documentation:
echo   - User guide:         README.md
echo   - Status legend:      Help menu in app
echo.

set /p RUN_NOW="Do you want to run Project Planner now? (Y/N): "
if /i "!RUN_NOW!"=="Y" (
    echo.
    echo [INFO] Launching Project Planner v1.6...
    echo.
    call run.bat
) else (
    echo.
    echo You can run it later using: run.bat
    echo.
)

pause