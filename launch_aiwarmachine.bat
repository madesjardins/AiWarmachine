@echo off
set AIWARMACHINE_PYTHON_DIR=%~dp0python
set TITLES_DIRPATH=%~dp0titles
set PYTHONPATH=%PYTHONPATH%;%AIWARMACHINE_PYTHON_DIR%;%TITLES_DIRPATH%
set TEMP_DIRPATH=%~dp0temp
set PIPER_DIRPATH=%~dp0apps\piper
call python %AIWARMACHINE_PYTHON_DIR%\launch_aiwarmachine.py

timeout /t 10
