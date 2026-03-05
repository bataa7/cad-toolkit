@echo off
chcp 65001 >nul
echo ========================================
echo 启动 CADToolkit
echo ========================================
echo.
echo 正在启动安装版主程序...
echo.

set "APP_DIR=%~dp0"
start "" "%APP_DIR%CADToolkit.exe"

if errorlevel 1 (
    echo.
    echo ========================================
    echo 程序异常退出
    echo ========================================
    pause
)
