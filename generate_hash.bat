@echo off
setlocal
echo ===============================================
echo   Generating SHA256 Hash for MSI Installer
echo ===============================================

if not exist "dist" (
    echo [ERROR] 'dist' folder not found. Please build the MSI first.
    pause
    exit /b 1
)

:: Find the MSI file in dist
set "MSI_FILE="
for %%f in (dist\*.msi) do (
    set "MSI_FILE=%%f"
)

if "%MSI_FILE%"=="" (
    echo [ERROR] No MSI file found in 'dist' folder.
    pause
    exit /b 1
)

echo Found Installer: %MSI_FILE%
echo.

:: Run the python script
python installer\generate_hash.py "%MSI_FILE%"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to generate hash.
) else (
    echo.
    echo [SUCCESS] Hash file generated successfully!
    echo Upload the .sha256.txt file to your GitHub Release.
)

pause
