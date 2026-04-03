@echo off
title Knowledge Archive
cd /d "%~dp0"
echo.
echo   Knowledge Archive
echo   =========================================
echo.

REM Try portable Python first
if exist "python_portable\python_windows\python\python.exe" (
    echo   Using portable Python...
    "python_portable\python_windows\python\python.exe" start_archive.py
    goto :end
)

REM Try system Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo   Using system Python...
    python start_archive.py
    goto :end
)

REM Try py launcher
where py >nul 2>nul
if %errorlevel% equ 0 (
    echo   Using py launcher...
    py start_archive.py
    goto :end
)

REM No Python found
echo.
echo   =============================================
echo   Python not found!
echo.
echo   Option 1: Run setup_portable_python.py first
echo             (requires Python on another machine)
echo.
echo   Option 2: Install Python from:
echo             https://www.python.org/downloads/
echo             Check "Add Python to PATH"
echo   =============================================
echo.
pause

:end
