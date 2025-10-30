@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   PlanIFlow - Project Planner v1.0 - Build to EXE
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

REM Check if logo file exists
if not exist "images\logo.ico" (
    echo [WARNING] Logo file not found at images\logo.ico
    echo The executable will be built without an icon.
    echo.
    set ICON_OPTION=
) else (
    echo [INFO] Logo file found: images\logo.ico
    set ICON_OPTION=--icon=images\logo.ico
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
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

REM Check and install dependencies
echo [INFO] Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

if defined NEED_INSTALL (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Check if PyInstaller is installed
echo [INFO] Checking for PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
if exist "*.spec" del /q *.spec
echo.

REM Build the executable
echo ===============================================
echo   Building PlanIFlow - ProjectPlanner v1.0 with Icon
echo ===============================================
echo.

pyinstaller --onefile --windowed --name="PlanIFlow_ProjectPlanner_v1.0" ^
    %ICON_OPTION% ^
    --add-data="images;images" ^
    --add-data="data_manager.py;." ^
    --add-data="calendar_manager.py;." ^
    --add-data="gantt_chart.py;." ^
    --add-data="exporter.py;." ^
    --add-data="themes.py;." ^
    --add-data="ui_main.py;." ^
    --add-data="settings_manager.py;." ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.backends.backend_qtagg ^
    --hidden-import=matplotlib.patches ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=openpyxl.styles ^
    --collect-all PyQt6 ^
    --collect-all matplotlib ^
    --noconsole ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Build completed successfully!
echo ===============================================
echo.
echo [SUCCESS] Executable created: dist\PlanIFlow_ProjectPlanner_v1.0.exe
echo [INFO] Icon has been embedded in the executable
echo.

REM Display file info
for %%A in ("dist\ProjectPlanner_v2.1.exe") do (
    set size=%%~zA
    set /a sizeMB=!size! / 1048576
    echo [INFO] File size: !sizeMB! MB
)

echo.
set /p TEST_EXE="Do you want to test the executable now? (Y/N): "
if /i "!TEST_EXE!"=="Y" (
    echo.
    echo [INFO] Launching PlanIFlow_ProjectPlanner_v1.0.exe...
    start "" "dist\PlanIFlow_ProjectPlanner_v1.0.exe"
)

call venv\Scripts\deactivate.bat

echo.
echo ===============================================
echo   Build process complete!
echo ===============================================
pause