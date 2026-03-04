@echo off
chcp 65001 >nul
echo ========================================
echo    CAD工具包 - 本地网站服务器
echo ========================================
echo.
echo 正在启动本地服务器...
echo.
echo 服务器启动后，请在浏览器访问：
echo http://localhost:8000
echo.
echo 按 Ctrl+C 可以停止服务器
echo ========================================
echo.

cd /d "%~dp0"
python -m http.server 8000

pause
