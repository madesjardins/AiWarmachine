@echo off
set AIWARMACHINE_PYTHON_DIR=%~dp0..\python
set PYTHONPATH=%PYTHONPATH%;%AIWARMACHINE_PYTHON_DIR%

call python %AIWARMACHINE_PYTHON_DIR%\AiWarmachine\test\test_camera.py

timeout /t 3
