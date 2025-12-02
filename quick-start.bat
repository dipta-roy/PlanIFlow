@echo off
echo ===============================================
echo   PlanIFlow - Project Planner v1.6.1 - Quick Start
echo ===============================================
echo.
echo Choose an option:
echo.
echo   1. Run the application
echo   2. Build executable
echo   3. Install/Setup environment
echo   4. Clean project
echo   0. Exit
echo.
set /p OPTION="Enter choice (1-6): "

if "%OPTION%"=="1" call run.bat
if "%OPTION%"=="2" call build.bat
if "%OPTION%"=="3" call install.bat
if "%OPTION%"=="4" call clean.bat
if "%OPTION%"=="0" exit /b 0

pause