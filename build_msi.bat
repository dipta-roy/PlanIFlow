@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo   PlanIFlow - Build MSI Installer (cx_Freeze)
echo ===============================================

:: 1. Setup Environment
echo [STEP 1/3] Setting up environment...

:: Check if venv exists
if not exist "venv" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment scripts not found.
    pause
    exit /b 1
)

:: Install dependencies
echo [INFO] Installing/Updating dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 2. Build Core Executables
echo.
echo [STEP 2/3] Building Core Executables...
echo This will create the raw binaries in the 'build' folder.

:: Clean build directory if needed (optional)
if exist "build" (
    echo Cleaning previous build...
    rmdir /s /q "build"
)
if exist "dist" (
    echo Cleaning previous dist...
    rmdir /s /q "dist"
)

python installer\setup_msi.py build

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo   [PAUSE FOR SIGNING]
echo.
echo   The raw executables have been built in the 'build' directory.
echo   (Look for a folder like build\exe.win-amd64-3.x\)
echo.
echo   If you wish to digitally sign 'PlanIFlow.exe' (to avoid Unknown Publisher
echo   warnings), please do so NOW.
echo.
echo   When you are finished signing the files in the build folder,
echo   press any key to continue to packaging.
echo ===============================================================================
pause

:: 3. Package MSI
echo.
echo [STEP 3/3] Packaging MSI Installer...
echo Note: This step uses the binaries from the build folder.

python installer\setup_msi.py bdist_msi

if errorlevel 1 (
    echo [ERROR] MSI packaging failed.
    pause
    exit /b 1
)

:: Move the result to a clean dist folder if cx_Freeze put it in dist/
echo.
echo Checking for MSI in dist...
for %%f in (dist\*.msi) do (
    echo Found: %%f
    echo Installer built successfully!
)

echo.
echo ===============================================
echo   Installer Build Complete!
echo ===============================================
echo.
pause
