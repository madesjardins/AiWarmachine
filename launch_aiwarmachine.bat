@echo off
set AIWARMACHINE_PYTHON_DIR=%~dp0python
set PYTHONPATH=%PYTHONPATH%;%AIWARMACHINE_PYTHON_DIR%;
set TEMP_DIRPATH=%~dp0temp
set PIPER_DIRPATH=%~dp0apps\piper
call python %AIWARMACHINE_PYTHON_DIR%\launch_aiwarmachine.py

timeout /t 10
