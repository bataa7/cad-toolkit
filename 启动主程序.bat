@echo off
chcp 65001 >nul
echo ========================================
echo 启动 CAD工具包
echo ========================================
echo.
echo 正在启动主程序...
echo.

python cad_toolkit_gui.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo 程序异常退出
    echo ========================================
    pause
)
