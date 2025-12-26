@echo off
SETLOCAL EnableDelayedExpansion

echo ===============================================
echo   PlanIFlow - Build Installer
echo ===============================================

:: 1. Build Core Application (Directory Mode)
echo [STEP 1/2] Building Core Application (Directory Mode)...
call build.bat --onedir --clean --no-pause
if errorlevel 1 (
    echo [ERROR] Failed to build core application.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo   [PAUSE FOR SIGNING]
echo.
echo   matrix Core application built at: dist\PlanIFlow_2.2.0.exe\
echo.
echo   If you wish to digitally sign the inner executables (e.g. PlanIFlow.exe),
echo   please do so NOW using your own certificate and tools.
echo.
echo   When you are finished signing, press any key to continue packaging.
echo ===============================================================================
pause

:: 2. Package Installer
echo.
echo [STEP 2/2] Packaging Installer...
:: Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python installer\package_installer.py
if errorlevel 1 (
    echo [ERROR] Failed to package installer.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Installer Build Complete!
echo ===============================================
echo.
echo  Output: dist\PlanIFlow_Setup_2.2.0.exe
echo.
echo  [FINAL ACTION]
echo  You may now digitally sign this final installer executable.
echo ===============================================
pause
