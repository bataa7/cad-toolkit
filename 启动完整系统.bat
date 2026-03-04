@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║          CAD工具包 - 完整更新系统启动器                    ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo.

:menu
echo ┌────────────────────────────────────────────────────────────┐
echo │  请选择操作：                                              │
echo ├────────────────────────────────────────────────────────────┤
echo │  1. 启动版本服务器（必须先启动）                          │
echo │  2. 运行更新系统演示                                       │
echo │  3. 运行主程序（集成更新功能）                            │
echo │  4. 清除测试设置                                           │
echo │  5. 生成安装程序配置                                       │
echo │  6. 一键集成更新系统                                       │
echo │  7. 查看文档                                               │
echo │  8. 退出                                                   │
echo └────────────────────────────────────────────────────────────┘
echo.

set /p choice="请输入选项 (1-8): "

if "%choice%"=="1" goto start_server
if "%choice%"=="2" goto run_demo
if "%choice%"=="3" goto run_main
if "%choice%"=="4" goto clear_settings
if "%choice%"=="5" goto generate_installer
if "%choice%"=="6" goto integrate
if "%choice%"=="7" goto show_docs
if "%choice%"=="8" goto exit

echo.
echo ✗ 无效选项，请重新选择
echo.
pause
cls
goto menu

:start_server
cls
echo ════════════════════════════════════════════════════════════
echo  启动版本服务器
echo ════════════════════════════════════════════════════════════
echo.
echo 正在启动服务器...
echo.
echo 服务器地址: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo ════════════════════════════════════════════════════════════
echo.
cd website
python -m http.server 8000
cd ..
pause
cls
goto menu

:run_demo
cls
echo ════════════════════════════════════════════════════════════
echo  运行更新系统演示
echo ════════════════════════════════════════════════════════════
echo.
echo 提示：请确保版本服务器已启动（选项1）
echo.
pause
python demo_update_system.py
pause
cls
goto menu

:run_main
cls
echo ════════════════════════════════════════════════════════════
echo  运行主程序
echo ════════════════════════════════════════════════════════════
echo.
echo 提示：请确保版本服务器已启动（选项1）
echo.
pause
python cad_toolkit_gui.py
pause
cls
goto menu

:clear_settings
cls
echo ════════════════════════════════════════════════════════════
echo  清除测试设置
echo ════════════════════════════════════════════════════════════
echo.
python clear_update_settings.py
pause
cls
goto menu

:generate_installer
cls
echo ════════════════════════════════════════════════════════════
echo  生成安装程序配置
echo ════════════════════════════════════════════════════════════
echo.
python installer_config.py
echo.
echo 下一步：
echo 1. 安装 Inno Setup: https://jrsoftware.org/isdl.php
echo 2. 打开 installer.iss 文件
echo 3. 点击 Build -^> Compile 生成安装程序
echo.
pause
cls
goto menu

:integrate
cls
echo ════════════════════════════════════════════════════════════
echo  一键集成更新系统
echo ════════════════════════════════════════════════════════════
echo.
python integrate_update.py
pause
cls
goto menu

:show_docs
cls
echo ════════════════════════════════════════════════════════════
echo  查看文档
echo ════════════════════════════════════════════════════════════
echo.
echo 可用文档：
echo.
echo 1. 集成更新系统指南.md
echo 2. 更新系统使用说明.md
echo 3. website/版本管理说明.md
echo.
set /p doc_choice="请选择要打开的文档 (1-3): "

if "%doc_choice%"=="1" start 集成更新系统指南.md
if "%doc_choice%"=="2" start 更新系统使用说明.md
if "%doc_choice%"=="3" start website/版本管理说明.md

pause
cls
goto menu

:exit
cls
echo.
echo 感谢使用 CAD工具包更新系统！
echo.
exit
