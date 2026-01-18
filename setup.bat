@echo off
title WinVoice Setup
echo 🚀 Initializing Setup Environment...
echo ----------------------------------
echo Step 1: Installing UI Engine...

:: Install only the GUI library needed for the installer itself
pip install PySide6

:: Launch the Main Installer
echo.
echo ✅ UI Engine Ready. Launching Wizard...
python installer.py
pause