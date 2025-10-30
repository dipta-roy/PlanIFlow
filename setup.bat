@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   Project Planner v2.0 - Environment Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
    echo.
) else (
    echo [INFO] Virtual environment already exists.
    set /p RECREATE="Do you want to recreate it? This will reinstall all packages. (Y/N): "
    if /i "!RECREATE!"=="Y" (
        echo [INFO] Removing old virtual environment...
        rmdir /s /q venv
        echo [INFO] Creating new virtual environment...
        python -m venv venv
        if errorlevel 1 (
            echo [ERROR] Failed to create virtual environment!
            pause
            exit /b 1
        )
        echo [SUCCESS] Virtual environment recreated successfully.
        echo.
    )
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

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo.

REM Install dependencies
echo [INFO] Installing Project Planner v2.0 dependencies...
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] All dependencies installed successfully.
echo.

REM Verify installation
echo [INFO] Verifying installation...
echo.

python -c "import PyQt6; print('[PASS] PyQt6')" || echo [FAIL] PyQt6
python -c "import pandas; print('[PASS] pandas')" || echo [FAIL] pandas
python -c "import matplotlib; print('[PASS] matplotlib')" || echo [FAIL] matplotlib
python -c "import openpyxl; print('[PASS] openpyxl')" || echo [FAIL] openpyxl

echo.

REM List installed packages
echo [INFO] Installed packages:
echo.
pip list --format=columns
echo.

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo ===============================================
echo   Setup completed successfully!
echo ===============================================
echo.
echo Environment is ready for Project Planner v2.0
echo.
echo Next steps:
echo   - Run application:    run.bat
echo   - Build executable:   build.bat
echo   - Development mode:   dev.bat
echo   - Run tests:          test.bat
echo.
pause