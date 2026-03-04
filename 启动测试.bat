@echo off
chcp 65001 >nul
echo ========================================
echo CAD工具包 - 消息推送和更新系统测试
echo ========================================
echo.

echo 正在检查依赖...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [错误] 未安装 Flask
    echo 正在安装依赖...
    pip install flask
    echo.
)

echo 正在启动测试服务器...
echo.
echo 提示：
echo   1. 服务器将在 http://localhost:5000 运行
echo   2. 在另一个终端运行 python integration_example.py 测试功能
echo   3. 按 Ctrl+C 停止服务器
echo.
echo ========================================
echo.

python test_server.py

pause
