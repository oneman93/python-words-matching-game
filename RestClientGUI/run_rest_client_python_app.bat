@echo off
REM Batch file to run the REST Client Python application
REM This file is called from DBConnectWPFApp's "run-python" button

cd /d "%~dp0"
python main.py

if errorlevel 1 (
    echo.
    echo Error: Failed to run Python application
    pause
)
