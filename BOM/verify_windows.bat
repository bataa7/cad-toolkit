@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo [1/4] Checking Python...
python --version || goto :fail

echo [2/4] Installing dependencies...
python -m pip install -r requirements.txt || goto :fail

echo [3/4] Running unit tests...
python -m unittest discover -s tests -v || goto :fail

echo [4/4] Running CLI smoke test...
if not exist "%~dp0artifacts" mkdir "%~dp0artifacts"
python bom_searcher.py --input "%~dp0测试.xlsx" --bom-folder "%~dp0" --output "%~dp0artifacts\verify_output.xlsx" || goto :fail

echo Verification succeeded.
exit /b 0

:fail
echo Verification failed.
exit /b 1
